#
# Title: polaris_app.py
# Description: driver for polaris application
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
from typing import List
import logging
import os

from ports import PortDriver, PortScraper
#from loader import PolarisLoader

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

#from scorer import Scorer
#from validator import Validator
from postgres import PostGres

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("polaris")


class PolarisApp:

    def __init__(self, args: dict[str, any]):
        self.stunt_box = args['stunt_box']

        self.cooked_dir = "/var/polaris/cooked"
        self.fail_dir = "/var/polaris/failure"
        self.fresh_dir = "/var/polaris/fresh"

#        self.db_conn = "postgresql+psycopg2://polaris_client:batabat@host.docker.internal:5432/polaris"
#        self.db_conn = "postgresql+psycopg2://polaris_client:batabat@172.17.0.1:5432/polaris"
        self.db_conn = "postgresql+psycopg2://polaris_client:batabat@127.0.0.1:5432/polaris"
        db_engine = create_engine(self.db_conn, echo=False)
        self.postgres = PostGres(sessionmaker(bind=db_engine, expire_on_commit=False))

    def get_port_urls(self) -> List[str]:
        default_ports = [
            "USBNC001", "USMRZ001", "USRD4001", "USSEL001", "USCRM001",
            "USPZH001", "USPBG001", "USANZ001", "USOQY001", "USSAC001",
            "USSCK001", "USRCH001", "USOAK001", "USSFO001", "USRWC002",
            "USMY3001", "USFOB001", "USEKA001", "USCEC001", "USVLO001"
        ]

        ports_list = self.postgres.port_select_for_scrape()

        # TODO if ports list is empty build urls from default ports
        
        return ports_list

    def port_collection(self):
        targets = self.get_port_urls()
        # TODO: Implement port collection logic
        pass

    def vessel_collection(self):
        pass

    def execute(self) -> None:
        logger.info(f"polaris execute")

        port_args = {
            "fresh_dir": self.fresh_dir,
        }

        port_urls = self.get_port_urls()
        logger.info(f"port_urls: {len(port_urls)}")

        port_driver = PortDriver(port_args)

if __name__ == "__main__":
    # stunt_box options: "score" and "validate"
    args = {
        "stunt_box":"port_collection"
    }

#    stunt_box = os.environ.get("stuntbox", "validate")

    app = PolarisApp(args)
    app.execute()

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
