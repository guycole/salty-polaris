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

import json
import os
import time

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

    def fetch_section_urls(self, html: str) -> dict:
        """Find URLs for #expected, #arrivals, #departures, #in-port sections on the port page."""
        soup = BeautifulSoup(html, "lxml")
        fragments = ["#expected", "#arrivals", "#departures", "#in-port"]
        section_urls = {}
        for frag in fragments:
            anchor = soup.find("a", href=lambda h: h and frag in h)
            if anchor and anchor["href"]:
                url = urljoin(self.url, anchor["href"])
                section_urls[frag] = url
        return section_urls

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


    for i, row in enumerate(rows):
        cells = row.find_all("td")
        if not cells:
            continue  # header row or empty row

        if i == 0:
            print("DEBUG: First row cell values:", [c.get_text(strip=True) for c in cells])

        # --- column 1: vessel name and type --------------------------------------

        name_cell = cells[1]
        name_anchor = name_cell.find("a", class_="named-item", href=True)
        if name_anchor:
            inner = name_anchor.find("div", class_="named-item-inner")
            if inner:
                div_title = inner.find("div", class_="named-title")
                div_subtitle = inner.find("div", class_="named-subtitle")
                name = div_title.get_text(strip=True) if div_title else None
                vessel_type = div_subtitle.get_text(strip=True).lower() if div_subtitle else None
            else:
                name = name_anchor.get_text(strip=True)
                vessel_type = None
            vessel_url = urljoin(VESSELS_FINDER_BASE_URL, name_anchor["href"])
        else:
            name = name_cell.get_text(strip=True)
            vessel_url = None
            vessel_type = None

        if not name:
            continue

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
                vessel_type=vessel_type,
                flag=cell_text(2),
                length=cell_text(7),
                arrival=cell_text(0),
                departure=cell_text(5),
            )
        )


    return vessels


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    port_code = DEFAULT_PORT_CODE
    print(f"Scraping vessels in port: {port_code}")
    scraper = VesselFinderScraper(port_code)
    html = scraper.fetch()
    vessels = scraper.parse(html)


    # Helper to convert VesselRecord to dict
    def vessel_to_dict(v):
        return {
            "name": v.name,
            "vessel_url": v.vessel_url,
            "vessel_type": v.vessel_type,
            "flag": v.flag,
            "length": v.length,
            "arrival": v.arrival,
            "departure": v.departure,
        }

    def make_json_preamble(port_code, url, vessels):
        return {
            "timestamp": int(time.time()),
            "port_code": port_code,
            "url": url,
            "vessels": [vessel_to_dict(v) for v in vessels],
        }

    timestamp = int(time.time())
    main_json_path = f"/tmp/{port_code}-main-{timestamp}.json"
    with open(main_json_path, "w") as f:
        json.dump(make_json_preamble(port_code, scraper.url, vessels), f, indent=2)
    print(f"Wrote main port vessels to {main_json_path}")

    # Find and visit each section URL
    section_urls = scraper.fetch_section_urls(html)
    for frag, url in section_urls.items():
        section_name = frag.lstrip('#').replace('-', '_')
        timestamp = int(time.time())
        json_path = f"/tmp/{port_code}-{section_name}-{timestamp}.json"
        print(f"Scraping section {frag} ({url}) ...")
        try:
            resp = requests.get(url, headers=scraper.headers, timeout=scraper.timeout)
            resp.raise_for_status()
            vessels = scraper.parse(resp.text)
            with open(json_path, "w") as f:
                json.dump(make_json_preamble(port_code, url, vessels), f, indent=2)
            print(f"Wrote {section_name} vessels to {json_path}")
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
