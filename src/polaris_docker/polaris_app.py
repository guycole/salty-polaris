#
# Title: polaris_app.py
# Description: driver for polaris application
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
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

    def execute(self) -> None:
        logger.info(f"polaris execute:{self.stunt_box}")

#        loader = PolarisLoader({
#            "freshDir": "/var/polaris/fresh",
#            "vesselTargets": []
#        }, self.postgres)
#        loader.execute()

        if self.stunt_box == "port_collection":
            port_driver = PortDriver({})
            #port_driver = PortDriver(self.postgres)
            #scorer = Scorer(self.postgres)
            #scorer.scorer(self.score_limit)
#        elif self.stunt_box == "validate":
#            validator = Validator(self.postgres)
#            validator.validate()
        else:
            logger.error(f"invalid stunt_box option:{self.stunt_box}")
            return


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
