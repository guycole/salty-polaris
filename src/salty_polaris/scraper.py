"""Scraper for VesselFinder port pages.

Fetches vessels currently in port from
https://www.vesselfinder.com/ports/<port_code>
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

VESSELS_FINDER_BASE_URL = "https://www.vesselfinder.com"
PORTS_PATH = "/ports"
DEFAULT_PORT_CODE = "USBNC001"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

REQUEST_TIMEOUT = 30


@dataclass
class VesselRecord:
    """Represents a vessel currently in port."""

    name: str
    vessel_url: Optional[str] = None
    vessel_type: Optional[str] = None
    flag: Optional[str] = None
    length: Optional[str] = None
    arrival: Optional[str] = None
    departure: Optional[str] = None

    def __repr__(self) -> str:
        return (
            f"VesselRecord(name={self.name!r}, type={self.vessel_type!r}, "
            f"flag={self.flag!r}, arrived={self.arrival!r})"
        )


class VesselFinderScraper:
    """Scrapes ships in port from VesselFinder port pages.

    Example::

        scraper = VesselFinderScraper("USBNC001")
        vessels = scraper.scrape()
        for v in vessels:
            print(v.name, v.arrival)
    """

    def __init__(
        self,
        port_code: str = DEFAULT_PORT_CODE,
        headers: Optional[dict] = None,
        timeout: int = REQUEST_TIMEOUT,
    ) -> None:
        self.port_code = port_code
        self.url = f"{VESSELS_FINDER_BASE_URL}{PORTS_PATH}/{port_code}"
        self.headers = headers if headers is not None else DEFAULT_HEADERS
        self.timeout = timeout

    def fetch(self) -> str:
        """Fetch raw HTML for the port page.

        Returns:
            HTML content as a string.

        Raises:
            requests.HTTPError: If the server returns a non-2xx status.
            requests.Timeout: If the request times out.
        """
        logger.info("Fetching %s", self.url)
        response = requests.get(
            self.url,
            headers=self.headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.text

    def parse(self, html: str) -> List[VesselRecord]:
        """Parse vessel records from raw HTML.

        Args:
            html: Raw HTML string from the port page.

        Returns:
            List of :class:`VesselRecord` instances.
        """
        soup = BeautifulSoup(html, "lxml")
        return _parse_vessels(soup)

    def scrape(self) -> List[VesselRecord]:
        """Fetch and parse vessels in port.

        Returns:
            List of :class:`VesselRecord` instances.
        """
        html = self.fetch()
        vessels = self.parse(html)
        logger.info("Found %d vessel(s) in port %s", len(vessels), self.port_code)
        return vessels


def _parse_vessels(soup: BeautifulSoup) -> List[VesselRecord]:
    """Extract vessel records from a parsed port page.

    VesselFinder renders a ``<table>`` with one row per vessel.  The columns
    (in order) are typically:

    0. Vessel name / link
    1. Type
    2. Flag
    3. LOA (length overall in metres)
    4. Arrived (local timestamp)
    5. Expected departure (local timestamp)

    Args:
        soup: Parsed BeautifulSoup document.

    Returns:
        List of :class:`VesselRecord` instances.
    """
    vessels: List[VesselRecord] = []

    # VesselFinder uses a table; try known class names first, then fall back
    # to the first <table> on the page.
    table = (
        soup.find("table", class_="ships-list")
        or soup.find("table", class_="table")
        or soup.find("table")
    )

    if table is None:
        logger.warning("No vessel table found on the page")
        return vessels

    tbody = table.find("tbody")
    rows = tbody.find_all("tr") if tbody else table.find_all("tr")

    for row in rows:
        cells = row.find_all("td")
        if not cells:
            continue  # header row or empty row

        # --- column 0: vessel name -----------------------------------------------
        name_cell = cells[0]
        name_anchor = name_cell.find("a")
        name = (
            name_anchor.get_text(strip=True)
            if name_anchor
            else name_cell.get_text(strip=True)
        )
        if not name:
            continue

        vessel_url: Optional[str] = None
        if name_anchor and name_anchor.get("href"):
            vessel_url = urljoin(VESSELS_FINDER_BASE_URL, name_anchor["href"])

        # --- helper: safe cell text -----------------------------------------------
        def cell_text(index: int) -> Optional[str]:
            if index >= len(cells):
                return None
            text = cells[index].get_text(strip=True)
            return text if text else None

        vessels.append(
            VesselRecord(
                name=name,
                vessel_url=vessel_url,
                vessel_type=cell_text(1),
                flag=cell_text(2),
                length=cell_text(3),
                arrival=cell_text(4),
                departure=cell_text(5),
            )
        )

    return vessels
