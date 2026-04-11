"""
port pages scraper, given a URL or a file,
extract port information (from HTML) and return a JSON summary
"""

import json
import logging
import os
import random
import requests
import socket
import sys
import time
import uuid

from utility import PolarisUtility

logger = logging.getLogger(__name__)

import yaml
from yaml.loader import SafeLoader

from bs4 import BeautifulSoup

from dataclasses import dataclass, field
from urllib.parse import urljoin


@dataclass
class VesselRecord:
    imo: str
    locode: str
    name: str
    port_url: str
    vessel_url: str
    vessel_type: str
    flag: str
    arrival: str
    departure: str
    built: str = "1900"
    size: str = "0"
    gross_ton: str = "0"
    in_port: bool = False

    def __repr__(self) -> str:
        return f"VesselRecord(name={self.name}, type={self.vessel_type}, flag={self.flag}, imo={self.imo}, gross_ton={self.gross_ton})"

    def to_dict(self) -> dict:
        return {
            "imoCode": self.imo,
            "loCode": self.locode,
            "name": self.name,
            "portUrl": self.port_url,
            "vesselUrl": self.vessel_url,
            "vesselType": self.vessel_type,
            "flag": self.flag,
            "size": 0 if len(self.size) < 2 else self.size,
            "grossTon": 0 if len(self.gross_ton) < 2 else int(self.gross_ton),
            "built": 1900 if len(self.built) < 2 else int(self.built),
            "arrivalDate": PolarisUtility.port_datetime(self.arrival).isoformat(),
            "departureDate": PolarisUtility.port_datetime(self.departure).isoformat(),
            "inPort": self.in_port,
        }


class PortParser:
    def __init__(self):
        self.base_url = "https://www.vesselfinder.com"

        def extract_flag(flag_div) -> str:
            if not flag_div:
                return ""
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
            return flag_div.text.strip() if flag_div.text.strip() else ""

        section_ids = {
            "arrivals": {"id": "arrivals", "date_field": "arrival"},
            "departures": {"id": "departures", "date_field": "departure"},
            "in-port": {"id": "inport", "date_field": None},
            "expected": {"id": "expected", "date_field": "arrival"},
        }

    def parse(self, html):
        # returns list of VesselRecord objects

        soup = BeautifulSoup(html, "lxml")

        # Extract canonical URL for the port
        canonical_link = soup.find("link", rel="canonical")
        port_url = (
            canonical_link["href"].strip()
            if canonical_link and canonical_link.has_attr("href")
            else ""
        )

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
            return flag_div.text.strip() if flag_div.text.strip() else ""

        def parse_table_section(section_key, date_field, in_port_flag):
            # Dynamically match the section title for any port
            section_patterns = {
                "arrivals": "Recent ship arrivals in ",
                "departures": "Recent ship departures from ",
                "expected": "Expected ships in ",
                "in-port": "Ships in port",
            }
            pattern = section_patterns[section_key]
            table = None
            for h2 in soup.find_all("h2", class_="tab-content-title"):
                h2_text = h2.text.strip()
                if (section_key == "in-port" and h2_text == pattern) or (
                    section_key != "in-port" and h2_text.startswith(pattern)
                ):
                    sib = h2
                    while sib is not None:
                        sib = sib.find_next_sibling()
                        if (
                            sib
                            and sib.name == "table"
                            and "ships-in-range" in sib.get("class", [])
                        ):
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
                    vessel_type = (
                        vessel_type_div.text.strip() if vessel_type_div else ""
                    )
                vessel_link = vessel_col.find("a", class_="named-item", href=True)
                vessel_url = (
                    urljoin(self.base_url, vessel_link["href"]) if vessel_link else ""
                )
                # Extract IMO from href, e.g. /vessels/details/9427964
                imo = ""
                if vessel_link and vessel_link.has_attr("href"):
                    import re

                    m = re.search(r"/vessels/details/(\d+)", vessel_link["href"])
                    if m:
                        imo = m.group(1)
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
                locode = port_url.split("/")[-1][:5] if port_url else ""
                record = VesselRecord(
                    imo=imo,
                    locode=locode,
                    name=name,
                    port_url=port_url,
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


class PortScraper:
    def __init__(self, fresh_dir: str, url: str):
        self.fresh_dir = fresh_dir
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

    def fetch(self, html_file_name: str, write_flag: bool) -> str:
        logger.info("fetching %s", self.url)

        # imitate human browsing behavior with random sleep before request
        time.sleep(random.uniform(5, 25))

        response = requests.get(self.url, headers=self.headers, timeout=self.timeout)
        response.raise_for_status()

        if write_flag:
            # Ensure the directory exists before writing
            os.makedirs(self.fresh_dir, exist_ok=True)
            with open(f"{self.fresh_dir}/{html_file_name}", "w", encoding="utf-8") as f:
                f.write(response.text)

        return response.text


class PortDriver:
    def __init__(self, fresh_dir: str):
        self.fresh_dir = fresh_dir

        base_file_name = str(uuid.uuid4())
        print("port base_file_name: ", base_file_name)
        self.html_file_name = f"{base_file_name}.html"
        self.json_file_name = f"{base_file_name}.json"

    def json_payload(
        self, arg: str, stunt: str, vessel_list: list[VesselRecord]
    ) -> dict[str, any]:
        payload = {
            "application": "polaris-ports-v1",
            "fileName": self.json_file_name,
            "hostName": socket.gethostname(),
            "loCode": arg.split("/")[-1][:5] if stunt == "net" else "XXXXX",
            "schemaVersion": 1,
            "timeStampEpoch": int(time.time()),
            "url": arg if stunt == "net" else "file://" + arg,
            "vessels": [],
        }

        for vessel in vessel_list:
            vessel_dict = vessel.to_dict()
            payload["vessels"].append(vessel_dict)

        return payload

    def json_writer(self, payload: dict[str, any]) -> None:
        try:
            with open(f"{self.fresh_dir}/{self.json_file_name}", "w") as out_file:
                json.dump(payload, out_file, indent=4)
        except Exception as error:
            print(error)

    def html_reader(self, file_name: str) -> str:
        try:
            with open(file_name, "r", encoding="utf-8") as in_file:
                return in_file.read()
        except Exception as error:
            print(error)
            return ""

    def execute(self, stunt: str, arg: str) -> dict[str, any]:
        parser = PortParser()
        port_dict = {}

        if stunt == "file":
            # file reads raw html from file system, does not write html/json
            print(f"file stunt: {arg}")
            raw_html = self.html_reader(arg)
            vessel_list = parser.parse(raw_html)
            port_dict = self.json_payload(arg, stunt, vessel_list)
        elif stunt == "net":
            # net reads raw html from network, and writes html/json
            # print(f"net stunt: {arg}")
            scraper = PortScraper(self.fresh_dir, arg)
            raw_html = scraper.fetch(self.html_file_name, True)
            vessel_list = parser.parse(raw_html)
            port_dict = self.json_payload(arg, stunt, vessel_list)
            self.json_writer(port_dict)
        elif stunt == "test":
            print(f"test stunt: {arg}")
            raw_html = self.html_reader(arg)
            vessel_list = parser.parse(raw_html)
            #            for vessel in vessel_list:
            #                print(vessel.to_dict())
            #            print(f"total vessels parsed: {len(vessel_list)}")
            port_dict = self.json_payload(arg, stunt, vessel_list)
            print(port_dict)
        else:
            print("unknown stunt")

        # print(f"parse results: {len(port_dict['vessels'])} vessels found")
        return port_dict


#
# ports development
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
            driver = PortDriver(configuration["freshDir"])
            # USRCH
            #            driver.execute("test", "../../sample/fe87d094-490a-4dd6-b881-5e70a97dc488.html")
            driver.execute("net", "https://www.vesselfinder.com/ports/USBNC001")
        except yaml.YAMLError as error:
            print(error)

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
