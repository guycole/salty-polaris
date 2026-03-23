"""
scraper for port pages.
"""

import json
import logging
import os
import requests
import sys
import time
import uuid

logger = logging.getLogger(__name__)

import yaml
from yaml.loader import SafeLoader

from bs4 import BeautifulSoup

from dataclasses import dataclass, field
from urllib.parse import urljoin

@dataclass
class VesselRecord:
    name: str
    vessel_url: str
    vessel_type: str 
    flag: str 
    arrival: str
    departure: str
    built: str = "0"
    size: str = "0" 
    gross_ton: str = "0"
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

    def __init__(self, fresh_dir: str, html_file_name: str, url: str) -> None:
        self.base_url = "https://www.vesselfinder.com"
        self.fresh_dir = fresh_dir
        self.html_file_name = html_file_name
        self.port = url.split("/")[-1]
        self.url = url

        self.headers = {
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

        def extract_flag(flag_div) -> str:
            if not flag_div:
                return ""
            if flag_div.has_attr("title"):
                return flag_div["title"].strip()
            flag_title_tag = flag_div.find(lambda tag: tag.has_attr("title"))
            if flag_title_tag and flag_title_tag.get("title") and flag_title_tag["title"].strip():
                return flag_title_tag["title"].strip()
            for descendant in flag_div.descendants:
                if hasattr(descendant, "attrs") and descendant.attrs.get("title") and descendant.attrs["title"].strip():
                    return descendant.attrs["title"].strip()
            return flag_div.text.strip() if flag_div.text.strip() else ""

        section_ids = {
            "arrivals": {"id": "arrivals", "date_field": "arrival"},
            "departures": {"id": "departures", "date_field": "departure"},
            "in-port": {"id": "inport", "date_field": None},
            "expected": {"id": "expected", "date_field": "arrival"},
        }

    def parse(self, html):
        soup = BeautifulSoup(html, "lxml")

        section_ids = {
            "arrivals": {"id": "arrivals", "date_field": "arrival"},
            "departures": {"id": "departures", "date_field": "departure"},
            "in-port": {"id": "inport", "date_field": None},
            "expected": {"id": "expected", "date_field": "arrival"},
        }

        def get_text_or_empty(td):
            return td.text.strip() if td and td.text else ""

        def extract_flag(flag_div):
            if not flag_div:
                return ""
            if flag_div.has_attr("title"):
                return flag_div["title"].strip()
            flag_title_tag = flag_div.find(lambda tag: tag.has_attr("title"))
            if flag_title_tag and flag_title_tag.get("title") and flag_title_tag["title"].strip():
                return flag_title_tag["title"].strip()
            for descendant in flag_div.descendants:
                if hasattr(descendant, "attrs") and descendant.attrs.get("title") and descendant.attrs["title"].strip():
                    return descendant.attrs["title"].strip()
            return flag_div.text.strip() if flag_div.text.strip() else ""

        def parse_table_section(section_key, date_field, in_port_flag):
            # Find the correct table by matching the heading text before the table
            section_titles = {
                "arrivals": "Recent ship arrivals in Selby",
                "departures": "Recent ship departures from Selby",
                "expected": "Expected ships in Selby",
                "in-port": "Ships in port",
            }
            expected_title = section_titles[section_key]
            table = None
            for h2 in soup.find_all("h2", class_="tab-content-title"):
                if h2.text.strip() == expected_title:
                    # The next table after this heading is the one we want
                    sib = h2
                    while sib is not None:
                        sib = sib.find_next_sibling()
                        if sib and sib.name == "table" and "ships-in-range" in sib.get("class", []):
                            table = sib
                            break
                    if table:
                        break
            if not table:
                return []
            records = []
            rows = table.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                if not cols or len(cols) < 2:
                    continue
                date_val = cols[0].text.strip() if date_field else ""
                vessel_col = cols[1]
                name = ""
                vessel_type = ""
                named_inner = vessel_col.find("div", class_="named-item-inner")
                if named_inner:
                    name_div = named_inner.find("div", class_="named-title")
                    vessel_type_div = named_inner.find("div", class_="named-subtitle")
                    name = name_div.text.strip() if name_div else ""
                    vessel_type = vessel_type_div.text.strip() if vessel_type_div else ""
                vessel_link = vessel_col.find("a", class_="named-item", href=True)
                vessel_url = urljoin(self.base_url, vessel_link["href"]) if vessel_link else ""
                flag_div = vessel_col.find("div", class_="m-flag-small")
                flag = extract_flag(flag_div) or ""
                built = ""
                gt = ""
                size = ""
                if len(cols) > 4:
                    built = ""
                    gt = ""
                    size = ""
                    for td in cols:
                        td_classes = td.get("class", [])
                        if any("col-y" in c for c in td_classes):
                            built = td.text.strip() if td.text.strip() != "-" else ""
                        if any("col-gt" in c for c in td_classes):
                            gt = td.text.strip() if td.text.strip() != "-" else ""
                        if any("col-sizes" in c for c in td_classes):
                            size = td.text.strip() if td.text.strip() != "-" else ""
                arrival_val = date_val if date_field == "arrival" else ""
                departure_val = date_val if date_field == "departure" else ""
                record = VesselRecord(
                    name=name,
                    vessel_url=vessel_url,
                    vessel_type=vessel_type,
                    flag=flag,
                    size=size,
                    gross_ton=gt,
                    built=built,
                    arrival=arrival_val,
                    departure=departure_val,
                    in_port=in_port_flag,
                )
                records.append(record)
            return records

        all_vessels = []
        all_vessels.extend(parse_table_section("arrivals", "arrival", False))
        all_vessels.extend(parse_table_section("departures", "departure", False))
        all_vessels.extend(parse_table_section("expected", "arrival", False))
        all_vessels.extend(parse_table_section("in-port", None, True))
        return all_vessels

    def fetch(self, write_flag: bool) -> str:
        logger.info("fetching %s", self.url)

        response = requests.get(self.url, headers=self.headers, timeout=self.timeout)
        response.raise_for_status()

        if write_flag:           
            with open(f"{self.fresh_dir}/{self.html_file_name}", "w", encoding="utf-8") as f:
                f.write(response.text)

        return response.text

    def collection(self, raw_html: str) -> list[VesselRecord]:
        if raw_html is None:
            print("fetching fresh html for collection")
            raw_html = self.fetch(True)
        else:
            print("Using saved HTML for collection")

        results = self.parse(raw_html)
        print(f"{self.port} collection results: {len(results)} vessels found")
        return results

    def json_preamble(self, json_file_name: str) -> dict[str, any]:
        return {
            "application": "polaris-ports-v1",
            "fileName": json_file_name,
            "portCode": self.port,
            "schemaVersion": 1,
            "timeStampEpoch": int(time.time()),
            "url": self.url,
            "vessels": [],
        }

class PortDriver:
    def __init__(self, configuration: dict[str, any]) -> None:
        self.fresh_dir = configuration["freshDir"]

    def json_writer(self, payload: dict[str, any], vessel_list: list[VesselRecord]) -> None:
        for vessel in vessel_list:
            vessel_dict = vessel.to_dict()
            payload["vessels"].append(vessel_dict)

        try:
            with open(f"{self.fresh_dir}/{payload['fileName']}", "w") as out_file:
                json.dump(payload, out_file, indent=4)
        except Exception as error:
            print(error)

    def execute(self, port_url: str, test_flag: bool) -> list[VesselRecord]:
        raw_html = None

        if test_flag:
            # read existing html file for testing
            raw_port_url = "https://www.vesselfinder.com/ports/USSEL001"
            raw_html_file = "/var/polaris/fresh/f985eb7d-3788-4277-bbbc-8f101288f592.html"

            raw_port_url = "https://www.vesselfinder.com/ports/USVLO001"
            raw_html_file = "/var/polaris/fresh/6c9f657d-a19f-449a-9af7-8b4be5682245.html"

            raw_port_url = "https://www.vesselfinder.com/ports/USPZH001"
            raw_html_file = "/var/polaris/fresh/1231c64a-2904-4eed-b749-41a4fcd38030.html"

            with open(raw_html_file, "r", encoding="utf-8") as f:
                raw_html = f.read()
                scraper = PortScraper(self.fresh_dir, None, raw_port_url)
                vessel_list = scraper.collection(raw_html)
                print(vessel_list)
                return vessel_list

        base_file_name = str(uuid.uuid4())
        html_file_name = f"{base_file_name}.html"
        json_file_name = f"{base_file_name}.json"
        print("base_file_name: ", base_file_name)

        scraper = PortScraper(self.fresh_dir, html_file_name, port_url)
        vessel_list = scraper.collection(raw_html)

        json_preamble = scraper.json_preamble(json_file_name)
        self.json_writer(json_preamble, vessel_list)
        return vessel_list

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
            driver = PortDriver(configuration)
            driver.execute(None, True)
        except yaml.YAMLError as error:
            print(error)

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
