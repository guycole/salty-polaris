
from dataclasses import dataclass
import sys
import json
from typing import Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time
import logging

logger = logging.getLogger(__name__)

import yaml
from yaml.loader import SafeLoader

@dataclass

class VesselObservation:
    name: str
    ais_type: Optional[str] = None
    beam: Optional[str] = None
    built: Optional[str] = None
    callsign: Optional[str] = None
    flag: Optional[str] = None
    gross_ton: Optional[str] = None
    imo: Optional[str] = None
    length: Optional[str] = None
    mmsi: Optional[str] = None
    vessel_url: Optional[str] = None

    course: Optional[str] = None
    speed: Optional[str] = None
    navigation_status: Optional[str] = None
    destination: Optional[str] = None
    destination_port_code: Optional[str] = None
    arrival_date: Optional[str] = None

    last_port: Optional[str] = None
    last_port_code: Optional[str] = None
    departure_date: Optional[str] = None

    def __repr__(self) -> str:
        return (f"VesselObservation(name={self.name!r}, type={self.ais_type!r}, flag={self.flag!r}, callsign={self.callsign!r}, gross_ton={self.gross_ton!r}, built={self.built!r})")

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "ais_type": self.ais_type,
            "beam": self.beam,
            "built": self.built,
            "callsign": self.callsign,
            "flag": self.flag,
            "gross_ton": self.gross_ton,
            "imo": self.imo,
            "length": self.length,
            "mmsi": self.mmsi,
            "vessel_url": self.vessel_url,
            "course": self.course,
            "speed": self.speed,
            "navigation_status": self.navigation_status,
            "destination": self.destination,
            "destination_port_code": self.destination_port_code,
            "arrival_date": self.arrival_date,
            "last_port": self.last_port,
            "last_port_code": self.last_port_code,
            "departure_date": self.departure_date
        }

class VesselScraper:
  
    def __init__(self, fresh_dir: str, time_stamp: int, url: str) -> None:
        port = VesselObservation(name="")
        self.fresh_dir = fresh_dir
        self.imo = url.split("/")[-1]
        self.time_stamp = time_stamp
        self.url = url

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

    def json_preamble(self) -> dict:
        return {
            "application": "polaris-vessels-v1",
            "imoCode": self.imo,
            "schemaVersion": 1,
            "timeStampEpoch": self.time_stamp,
            "url": self.url,
            "observation": {}
        }
    
    def json_writer(self, payload: dict) -> None:
        base_file_name = self.get_base_file_name()
        json_path = f"{base_file_name}.json"
        print(f"Writing to {json_path}")

        try:
            with open(json_path, "w") as out_file:
                json.dump(payload, out_file, indent=4)
        except Exception as error:
            print(error)

    def get_base_file_name(self) -> str:
        return f"{self.fresh_dir}/{self.imo}-{self.time_stamp}"

    def fetch(self, write_flag:bool) -> str:
        logger.info("fetching %s", self.url)

        response = requests.get(self.url, headers=self.headers, timeout=self.timeout)
        response.raise_for_status()

        if write_flag:
            base_file_name = self.get_base_file_name()
            html_path = f"{base_file_name}.html"

            with open(html_path, "w", encoding="utf-8") as f:
                f.write(response.text)

        return response.text
    
    def parse(self, raw_html: str) -> VesselObservation:
        soup = BeautifulSoup(raw_html, "html.parser")

        # Helper to get text from a table row by label
        def get_table_value(label: str) -> str:
            for td in soup.find_all('td'):
                if td.get_text(strip=True) == label:
                    next_td = td.find_next_sibling('td')
                    if next_td:
                        return next_td.get_text(strip=True)
            return None

        # Helper to get value from a/v3 table (Voyage Data)
        def get_aparams_value(label: str) -> str:
            for tr in soup.select('table.aparams tr'):
                tds = tr.find_all('td')
                if len(tds) == 2 and tds[0].get_text(strip=True) == label:
                    return tds[1].get_text(strip=True)
            return None

        # Vessel name (from h1.title)
        name = None
        h1 = soup.find('h1', class_='title')
        if h1:
            name = h1.get_text(strip=True)

        # AIS type (from "AIS Type" in Voyage Data)
        ais_type = get_aparams_value('AIS Type')

        # Flag (from "AIS Flag" in Voyage Data or Vessel Particulars)
        flag = get_aparams_value('AIS Flag')
        if not flag:
            arrival_port_code: Optional[str] = None

        # Built (from "Year of Build" in Vessel Particulars)
        built = get_table_value('Year of Build')

        # Gross tonnage (from "Gross Tonnage" in Vessel Particulars)
        gross_ton = get_table_value('Gross Tonnage')

        # IMO and MMSI (from "IMO / MMSI" in Voyage Data)
        imo, mmsi = None, None
        imo_mmsi = get_aparams_value('IMO / MMSI')
        if imo_mmsi and '/' in imo_mmsi:
            parts = [p.strip() for p in imo_mmsi.split('/')]
            if len(parts) == 2:
                imo, mmsi = parts
        else:
            imo = get_table_value('IMO number')

        # Callsign (from "Callsign" in Voyage Data)
        callsign = get_aparams_value('Callsign')

        # Length and Beam (from "Length / Beam" in Voyage Data or Vessel Particulars)
        length, beam = None, None
        len_beam = get_aparams_value('Length / Beam')
        if len_beam and '/' in len_beam:
            parts = [p.strip().replace(' m', '') for p in len_beam.split('/')]
            if len(parts) == 2:
                length, beam = parts
        else:
            length = get_table_value('Length Overall (m)')
            beam = get_table_value('Beam (m)')

        # Course and Speed (prefer djson data-json, fallback to table)
        course, speed = None, None
        djson_span = soup.find('div', id='djson')
        if djson_span and djson_span.has_attr('data-json'):
            import json as _json
            try:
                djson = _json.loads(djson_span['data-json'])
                course = str(djson.get('ship_cog')) if djson.get('ship_cog') is not None else None
                speed = str(djson.get('ship_sog')) if djson.get('ship_sog') is not None else None
            except Exception:
                pass
        if not course or not speed:
            course_speed = get_aparams_value('Course / Speed')
            if course_speed and '/' in course_speed:
                parts = [p.strip() for p in course_speed.split('/')]
                if len(parts) == 2:
                    course, speed = parts

        # Navigation Status (from "Navigation Status" in Voyage Data)
        navigation_status = get_aparams_value('Navigation Status')

        # Destination (from "Destination" in Voyage Data)
        destination = None
        destination_port_code = None
        arrival_date = None
        dest_div = soup.find('div', class_='vilabel', string='Destination')
        if dest_div:
            # The destination is in the next div with class _3-Yih
            next_div = dest_div.find_next('div', class_='_3-Yih')
            if next_div:
                # Normalize whitespace and use title case for city, upper for code
                dest_text = next_div.get_text(strip=True)
                if dest_text:
                    parts = dest_text.split()
                    if len(parts) > 1:
                        destination = parts[0].upper() + ' ' + ' '.join(parts[1:]).title()
                    else:
                        destination = dest_text.title()
            # Arrival date is in the next _value span with class _mcol12ext and contains 'ETA:'
            value_div = dest_div.find_next('div', class_='_value')
            if value_div:
                eta_span = value_div.find('span', class_='_mcol12ext')
                if eta_span and 'ETA:' in eta_span.get_text():
                    eta_text = eta_span.get_text()
                    # Extract just the date part after 'ETA:'
                    arrival_date = eta_text.split('ETA:')[1].split(',')[0].strip()

        # Arrival date (from "ATA" in Voyage Data)
        arrival_date = None
        ata_span = soup.find('span', class_='_mcol12')
        if ata_span and 'ATA:' in ata_span.get_text():
            arrival_date = ata_span.get_text().replace('ATA:', '').strip()

        # Last port and last port code (from "Last Port" in Voyage Data)
        last_port, last_port_code = None, None
        last_port_div = soup.find('div', class_='vilabel', string='Last Port')
        if last_port_div:
            last_port_a = last_port_div.find_next('a')
            if last_port_a:
                last_port = last_port_a.get_text(strip=True)
                if last_port_a.has_attr('href'):
                    last_port_code = last_port_a['href'].split('/')[-1]

        # Departure date (from "Last Port" and "ATD" in Voyage Data)
        departure_date = None
        last_port_div = soup.find('div', class_='vilabel', string='Last Port')
        if last_port_div:
            atd_div = last_port_div.find_next('div', class_='_value')
            if atd_div and 'ATD:' in atd_div.get_text():
                departure_date = atd_div.get_text().split('ATD:')[1].split('(')[0].strip()

        # Vessel URL (from self.url)
        vessel_url = self.url

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
            destination_port_code=destination_port_code,
            departure_date=departure_date,
            course=course,
            speed=speed,
            navigation_status=navigation_status,
            destination=destination,
            last_port=last_port,
            last_port_code=last_port_code,
        )

    def collection(self, raw_html: str) -> None:
        if raw_html is None:
            raw_html = self.fetch(True)
        else:
            print("Using provided raw HTML for collection")

        results = self.parse(raw_html)

        preamble = self.json_preamble()
        preamble["observation"] = results.to_dict()
        self.json_writer(preamble)

class Driver:
    def __init__(self, configuration: dict[str, any]) -> None:
        self.fresh_dir = configuration['freshDir']
        self.vessel_targets = configuration['vesselTargets']

    def execute(self) -> None:
        time_stamp = int(time.time())

        # NYK Vesta
        raw_html_file = "/var/polaris/fresh/9312808-1773960722.html"
        url = "https://www.vesselfinder.com/vessels/details/9312808"	

        # Polaris Voyager
        # raw_html_file = "/var/polaris/fresh/9665748-1773968398.html"
        url = "https://www.vesselfinder.com/vessels/details/9665748"

        raw_html = None
#        with open(raw_html_file, "r", encoding="utf-8") as f:
#            raw_html = f.read()

        for vessel_url in self.vessel_targets:
            scraper = VesselScraper(self.fresh_dir, time_stamp, vessel_url)
            scraper.collection(raw_html)

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