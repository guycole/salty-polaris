#
# Title: loader.py
# Description: polaris database loader
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
import json
import logging
import sys

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from postgres import PostGres

logger = logging.getLogger(__name__)

import yaml
from yaml.loader import SafeLoader

class Loader:
    def __init__(self) -> None:
#        self.db_conn = "postgresql+psycopg2://polaris_client:batabat@host.docker.internal:5432/polaris"
#        self.db_conn = "postgresql+psycopg2://polaris_client:batabat@172.17.0.1:5432/polaris"
        self.db_conn = "postgresql+psycopg2://polaris_client:batabat@127.0.0.1:5432/polaris"
        db_engine = create_engine(self.db_conn, echo=False)
        self.postgres = PostGres(sessionmaker(bind=db_engine, expire_on_commit=False))

    def json_reader(self, file_name: str) -> dict[str, any]:
        results = {}

        try:
            with open(file_name, "r") as in_file:
                results = json.load(in_file)
        except Exception as error:
            print(error)

        return results
    
    def json_to_vessel_dict(self, json_dict: dict[str, any]) -> dict[str, any]:
        vessel_dict = {}
        vessel_dict["ais_type"] = json_dict['observation']["aisType"]
        vessel_dict["beam"] = json_dict['observation']["beam"]
        vessel_dict["built_year"] = json_dict['observation']["built"]
        vessel_dict["callsign"] = json_dict['observation']["callsign"]
        vessel_dict["gross_ton"] = json_dict['observation']["grossTon"]
        vessel_dict["imo_code"] = json_dict['observation']["imo"]
        vessel_dict["length"] = json_dict['observation']["length"]
        vessel_dict["mmsi_code"] = json_dict['observation']["mmsi"]
        vessel_dict["url"] = json_dict["url"]
        vessel_dict["vessel_flag"] = json_dict['observation']["flag"]
        vessel_dict["vessel_name"] = json_dict['observation']["name"]

        return vessel_dict

    def json_to_observation_dict(self, json_dict: dict[str, any]) -> dict[str, any]:
        dest = "dest"
        arrival = datetime(1971, 1, 1, 0, 1, tzinfo=timezone.utc)
        origin = "origin"
        departure = datetime(1971, 1, 1, 0, 1, tzinfo=timezone.utc)

        observation_dict = {}
        observation_dict["imo_code"] = json_dict['observation']["imo"]
     
        observation_dict["time_stamp"] = datetime.fromtimestamp(json_dict["timeStampEpoch"], tz=timezone.utc)
        observation_dict["course"] = float(json_dict['observation']["course"])
        observation_dict["speed"] = float(json_dict['observation']["speed"])
        observation_dict["nav_status"] = json_dict['observation']["navigationStatus"]
        observation_dict["dest_code"] = dest
        observation_dict["arrival"] = arrival
        observation_dict["origin_code"] = origin
        observation_dict["departure"] = departure

        return observation_dict
        
    def eclectic(self, vessel_dict: dict[str, any], obs_dict: dict[str, any]) -> None:
        print(f"eclectic: {vessel_dict}")
        vessel_row = self.postgres.vessel_select_by_imo(vessel_dict["imo_code"])
        print(f"row: {vessel_row}")
        if vessel_row is None:
            # insert unknown vessel
            vessel_row = self.postgres.vessel_insert(vessel_dict)
    
        obs_row = self.postgres.observation_insert(obs_dict)
        print(obs_row)

    def execute(self, file_names: list[str]) -> None:
        for file_name in file_names:
            json_dict = self.json_reader(file_name)
            if json_dict['application'] == "polaris-vessels-v1":
                vessel_dict = self.json_to_vessel_dict(json_dict)
                obs_dict = self.json_to_observation_dict(json_dict)
                self.eclectic(vessel_dict, obs_dict)
#            else:
#                print(f"skipping {file_name} with application {json_dict['application']}")

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
            driver = Loader()
            driver.execute(configuration["vesselObservations"])
        except yaml.YAMLError as error:
            print(error)

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
