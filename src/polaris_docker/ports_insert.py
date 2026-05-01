"""
format ports for postgres
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

import yaml
from yaml.loader import SafeLoader

class PortInsert:
    def __init__(self, configuration: dict[str, any]):
        pass

    def execute(self, file_name:str) -> None:
        buffer = None
        
        try:
            with open(file_name, "r", encoding="utf-8") as in_file:
                buffer = in_file.readlines()
        except Exception as error:
            print(error)
            return ""

        for row in buffer:
            if len(row) > 3:
                tokens = row.split(",")
                name = tokens[0].strip()
                url = tokens[1].strip()

                tokens = url.split("/")
                locode = tokens[-1][:5]

                print(f"insert into polaris_port(locode, name, scrape_flag, url) values('{locode}', '{name}', false, '{url}');")

#
# ports insert
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
            driver = PortInsert(configuration)
            driver.execute("f1")
        except yaml.YAMLError as error:
            print(error)

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
