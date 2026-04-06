#
# Title: polaris_app.py
# Description: driver for polaris application
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
import datetime
import json
import logging
import os

from ports import PortDriver, PortParser
from vessels import VesselDriver, VesselScraper
from visit import VisitDriver

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from postgres import PostGres

import yaml
from yaml.loader import SafeLoader

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("polaris")

class PolarisApp:

    def __init__(self, configuration: dict[str, any]):
        self.stunt_box = configuration['stunt_box']

        self.failure_dir = "/var/polaris/failure"
        self.fresh_dir = "/var/polaris/fresh"
        self.success_dir = "/var/polaris/success"

        self.failure = 0
        self.success = 0
        
        self.db_conn = configuration['dbConn']
        db_engine = create_engine(self.db_conn, echo=False)
        self.postgres = PostGres(sessionmaker(bind=db_engine, expire_on_commit=False))

    def file_failure(self, file_name: str):
        logger.info(f"file failure:{file_name}")

        self.failure += 1
        os.rename(file_name, self.failure_dir + "/" + file_name)

    def file_success(self, file_name: str):
        #        logger.info(f"file success:{file_name}")

        self.success += 1
        os.rename(file_name, self.success_dir + "/" + file_name)

    def get_port_urls(self) -> list[str]:
        ports_list = self.postgres.port_select_for_scrape()
        return ports_list

    def json_reader(self, file_name: str) -> dict[str, any]:
        results = {}

        try:
            with open(file_name, "r") as in_file:
                results = json.load(in_file)
        except Exception as error:
            logger.error(f"json read error for {file_name}: {error}")

        return results

    def port_datetime(self, arg: str) -> datetime.datetime:
        """
        Convert a string like 'Apr 14, 02:00' to a datetime with the current year.
        Returns 1 JAN 1970 if arg is empty or invalid.
        """
        if not arg or not arg.strip():
            return datetime.datetime(1970, 1, 1)
        try:
            # Use current year (timezone-aware UTC)
            this_year = datetime.datetime.now(datetime.UTC).year
            # Example: 'Apr 14, 02:00' -> 'Apr 14 2026 02:00'
            dt = datetime.datetime.strptime(
                f"{arg.strip()} {this_year}", "%b %d, %H:%M %Y"
            )
            return dt
        except Exception as e:
            logger.warning(f"Could not parse port datetime from '{arg}': {e}")
            return None

    def port_load_log_insert(self, json_dict: dict[str, any]) -> None:
        if "hostName" not in json_dict:
            json_dict["hostName"] = "unknown"

        # Convert epoch seconds to ISO 8601 timestamp string with UTC timezone for Postgres
        file_time_epoch = json_dict["timeStampEpoch"]
        file_time = datetime.datetime.fromtimestamp(
            file_time_epoch, tz=datetime.timezone.utc
        ).isoformat(sep=" ", timespec="seconds")
        # Ensure 'Z' suffix for UTC (Postgres compatible)
        if file_time.endswith("+00:00"):
            file_time = file_time[:-6] + "Z"

        args = {
            "file_name": json_dict["fileName"],
            "file_time": file_time,
            "file_type": json_dict["application"],
            "obs_quantity": len(json_dict["vessels"]),
            "host_name": json_dict["hostName"],
            "locode": json_dict["loCode"],
        }

        self.postgres.load_log_insert(args)

    def port_observation(self, vessel_dict: dict[str, any]) -> None:
        args = {
            "imo_code": vessel_dict["imoCode"],
            "obs_time": datetime.datetime.now(),
            "locode": vessel_dict["loCode"],
            "arrival": self.port_datetime(vessel_dict["arrival"]),
            "departure": self.port_datetime(vessel_dict["departure"]),
            "in_port": vessel_dict["inPort"],
        }

        self.postgres.observation_insert(args)

    def port_v1(self, file_flag: bool, json_dict: dict[str, any]) -> None:
        # process port scrape

        logger.info(
            f"port v1: {json_dict['loCode']} {len(json_dict['vessels'])} vessels"
        )

        vessel_request = {}

        for vessel in json_dict["vessels"]:
            imo = vessel["vesselUrl"].split("/")[-1]
            selected = self.postgres.vessel_select_by_imo(imo)
            if selected is None:
                vessel_request[imo] = vessel["vesselUrl"]
            else:
                self.port_observation(vessel)

        self.port_load_log_insert(json_dict)

        logger.info(f"missing vessels: {len(vessel_request)} vessels requested")

        if file_flag:
            logger.info("skipping vessel request")
        else:
            # now add missing vessel details
            for key in vessel_request:
                logger.info(f"requesting vessel {key} from {vessel_request[key]}")
                driver = VesselDriver(self.fresh_dir)
                vessel_dict = driver.execute("net", vessel_request[key])
                self.vessel_v1_insert(vessel_dict)
#                self.port_observation(vessel_dict)

    def vessel_v1_insert(self, vessel_dict: dict[str, any]) -> None:
        imo_code = vessel_dict["url"].split("/")[-1]

        selected = self.postgres.vessel_select_by_imo(imo_code)
        if selected is None:
            args = {
                "ais_type": vessel_dict["observation"]["aisType"],
                "beam": vessel_dict["observation"]["beam"],
                "built_year": vessel_dict["observation"]["built"],
                "callsign": vessel_dict["observation"]["callsign"],
                "gross_ton": vessel_dict["observation"]["grossTon"],
                "imo_code": imo_code,
                "length": vessel_dict["observation"]["length"],
                "mmsi_code": vessel_dict["observation"]["mmsi"],
                "url": vessel_dict["url"],
                "vessel_flag": vessel_dict["observation"]["flag"],
                "vessel_name": vessel_dict["observation"]["name"],
            }

            if args["ais_type"] is None or args["ais_type"] == "":
                args["ais_type"] = "Unknown"

            if args["beam"] is None or args["beam"] == "":
                args["beam"] = 0

            if args["built_year"] is None or args["built_year"] == "":
                args["built_year"] = 1900

            if args["gross_ton"] is None or args["gross_ton"] == "":
                args["gross_ton"] = 0

            if args["length"] is None or args["length"] == "":
                args["length"] = 0

            if args["mmsi_code"] is None or args["mmsi_code"] == "":
                args["mmsi_code"] = "000000000"

            self.postgres.vessel_insert(args)

    def file_driver(self) -> None:
        os.chdir(self.fresh_dir)
        targets = os.listdir(".")
        logger.info(f"{len(targets)} files noted")

        for target in targets:
            if target.endswith(".json"):
                # vessels load first
                json_dict = self.json_reader(target)

                if "application" not in json_dict:
                    self.file_failure(target)
                elif json_dict["application"] == "polaris-vessels-v1":
                    self.vessel_v1_insert(json_dict)
                    self.file_success(target)
            else:
                logger.warning(f"skipping file: {target}")
                self.file_failure(target)

        targets = os.listdir(".")
        logger.info(f"{len(targets)} port files noted")
        for target in targets:
            json_dict = self.json_reader(target)

            if "application" not in json_dict:
                self.file_failure(target)
                continue

            if json_dict["application"] == "polaris-ports-v1":
                try:
                    self.port_v1(True, json_dict)

                    visit_driver = VisitDriver(self.postgres.Session)
                    visit_driver.visit_v1(json_dict)

                    self.file_success(target)
                except Exception as error:
                    logger.info(error)
                    self.file_failure(target)
            else:
                logger.info(f"unknown file type: {target}")
                self.file_failure(target)

    def net_driver(self) -> None:
        # read port urls from database and scrape each one
        ports_urls = self.get_port_urls()
        ports_urls = ["https://www.vesselfinder.com/ports/USSAC001"]
        for port_url in ports_urls:
            logger.info(f"processing {port_url}")
            port_driver = PortDriver(self.fresh_dir)
            port_dict = port_driver.execute("net", port_url)
            self.port_v1(False, port_dict)

            visit_driver = VisitDriver(self.postgres.Session)
            visit_driver.visit_v1(port_dict)

    def execute(self) -> None:
        logger.info(f"polaris execute")

        if self.stunt_box == "file":
            self.file_driver()
        elif self.stunt_box == "net":
            logger.info(f"stunt box: net")
            self.net_driver()


if __name__ == "__main__":
    configuration = {}
    
    file_name = "config.yaml"

    with open(file_name, "r") as in_file:
        try:
            configuration = yaml.load(in_file, Loader=SafeLoader)
        except yaml.YAMLError as error:
            print(error)

    # stunt_box options: "file" and "net"
    configuration['stunt_box'] = os.environ.get("stuntbox", "net")
#    configuration['stunt_box'] = os.environ.get("stuntbox", "file")

    app = PolarisApp(configuration)
    app.execute()

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
