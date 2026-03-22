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

from vessels import VesselScraper

from postgres import PostGres

class PolarisLoader:
    def __init__(self, configuration: dict[str, any], postgres: PostGres) -> None:
        self.fresh_dir = configuration["freshDir"]
        self.vessel_targets = configuration["vesselTargets"]
        self.postgres = postgres
    def json_reader(self, file_name: str) -> dict[str, any]:
        results = {}

        try:
            with open(file_name, "r") as in_file:
                results = json.load(in_file)
                results['file_name'] = file_name
        except Exception as error:
            print(error)

        return results

    def get_vessel(self, vessel_url: str) -> dict[str, any]:
        time_stamp = int(time.time())

        scraper = VesselScraper(self.fresh_dir, time_stamp, vessel_url)
        vessel_json = scraper.collection(None)
        print(vessel_json)

        imo = vessel_url.split("/")[-1]
#        imo = '8834407'
        print(imo)

        print("aaaaaaa")
        candidate = self.postgres.vessel_select_by_imo(imo)
        print("xxxxxxx")
        print(candidate)
        if candidate is None:
            print("inserting")
            candidate = self.postgres.vessel_insert_or_update(vessel_json)

        vessel_data = None
    
        return vessel_data

    def port_processor(self, candidate: dict[str, any]) -> None:
        print(f"port {candidate['portCode']} has {len(candidate['vessels'])} vessels")

        vessels = candidate['vessels']
        for vessel in vessels:
            print(f"{vessel['name']}")
            imo = vessel['vesselUrl'].split("/")[-1]
            print(f"IMO: {imo}")
            # test for imo in vessel table
            vessel_data = self.get_vessel(vessel['vesselUrl'])
        



    def execute(self) -> None:
        json_test_filename = "/var/polaris/fresh/USSFO001-1774054861.json"
        json_test_filename = "/var/polaris/fresh/USSFO001-1774113421.json"

        candidate = self.json_reader(json_test_filename)
        if candidate['application'] == "polaris-ports-v1":
            self.port_processor(candidate)
        else:
            print("unknown")
            print(candidate['application'])

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
