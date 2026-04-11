"""
discover missing ports
"""

import json
import logging
import os
import random
import requests
import socket
import sys
import time
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from postgres import PostGres

import yaml
from yaml.loader import SafeLoader

class PortGroom:
    def __init__(self, configuration: dict[str, any]):
        self.db_conn = configuration["dbConn"]
        db_engine = create_engine(self.db_conn, echo=False)
        self.postgres = PostGres(sessionmaker(bind=db_engine, expire_on_commit=False))

    def execute(self) -> None:
        print("execute")

        unique_ports = []
        selected_visits = self.postgres.visit_select_all()
        print(f"selected_visits: {len(selected_visits)}")

        for visit in selected_visits:
            if visit.locode_destination not in unique_ports:
                unique_ports.append(visit.locode_destination)

            if visit.locode_last not in unique_ports:
                unique_ports.append(visit.locode_last)

        print(f"unique_ports: {len(unique_ports)}")

        for port in unique_ports:
            if port == "XXXXX":
                continue

            temp = port[:5]
            selected = self.postgres.port_select_by_locode(port[:5])
            if selected is None:
                print(f"Port {temp} not found in database.")

#
# ports groomer
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
            driver = PortGroom(configuration)
            driver.execute()
        except yaml.YAMLError as error:
            print(error)

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
