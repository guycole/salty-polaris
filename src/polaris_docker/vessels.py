from ast import arg
from dataclasses import dataclass
from html import parser
import random
import sys
import json
from typing import Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import socket
import time
import uuid
import logging

from utility import PolarisUtility

logger = logging.getLogger(__name__)

import yaml
from yaml.loader import SafeLoader


@dataclass
class VesselObservation:
    name: str
    ais_type: str
    beam: str
    built: str
    callsign: str
    flag: str
    gross_ton: str
    imo: str
    length: str
    mmsi: str
    vessel_url: str

    course: str
    speed: str
    navigation_status: str

    destination: str
    destination_locode: str
    arrival_date: str

    last_port: str
    last_locode: str
    departure_date: str

    def __repr__(self) -> str:
        return f"VesselObservation(name={self.name!r}, type={self.ais_type!r}, flag={self.flag!r}, callsign={self.callsign!r})"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "aisType": self.ais_type,
            "beam": self.beam,
            "built": self.built,
            "callsign": self.callsign,
            "flag": self.flag,
            "grossTon": self.gross_ton,
            "imoCode": self.imo,
            "length": self.length,
            "mmsi": self.mmsi,
            "vesselUrl": self.vessel_url,
            "course": self.course,
            "speed": self.speed,
            "navigationStatus": self.navigation_status,
            "destination": self.destination,
            "destinationLoCode": self.destination_locode,
            "arrivalDate": self.arrival_date,
            "lastPort": self.last_port,
            "lastLoCode": self.last_locode,
            "departureDate": self.departure_date,
        }


class VesselParser:

    def __init__(self):
        self.base_url = "https://www.vesselfinder.com"

    def parse(self, raw_html: str) -> VesselObservation:
        soup = BeautifulSoup(raw_html, "html.parser")

        # Extract canonical URL for the vessel
        canonical_link = soup.find("link", rel="canonical")
        vessel_url = (
            canonical_link["href"].strip()
            if canonical_link and canonical_link.has_attr("href")
            else ""
        )

        # Helper to get text from a table row by label
        def get_table_value(label: str) -> str:
            for td in soup.find_all("td"):
                if td.get_text(strip=True) == label:
                    next_td = td.find_next_sibling("td")
                    if next_td:
                        return next_td.get_text(strip=True)
            return None

        # Helper to get value from a/v3 table (Voyage Data)
        def get_aparams_value(label: str) -> str:
            for tr in soup.select("table.aparams tr"):
                tds = tr.find_all("td")
                if len(tds) == 2 and tds[0].get_text(strip=True) == label:
                    return tds[1].get_text(strip=True)
            return None

        # Vessel name (from h1.title)
        name = None
        h1 = soup.find("h1", class_="title")
        if h1:
            name = h1.get_text(strip=True)

        # AIS type (from "AIS Type" in Voyage Data)
        ais_type = get_aparams_value("AIS Type")

        # Flag (from "AIS Flag" in Voyage Data or Vessel Particulars)
        flag = get_aparams_value("AIS Flag")
        if not flag:
            arrival_port_code: Optional[str] = None

        # Built (from "Year of Build" in Vessel Particulars)
        built = get_table_value("Year of Build")

        # Gross tonnage (from "Gross Tonnage" in Vessel Particulars)
        gross_ton = get_table_value("Gross Tonnage")

        # IMO and MMSI (from "IMO / MMSI" in Voyage Data)
        imo, mmsi = None, None
        imo_mmsi = get_aparams_value("IMO / MMSI")
        if imo_mmsi and "/" in imo_mmsi:
            parts = [p.strip() for p in imo_mmsi.split("/")]
            if len(parts) == 2:
                imo, mmsi = parts
        else:
            imo = get_table_value("IMO number")

        # Callsign (from "Callsign" in Voyage Data)
        callsign = get_aparams_value("Callsign")

        # Length and Beam (from "Length / Beam" in Voyage Data or Vessel Particulars)
        length, beam = None, None
        len_beam = get_aparams_value("Length / Beam")
        if len_beam and "/" in len_beam:
            parts = [p.strip().replace(" m", "") for p in len_beam.split("/")]
            if len(parts) == 2:
                length, beam = parts
        else:
            length = get_table_value("Length Overall (m)")
            beam = get_table_value("Beam (m)")

        # Course and Speed (prefer djson data-json, fallback to table)
        course, speed = None, None
        djson_span = soup.find("div", id="djson")
        if djson_span and djson_span.has_attr("data-json"):
            import json as _json

            try:
                djson = _json.loads(djson_span["data-json"])
                course = (
                    str(djson.get("ship_cog"))
                    if djson.get("ship_cog") is not None
                    else None
                )
                speed = (
                    str(djson.get("ship_sog"))
                    if djson.get("ship_sog") is not None
                    else None
                )
            except Exception:
                pass
        if not course or not speed:
            course_speed = get_aparams_value("Course / Speed")
            if course_speed and "/" in course_speed:
                parts = [p.strip() for p in course_speed.split("/")]
                if len(parts) == 2:
                    course, speed = parts

        # Navigation Status (from "Navigation Status" in Voyage Data)
        navigation_status = get_aparams_value("Navigation Status")

        # Destination (from "Destination" in Voyage Data)
        destination = None
        destination_locode = None
        arrival_date = None

        def extract_labeled_date(text: str, label: str) -> str:
            if not text or label not in text:
                return None
            tail = text.split(label, 1)[1].strip()
            # Trim relative-time suffixes and timezone token if present.
            tail = tail.split("(", 1)[0].strip()
            if tail.endswith(" UTC"):
                tail = tail[:-4].strip()
            return tail

        dest_div = soup.find("div", class_="vilabel", string="Destination")
        if dest_div:
            # The destination is in the next <a> tag (port link)
            dest_a = dest_div.find_next("a")
            if dest_a:
                destination = dest_a.get_text(strip=True)
                href = dest_a.get("href", "")
                # Extract locode from /ports/LOCODE
                if href.startswith("/ports/"):
                    destination_locode = href.split("/ports/")[-1]
            # Arrival date is in the next _value span with class _mcol12ext and contains 'ETA:'
            value_div = dest_div.find_next("div", class_="_value")
            if value_div:
                value_text = value_div.get_text(" ", strip=True)
                arrival_date = extract_labeled_date(value_text, "ETA:")

        if not destination_locode:
            destination_locode = "PAXXX001"

        # Arrival date (from "ATA" in Voyage Data) -- only overwrite if not set from ETA
        if arrival_date is None:
            # Try ATA from the last-port value block first.
            if last_port_div := soup.find("div", class_="vilabel", string="Last Port"):
                atd_div = last_port_div.find_next("div", class_="_value")
                if atd_div:
                    arrival_date = extract_labeled_date(
                        atd_div.get_text(" ", strip=True), "ATA:"
                    )
            if arrival_date is None:
                ata_span = soup.find("span", class_="_mcol12")
                if ata_span:
                    arrival_date = extract_labeled_date(
                        ata_span.get_text(" ", strip=True), "ATA:"
                    )

        # Last port and last port code (from "Last Port" in Voyage Data)
        last_port, last_locode = None, None
        last_port_div = soup.find("div", class_="vilabel", string="Last Port")
        if last_port_div:
            last_port_a = last_port_div.find_next("a")
            if last_port_a and last_port_a.get("href", "").startswith("/ports/"):
                last_port = last_port_a.get_text(strip=True)
                last_locode = last_port_a["href"].split("/ports/")[-1]
            else:
                # No port link present — name is in the _3-Yih div, locode is unknown
                name_div = last_port_div.find_next("div", class_="_3-Yih")
                if name_div:
                    last_port = name_div.get_text(strip=True)
                last_locode = "PAXXX001"

        # Departure date (from "Last Port" and "ATA"/"ATD" in Voyage Data)
        departure_date = None
        last_port_div = soup.find("div", class_="vilabel", string="Last Port")
        if last_port_div:
            atd_div = last_port_div.find_next("div", class_="_value")
            if atd_div:
                text = atd_div.get_text(" ", strip=True)
                # Prefer ATD, fallback to ATA if present
                departure_date = extract_labeled_date(text, "ATD:")
                if departure_date is None:
                    # Sometimes only ATA is present, use that as fallback
                    departure_date = extract_labeled_date(text, "ATA:")

        # vessel_url is now set from canonical link above

        return VesselObservation(
            name=name,
            ais_type=ais_type,
            beam=beam,
            built=built,
            callsign=callsign,
            flag=flag,
            gross_ton=gross_ton,
            imo=imo,
            length=length,
            mmsi=mmsi,
            vessel_url=vessel_url,
            arrival_date=arrival_date,
            destination_locode=destination_locode,
            departure_date=departure_date,
            course=course,
            speed=speed,
            navigation_status=navigation_status,
            destination=destination,
            last_port=last_port,
            last_locode=last_locode,
        )


class VesselScraper:
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
        # imitate human browsing behavior with random sleep before request
        duration = random.uniform(5, 25)
        logger.info(f"sleeping for {duration:.2f} seconds before fetching {self.url}")
        time.sleep(duration)

        attempts = 0
        for attempts in range(3):
            try:
                response = requests.get(
                    self.url, headers=self.headers, timeout=self.timeout
                )
                response.raise_for_status()
                break  # success, exit the retry loop
            except requests.RequestException as error:
                logger.error(
                    f"attempt {attempts + 1} error fetching {self.url}: {error}"
                )

                if attempts < 2:
                    backoff = 2 ** attempts
                    logger.info(f"retrying in {backoff} seconds...")
                    time.sleep(backoff)
                else:
                    logger.error(f"failed to fetch {self.url} after 3 attempts")
                    return ""
 
        if write_flag:
            with open(f"{self.fresh_dir}/{html_file_name}", "w", encoding="utf-8") as f:
                f.write(response.text)

        return response.text


class VesselDriver:
    def __init__(self, fresh_dir: str):
        self.fresh_dir = fresh_dir

        base_file_name = str(uuid.uuid4())
        print("vessel base_file_name: ", base_file_name)

        self.html_file_name = f"{base_file_name}.html"
        self.json_file_name = f"{base_file_name}.json"

    def html_reader(self, file_name: str) -> str:
        try:
            with open(file_name, "r", encoding="utf-8") as in_file:
                return in_file.read()
        except Exception as error:
            print(error)
            return ""

    def json_preamble(self, obs: VesselObservation) -> dict[str, any]:
        if obs.imo is None or obs.imo == "":
            imo_code = obs.vessel_url.split("/")[-1]
            obs.imo = imo_code
        else:
            imo_code = obs.imo

        payload = {
            "application": "polaris-vessels-v1",
            "fileName": self.json_file_name,
            "hostName": socket.gethostname(),
            "imoCode": imo_code,
            "schemaVersion": 1,
            "timeStampEpoch": int(time.time()),
            "url": obs.vessel_url,
            "observation": obs.to_dict(),
        }

        payload["observation"]["arrivalDate"] = (
            PolarisUtility.port_datetime(obs.arrival_date).isoformat()
            if obs.arrival_date
            else None
        )
        payload["observation"]["departureDate"] = (
            PolarisUtility.port_datetime(obs.departure_date).isoformat()
            if obs.departure_date
            else None
        )

        return payload

    def json_writer(self, payload: dict[str, any]) -> None:
        try:
            with open(f"{self.fresh_dir}/{self.json_file_name}", "w") as out_file:
                json.dump(payload, out_file, indent=4)
        except Exception as error:
            print(error)

    def execute(self, stunt: str, arg: str) -> dict[str, any]:
        parser = VesselParser()
        obs_dict = {}

        if stunt == "file":
            # file reads raw html from file system, does not write html/json
            print(f"file stunt: {arg}")
            raw_html = self.html_reader(arg)
            obs = parser.parse(raw_html)
            obs_dict = self.json_preamble(obs)
        elif stunt == "net":
            # net reads raw html from network, and writes html/json
            # print(f"net stunt: {arg}")
            scraper = VesselScraper(self.fresh_dir, arg)
            raw_html = scraper.fetch(self.html_file_name, True)
            obs = parser.parse(raw_html)
            obs_dict = self.json_preamble(obs)
            self.json_writer(obs_dict)
        elif stunt == "test":
            print(f"test stunt: {arg}")
            raw_html = self.html_reader(arg)
            obs = parser.parse(raw_html)
            obs_dict = self.json_preamble(obs)
            print(obs_dict)
        else:
            print("unknown stunt")

        return obs_dict


#
# vessels development
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
            driver = VesselDriver(configuration["freshDir"])
            #            driver.execute("file", "/var/polaris/fresh/e84acc3f-6bd3-423a-8f2b-0bd034bb868d.html")

            # tanker PEGASUS VOYAGER
            #driver.execute(
            #    "net", "https://www.vesselfinder.com/vessels/details/9665736"
            #)
            # driver.execute("test", "../../sample/fa17379f-e3bd-4540-9fb6-59bfadcc5372.html")

            driver.execute("test", "../../sample/ed7e60f3-9f11-4f70-8259-6ec8e64526c9.html")

            # tanker CHANTAL
            # driver.execute("net", "https://www.vesselfinder.com/vessels/details/9382982")

            # bulker JADE WEALTH
            # driver.execute("test", "../../sample/ddf84d24-ac17-49d2-acf5-d1133fad3be7.html")
        except yaml.YAMLError as error:
            print(error)

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
