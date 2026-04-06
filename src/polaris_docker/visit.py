import datetime
import json
import logging
import os
import random
import requests
import socket
import sys
import time
import uuid

from postgres import PostGres

logger = logging.getLogger(__name__)

import yaml
from yaml.loader import SafeLoader

from bs4 import BeautifulSoup

from dataclasses import dataclass, field
from urllib.parse import urljoin

import sqlalchemy
from sqlalchemy import and_, create_engine
from sqlalchemy import func
from sqlalchemy import select

from sql_table import (
    PolarisLoadLog,
    PolarisObservation,
    PolarisPort,
    PolarisVessel,
    PolarisVisit
)

class VisitDriver:
    def __init__(self, session: sqlalchemy.orm.session.sessionmaker):
        self.postgres = PostGres(session)

        self.default_date = datetime.datetime(1970, 1, 1)

#        imo = "9538971" 
#        selected = self.postgres.vessel_select_by_imo(imo)
#        print(selected)

    def visit_v1(self, json_dict: dict[str, any]) -> None:
        print("visit v1")

        print(json_dict)

        for vessel in json_dict["vessels"]:
            if vessel['grossTon'] < 400:
                print("skipping vessel with gross tonnage < 400")
                continue

            selected = self.postgres.visit_select_by_imo_and_active(vessel["imoCode"])
            print(selected)

            if vessel["inPort"]:
                print(f"inport true for {vessel['name']}")
            else:
                print(f"inport false for {vessel['name']}")

#        selected = self.postgres.vessel_select_by_imo(vessel["imoCode"])
#        print(selected)
    

    def visit_vx(self, json_dict: dict[str, any]) -> None:
        print("visit v1")

        for vessel in json_dict["vessels"]:
            print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
            print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" + str(vessel['grossTon']))

            if vessel['grossTon'] < 400:
                print("skipping vessel with gross tonnage < 400")
                continue

            print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
            print(vessel)
            print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
                
            selected = self.postgres.vessel_select_by_imo(vessel["imoCode"])
            print(selected)

            arrival = self.port_datetime(vessel["arrival"])
            departure = self.port_datetime(vessel["departure"])

            print(f"arrival: {arrival}, departure: {departure}")

#                self.postgres.visit_insert(
#                    {
#                        "date_arrival": arrival.date(),
#                        "date_departure": departure.date(),
#                        "imo_code": vessel["imoCode"],
#                        "in_port": vessel["inPort"],
#                        "locode_current": vessel["loCode"],
#                        "locode_destination": "fixme",  
#                        "locode_last": "fixme",
#                   }
#                )

    def execute(self, stunt: str, arg: str) -> dict[str, any]:
        parser = PortParser()
        port_dict = {}

        if stunt == "file":
            # file reads raw html from file system, does not write html/json
            print(f"file stunt: {arg}")
            raw_html = self.html_reader(arg)
            vessel_list = parser.parse(raw_html)
            port_dict = self.json_preamble(vessel_list)
        elif stunt == "net":
            # net reads raw html from network, and writes html/json
            # print(f"net stunt: {arg}")
            scraper = PortScraper(self.fresh_dir, arg)
            raw_html = scraper.fetch(self.html_file_name, True)
            vessel_list = parser.parse(raw_html)
            port_dict = self.json_preamble(vessel_list)
            self.json_writer(port_dict)
        elif stunt == "test":
            print(f"test stunt: {arg}")
            raw_html = self.html_reader(arg)
            vessel_list = parser.parse(raw_html)
            for vessel in vessel_list:
                print(vessel.to_dict())
            port_dict = self.json_preamble(vessel_list)
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
            driver.execute("test", "/var/polaris/fresh/fa94efb1-8d06-4aed-b5a8-f1e6ea635f49.html")
            #driver.execute("net", "https://www.vesselfinder.com/ports/USBNC001")
        except yaml.YAMLError as error:
            print(error)

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
