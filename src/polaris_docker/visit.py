import datetime
import logging
import sys

from postgres import PostGres
from vessels import VesselDriver

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
    def __init__(self, fresh_dir: str, session: sqlalchemy.orm.session.sessionmaker):
        self.fresh_dir = fresh_dir
        self.postgres = PostGres(session)

        self.default_date = datetime.datetime(1970, 1, 1)

    def visit_insert(self, vessel_dict: dict[str, any]) -> None:
        print(f"visit insert for {vessel_dict['name']} ({vessel_dict['arrival_date']})")

        vessel_driver = VesselDriver(self.fresh_dir)
        detail_dict = vessel_driver.execute("net", vessel_dict["vessel_url"])
        print(detail_dict)

        args = {
            "active_flag": True,
            "date_arrival": vessel_dict["arrival_date"],
            "date_departure": vessel_dict["departure_date"],
            "duration_days": 0,
            "imo_code": vessel_dict["imo_code"],
            "in_port": vessel_dict["in_port"],
            "locode_destination": detail_dict["observation"].get("destinationLoCode", "XXXXX"),
            "locode_last": detail_dict["observation"]["lastLoCode"],
        }

        if args["date_departure"] != self.default_date:
            args["active_flag"] = False
            args["duration_days"] = (args["date_departure"] - args["date_arrival"]).days

        if args["duration_days"] < 0:
            args["duration_days"] = 0

        if args["locode_last"] is None or args["locode_last"] == "":
            args["locode_last"] = "XXXXX"

        if args["locode_destination"] is None or args["locode_destination"] == "":
            args["locode_destination"] = "XXXXX"

        self.postgres.visit_insert(args)

    def visit_update(self, vessel_dict: dict[str, any]) -> None:
        print(f"visit update for {vessel_dict['name']} ({vessel_dict['imo_code']})")

        vessel_driver = VesselDriver(self.fresh_dir)
        detail_dict = vessel_driver.execute("net", vessel_dict["vessel_url"])
        print(detail_dict)

        args = {
            "active_flag": False,
            "date_departure": vessel_dict["departure_date"],
            "duration_days": (vessel_dict["departure_date"] - vessel_dict["arrival_date"]).days,
            "imo_code": vessel_dict["imo_code"],
            "locode_destination": detail_dict["observation"].get("destinationLoCode", "XXXXX"),
        }

        if args["duration_days"] < 0:
            args["duration_days"] = 0

        if args["locode_destination"] is None or args["locode_destination"] == "":
            args["locode_destination"] = "XXXXX"

        self.postgres.visit_update_departure(args)

    def visit_cooker(self, vessel_dict: dict[str, any]) -> None:
        print(f"visit cooker {vessel_dict['name']} ({vessel_dict['imo_code']})")

        # update existing or insert fresh?
        selected = self.postgres.visit_select_by_imo_and_active(vessel_dict["imo_code"])
        print(f"visit cooker selected: {len(selected)} records")

        if len(selected) < 1:
            print("visit cooker no active visit")
            self.visit_insert(vessel_dict)
        elif vessel_dict["departure_date"] == self.default_date:
            print("visit cooker active visit with no departure date")
        else:
            print("visit cooker update visit with departure date")
            self.visit_update(vessel_dict)

    def observation_insert(self, lo_code: str, obs_date: datetime.datetime, vessel: dict[str, any]) -> None:
        # print(f"Observation insert for {vessel['name']} ({vessel['imo_code']}) at {obs_date} in port {lo_code}")

        args = {
            "date_arrival": vessel["arrival_date"],
            "date_departure": vessel["departure_date"],
            "imo_code": vessel["imo_code"],
            "in_port": vessel["in_port"],
            "locode": lo_code,
            "obs_time": obs_date
        }

        self.postgres.observation_insert(args)

    def deduplicate(self, json_dict: dict[str, any]) -> dict[str, any]:
        # the raw json_dict may have duplicate vessels because single page application
        # which is scraped in the order "expected", "arrivals", "departures" and "in port"
        # iterate through the vessels merge the dates

        results = {}

        for vessel in json_dict["vessels"]:
            arrival_date = datetime.datetime.fromisoformat(vessel["arrivalDate"])
            departure_date = datetime.datetime.fromisoformat(vessel["departureDate"])
            imo_code = vessel["imoCode"] 
            in_port = vessel["inPort"]

            if imo_code not in results:
                results[imo_code] = {
                    "arrival_date": arrival_date,
                    "departure_date": departure_date,
                    "gross_ton": int(vessel["grossTon"]),
                    "imo_code": imo_code,
                    "in_port": in_port,
                    "name": vessel["name"],
                    "vessel_url": vessel["vesselUrl"]
                }
            else:
                current = results[imo_code]
                current["arrival_date"] = max(current["arrival_date"], arrival_date)
                current["departure_date"] = max(current["departure_date"], departure_date)
                current["in_port"] = current["in_port"] or in_port

        return results

    def visit_v1(self, json_dict: dict[str, any]) -> None:
        print("visit v1")

        #print(json_dict)

        obs_date = datetime.datetime.fromtimestamp(json_dict['timeStampEpoch'])

        vessels = self.deduplicate(json_dict)

        for key in vessels:
            vessel = vessels[key]
            print(f"{vessel['name']} ({vessel['imo_code']}) {vessel['gross_ton']} {vessel['in_port']} {vessel['arrival_date']} {vessel['departure_date']}")

            self.observation_insert(json_dict['loCode'], obs_date, vessel)

            if vessel['gross_ton'] < 400:
                print("skipping vessel with gross tonnage < 400")
                continue

            if vessel['arrival_date'] > obs_date:
                print("skipping vessel with arrival date in the future")
                continue

            selected = self.postgres.visit_select_for_duplicate(vessel["imo_code"], vessel["arrival_date"], vessel["departure_date"])
            if len(selected) < 1:
                self.visit_cooker(vessel)
            elif len(selected) == 1:
                print("skipping vessel with duplicate visit")
            else :
                print("ERROR: vessel with multiple duplicate visits")

#            selected = self.postgres.visit_select_for_duplicate(vessel["imo_code"], vessel["arrival_date"], vessel["departure_date"])
#        
#           selected = self.postgres.visit_select_by_imo_and_active(vessel["imo_code"])
#            if len(selected) < 1:
#                print("no active visit")
#
#               if vessel['in_port']:
#                    print("in port true, creating visit")
#                    self.arrival(vessel)
#                elif vessel['arrival_date'] > self.default_date:
#                    print("arrival date exists, creating visit")
#                    self.arrival(vessel)
#            elif len(selected) == 1:
#                print("one active visit")
#                if vessel['departure_date'] > self.default_date and vessel['departure_date'] < obs_date:
#                    print("departure date exists and in the past, updating visit")
#                    print(f"DEBUG: arrival_date type: {type(vessel['arrival_date'])}, value: {repr(vessel['arrival_date'])}")
#                    print(f"DEBUG: departure_date type: {type(vessel['departure_date'])}, value: {repr(vessel['departure_date'])}")
#                    print(f"DEBUG: timedelta: {vessel['departure_date'] - vessel['arrival_date']}")
#                    duration_days = (vessel['departure_date'] - vessel['arrival_date']).days
#                    self.departure(duration_days, vessel)
#            else:
#                print("multiple active visits")

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
