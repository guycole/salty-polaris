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
import sys
import time

logger = logging.getLogger(__name__)

import yaml
from yaml.loader import SafeLoader


@dataclass
class VesselRecord:
    name: str 
    vessel_url: str
    vessel_type: str 
    flag: str
    arrival: str
    departure: str
    size: str
    built: str 
    gross_ton: str
    in_port: bool = False

    def __repr__(self) -> str:
        return f"VesselRecord(name={self.name!r}, type={self.vessel_type!r}, flag={self.flag!r}, size={self.size!r}, gross_ton={self.gross_ton!r}, built={self.built!r})"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "vesselUrl": self.vessel_url,
            "vesselType": self.vessel_type,
            "flag": self.flag,
            "size": 0 if len(self.size) < 2 else self.size,
            "grossTon": 0 if len(self.gross_ton) < 2 else int(self.gross_ton),
            "built": 0 if len(self.built) < 2 else int(self.built),
            "arrival": self.arrival,
            "departure": self.departure,
        } 

class PortScraper:

    def __init__(
        self, base_url: str, fresh_dir: str, path: str, port: str, time_stamp: int
    ) -> None:
        self.base_url = base_url
        self.fresh_dir = fresh_dir
        self.path = path
        self.port = port
        self.time_stamp = time_stamp
        self.url = f"{self.base_url}{self.path}/{self.port}"

        self.headers: Optional[dict] = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.vesselfinder.com/",
            "Connection": "keep-alive",
        }
        self.timeout: int = 30

    def fetch(self, write_flag: bool) -> str:
        logger.info("fetching %s", self.url)

        response = requests.get(self.url, headers=self.headers, timeout=self.timeout)
        response.raise_for_status()

        if write_flag:
            base_file_name = self.get_base_file_name()
            html_path = f"{base_file_name}.html"

            with open(html_path, "w", encoding="utf-8") as f:
                f.write(response.text)

        return response.text

    def get_base_file_name(self) -> str:
        return f"{self.fresh_dir}/{self.port}-{self.time_stamp}"

    def parse(self, html: str) -> List[VesselRecord]:
        soup = BeautifulSoup(html, "lxml")

        section_ids = {
            "arrivals": {"id": "arrivals", "date_field": "arrival"},
            "departures": {"id": "departures", "date_field": "departure"},
            "in-port": {"id": "inport", "date_field": None},
            "expected": {"id": "expected", "date_field": "arrival"},
        }

        def extract_flag(flag_div):
            if flag_div:
                if flag_div.has_attr("title"):
                    return flag_div["title"].strip()
                flag_title_tag = flag_div.find(lambda tag: tag.has_attr("title"))
                if (
                    flag_title_tag
                    and flag_title_tag.get("title")
                    and flag_title_tag["title"].strip()
                ):
                    return flag_title_tag["title"].strip()
                for descendant in flag_div.descendants:
                    if (
                        hasattr(descendant, "attrs")
                        and descendant.attrs.get("title")
                        and descendant.attrs["title"].strip()
                    ):
                        return descendant.attrs["title"].strip()
                if flag_div.text.strip():
                    return flag_div.text.strip()
            return None

        def parse_table_section(section_id, date_field, in_port_flag):
            section = soup.find("section", id=section_id)
            if not section:
                return []
            table = section.find("table")
            if not table:
                return []
            records = []
            for row in table.find_all("tr")[1:]:  # skip header row
                cols = row.find_all("td")
                if not cols or len(cols) < 2:
                    continue
                # For arrivals/departures/expected, first col is date, second is vessel
                date_val = cols[0].text.strip() if date_field else None
                vessel_col = cols[1]
                named_inner = vessel_col.find("div", class_="named-item-inner")
                name = None
                vessel_type = None
                if named_inner:
                    name_div = named_inner.find("div", class_="named-title")
                    vessel_type_div = named_inner.find("div", class_="named-subtitle")
                    name = name_div.text.strip() if name_div else None
                    vessel_type = (
                        vessel_type_div.text.strip() if vessel_type_div else None
                    )
                vessel_link = vessel_col.find("a", class_="named-item")
                vessel_url = (
                    urljoin(self.base_url, vessel_link["href"])
                    if vessel_link and vessel_link.has_attr("href")
                    else None
                )
                flag_div = vessel_col.find("div", class_="m-flag-small")
                flag = extract_flag(flag_div)
                # Parse built, gt, and size columns if present
                built = cols[4].text.strip() if len(cols) > 4 else None
                gt = cols[5].text.strip() if len(cols) > 5 else None
                size = None
                for td in cols:
                    td_classes = td.get("class", [])
                    if any("col-sizes" in c for c in td_classes):
                        size = td.text.strip()
                        break
                record = VesselRecord(
                    name=name,
                    vessel_url=vessel_url,
                    vessel_type=vessel_type,
                    flag=flag,
                    size=size,
                    gross_ton=gt,
                    built=built,
                    arrival=date_val if date_field == "arrival" else None,
                    departure=date_val if date_field == "departure" else None,
                    in_port=in_port_flag,
                )
                records.append(record)
            return records

        all_vessels = []
        all_vessels.extend(parse_table_section("arrivals", "arrival", False))
        all_vessels.extend(parse_table_section("departures", "departure", False))
        all_vessels.extend(parse_table_section("expected", "arrival", False))
        all_vessels.extend(parse_table_section("inport", None, True))
        return all_vessels

    def collection(self, raw_html: str) -> List[VesselRecord]:
        if raw_html is None:
            raw_html = self.fetch(True)
        else:
            print("Using provided raw HTML for collection")

        results = self.parse(raw_html)
        print(len(results), "vessels found for port", self.port)

        return results

    def json_preamble(self) -> dict:
        return {
            "application": "polaris-ports-v1",
            "portCode": self.port,
            "schemaVersion": 1,
            "timeStampEpoch": self.time_stamp,
            "url": self.url,
            "vessels": [],
        }


class Driver:
    def __init__(self, configuration: dict[str, any]) -> None:
        self.fresh_dir = configuration["freshDir"]
        self.port_targets = configuration["portTargets"]

        self.base_url = configuration["vesselFinderUrl"]
        self.ports_path = configuration["portsPath"]

    def vessel_to_dict(self, vessel: VesselRecord) -> dict:
        return {
            "name": vessel.name,
            "vesselUrl": vessel.vessel_url,
            "vesselType": vessel.vessel_type,
            "flag": vessel.flag,
            "size": 0 if len(vessel.size) < 2 else vessel.size,
            "grossTon": 0 if len(vessel.gross_ton) < 2 else int(vessel.gross_ton),
            "built": 0 if len(vessel.built) < 2 else int(vessel.built),
            "arrival": vessel.arrival,
            "departure": vessel.departure,
            "inPort": vessel.in_port,
        }

    def json_writer(
        self, file_name: str, payload: dict, vessel_list: List[VesselRecord]
    ) -> None:
        for vessel in vessel_list:
            vessel_dict = self.vessel_to_dict(vessel)
            payload["vessels"].append(vessel_dict)

        try:
            with open(f"{file_name}.json", "w") as out_file:
                json.dump(payload, out_file, indent=4)
        except Exception as error:
            print(error)

    def execute(self) -> None:
        print(f"collection for {len(self.port_targets)} ports")

        time_stamp = int(time.time())

        raw_html_file = "/var/polaris/fresh/USBNC001-1773890936.html"

        raw_html = None
        #        with open(raw_html_file, "r", encoding="utf-8") as f:
        #            raw_html = f.read()

        for port in self.port_targets:
            scraper = PortScraper(
                self.base_url, self.fresh_dir, self.ports_path, port, time_stamp
            )
            base_file_name = scraper.get_base_file_name()
            vessel_list = scraper.collection(raw_html)
            payload = scraper.json_preamble()
            self.json_writer(base_file_name, payload, vessel_list)


#
# argv[1] = configuration filename
#
if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_name = sys.argv[1]
    else:
        file_name = "config.yaml"

    with open(file_name, "r") as in_file:
        try:
            configuration = yaml.load(in_file, Loader=SafeLoader)
            driver = Driver(configuration)
            driver.execute()
        except yaml.YAMLError as error:
            print(error)

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
