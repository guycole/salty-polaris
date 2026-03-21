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

class Driver:
    def __init__(self, configuration: dict[str, any]) -> None:
        self.fresh_dir = configuration["freshDir"]
        self.vessel_targets = configuration["vesselTargets"]

    def json_reader(self, file_name: str) -> dict[str, any]:
        results = {}

        try:
            with open(file_name, "r") as in_file:
                results = json.load(in_file)
                results['file_name'] = file_name
        except Exception as error:
            print(error)

        return results

    def port_processor(self, candidate: dict[str, any]) -> None:
        print(f"port {candidate['portCode']} has {len(candidate['vessels'])} vessels")

        vessels = candidate['vessels']
        for vessel in vessels:
            print(f"{vessel['name']}")
            imo = vessel['vesselUrl'].split("/")[-1]
            print(f"IMO: {imo}")

    def execute(self) -> None:
        json_test_filename = "/var/polaris/fresh/USSFO001-1774054861.json"

        candidate = self.json_reader(json_test_filename)
        if candidate['application'] == "polaris-ports-v1":
            self.port_processor(candidate)
        elif candidate['application'] == "polaris-vessels-v1":
            print("vessel")
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
