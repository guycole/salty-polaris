#
# Title: polaris_app.py
# Description: driver for polaris application
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
import logging
import os

from ports import PortDriver, PortParser
from vessels import VesselDriver, VesselScraper

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

#from scorer import Scorer
#from validator import Validator
from postgres import PostGres

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("polaris")


class PolarisApp:

    def __init__(self, stunt_box: str):
        self.stunt_box = stunt_box

        self.cooked_dir = "/var/polaris/cooked"
        self.fail_dir = "/var/polaris/failure"
        self.fresh_dir = "/var/polaris/fresh"

#        self.db_conn = "postgresql+psycopg2://polaris_client:batabat@host.docker.internal:5432/polaris"
#        self.db_conn = "postgresql+psycopg2://polaris_client:batabat@172.17.0.1:5432/polaris"
        self.db_conn = "postgresql+psycopg2://polaris_client:batabat@127.0.0.1:5432/polaris"
        db_engine = create_engine(self.db_conn, echo=False)
        self.postgres = PostGres(sessionmaker(bind=db_engine, expire_on_commit=False))

    def get_port_urls(self) -> list[str]:
    
        ports_list = self.postgres.port_select_for_scrape()

        # TODO if ports list is empty build urls from default ports
        
        return ports_list

    def vessel_collection(self, vessel_list) -> None:
        print(f"vessel collection: {len(vessel_list)} vessels")

#        deduplicated_vessels = {}

#        for vessel in vessel_list:
#            print(vessel)
#            print(vessel.vessel_url)

#            deduplicated_vessels[vessel.vessel_url] = vessel

#            vessel_driver = VesselDriver({"freshDir": self.fresh_dir})
#            vessel_driver.execute(vessel.vessel_url, False)

    def port_file(self, port_dict: dict[str, any]) -> None:
        print(f"port file: {port_dict['fileName']}")

        file_name = port_dict["fileName"]
        if self.postgres.load_log_select_by_file_name(file_name) is not None:
            logger.info(f"skipping known file {file_name}")
            return

    def file_driver(self) -> None:  
        os.chdir(self.fresh_dir)
        targets = os.listdir(".")
        logger.info(f"{len(targets)} files noted")

        for target in targets:
            if target.endswith(".html"):
                logger.info(f"processing {target}")

                raw_html_file = os.path.join(self.fresh_dir, target)

                port_driver = PortDriver(self.fresh_dir)
                port_dict = port_driver.execute("file", raw_html_file)
                if port_dict['portCode'] != "bogus":
                    self.port_file(port_dict)

    def net_driver(self) -> None:
        pass

    def execute(self) -> None:
        logger.info(f"polaris execute")

        if self.stunt_box == "file":
            self.file_driver()
        elif self.stunt_box == "net":
            logger.info(f"stunt box: net")
            self.net_driver()

if __name__ == "__main__":
    # stunt_box options: "file" and "net"
    stunt_box = os.environ.get("stuntbox", "file")

    app = PolarisApp(stunt_box)
    app.execute()

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
