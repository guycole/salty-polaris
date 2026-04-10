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
from utility import PolarisUtility

logger = logging.getLogger(__name__)

import yaml
from yaml.loader import SafeLoader

from bs4 import BeautifulSoup

from dataclasses import dataclass, field
from urllib.parse import urljoin

import sqlalchemy
from sqlalchemy import Integer, and_, create_engine, null
from sqlalchemy import func
from sqlalchemy import select

from sql_table import (
    PolarisLoadLog,
    PolarisObservation,
    PolarisPort,
    PolarisVessel,
    PolarisVisit
)

from vessels import VesselDriver

@dataclass
class VisitRecord:
    date_arrival: datetime.date
    date_departure: datetime.date
    imo_code: str
    in_port: bool
    locode_current: str
    locode_destination: str
    locode_last: str

    def __repr__(self) -> str:
        return f"VisitRecord(date_arrival={self.date_arrival}, date_departure={self.date_departure}, imo_code={self.imo_code}, in_port={self.in_port}, locode_current={self.locode_current}, locode_destination={self.locode_destination})"

class VisitDriver:
    def __init__(self, fresh_dir: str, session: sqlalchemy.orm.session.sessionmaker):
        self.fresh_dir = fresh_dir
        self.postgres = PostGres(session)

        self.default_date = datetime.datetime(1970, 1, 1)
        self.time_now = datetime.datetime.now()

    def normalize_date(self, value: any) -> datetime.date:
        if isinstance(value, datetime.datetime):
            return value.date()
        if isinstance(value, datetime.date):
            return value
        if isinstance(value, str) and value.strip():
            parsed = PolarisUtility.port_datetime(value)
            if parsed is not None:
                return parsed.date()
        return self.default_date.date()

    def visit_departure(self, duration_days: int, json_dict: dict[str, any]) -> None:
        # Update the visit record for vessel departure
        print(f"visit departure for {json_dict['name']} ({json_dict['imoCode']})")

        vessel_driver = VesselDriver(self.fresh_dir)
        vessel_dict = vessel_driver.execute("net", json_dict["vesselUrl"])

        raw_departure = json_dict.get("departure")
        if not raw_departure:
            raw_departure = vessel_dict["observation"].get("departureDate")

        args = {
            "date_departure": self.normalize_date(raw_departure),
            "duration_days": duration_days,
            "imo_code": json_dict["imoCode"],
            "locode_destination": vessel_dict["observation"]["destinationLoCode"],
        }

        self.postgres.visit_update_departure(args)

    def visit_insert(self, json_dict: dict[str, any]) -> None:
        print(f"visit insert for {json_dict['name']} ({json_dict['arrival']})")

        print(json_dict)

        vessel_driver = VesselDriver(self.fresh_dir)
        vessel_dict = vessel_driver.execute("net", json_dict["vesselUrl"])
        print("xxxxxxxxx")
        print(vessel_dict)

        raw_arrival = json_dict.get("arrival")
        if not raw_arrival:
            raw_arrival = vessel_dict["observation"].get("arrivalDate")

        raw_departure = json_dict.get("departure")
        if not raw_departure:
            raw_departure = vessel_dict["observation"].get("departureDate")

        args = {
            "date_arrival": self.normalize_date(raw_arrival),
            "date_departure": self.normalize_date(raw_departure),
            "duration_days": 0,
            "imo_code": json_dict["imoCode"],
            "in_port": json_dict["inPort"],
            "locode_current": json_dict["loCode"],
            "locode_destination": vessel_dict["observation"].get("destinationLoCode", "XXXXX"),
            "locode_last": vessel_dict["observation"]["lastLoCode"],
        }

        self.postgres.visit_insert(args)

    def visit_v1(self, json_dict: dict[str, any]) -> None:
        print("visit v1")

#        print(json_dict)

        for vessel in json_dict["vessels"]:
            print(f"processing vessel {vessel['name']} ({vessel['imoCode']})")

            if vessel['grossTon'] < 400:
                print("skipping vessel with gross tonnage < 400")
                continue

            if len(vessel["arrival"]) > 0:
                temp_dt = PolarisUtility.port_datetime(vessel["arrival"])
                if temp_dt is None:
                    continue
                temp = temp_dt.date()
                if temp > self.time_now.date():
                    print("skipping future arrival date")
                    continue

                vessel["arrival"] = temp
                print("arrival vessel is inport")
                vessel["inPort"] = True
    
            if len(vessel["departure"]) > 0:
                temp_dt = PolarisUtility.port_datetime(vessel["departure"])
                if temp_dt is None:
                    continue
                temp = temp_dt.date()
                vessel["departure"] = temp

                print("departure vessel is not inport")
                vessel["inPort"] = False

            duration = 0
            selected = self.postgres.visit_select_by_imo_and_active(vessel["imoCode"])
            if len(selected) < 1:
                print(f"no visit record found for {vessel['name']}")
                if vessel["inPort"]:
                    print(f"inport true for {vessel['name']}")
                    self.visit_insert(vessel)
            elif len(selected) == 1:
                print(f"visit record already exists for {vessel['name']}")
                if vessel["inPort"]:
                    print(f"inport true for {vessel['name']}")
                else:
                    print(f"inport false1 for {vessel['name']}")
                    duration = (vessel["departure"] - selected[0].date_arrival).days
                    self.visit_departure(duration, vessel)
            else:
                print(f"multiple records for {vessel['name']}")
                self.visit_departure(duration, vessel)

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
