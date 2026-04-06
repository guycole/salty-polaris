#
# Title: sql_table.py
# Description: database table definitions
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
# from concurrent.interpreters import create
from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import BigInteger, Boolean, Date, DateTime, Float, Integer, String

from sqlalchemy.orm import registry
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.declarative import declared_attr

mapper_registry = registry()


class Base(DeclarativeBase):
    pass


class PolarisLoadLog(Base):
    """load_log table definition"""

    __tablename__ = "polaris_load_log"

    id = Column(Integer, primary_key=True)
    file_name = Column(String)
    file_time = Column(DateTime)
    file_type = Column(String)
    load_time = Column(DateTime)
    obs_quantity = Column(Integer)
    host_name = Column(String)
    locode = Column(String)

    def __init__(self, args: dict[str, any]):
        self.file_name = args["file_name"]
        self.file_time = args["file_time"]
        self.file_type = args["file_type"]
        self.load_time = datetime.now()
        self.obs_quantity = args["obs_quantity"]
        self.host_name = args["host_name"]
        self.locode = args["locode"]

    def __repr__(self):
        return f"load_log({self.file_name} {self.file_time} {self.host_name})"


class PolarisObservation(Base):
    __tablename__ = "polaris_observation"

    id = Column(Integer, primary_key=True)
    imo_code = Column(String)
    obs_time = Column(DateTime)
    locode = Column(String)
    arrival = Column(DateTime)
    departure = Column(DateTime)
    in_port = Column(Boolean)

    def __init__(self, args: dict[str, any]):
        self.imo_code = args["imo_code"]
        self.imo_code = args["imo_code"]
        self.obs_time = args["obs_time"]
        self.locode = args["locode"]
        self.arrival = args["arrival"]
        self.departure = args["departure"]
        self.in_port = args["in_port"]


class PolarisPort(Base):
    __tablename__ = "polaris_port"

    id = Column(Integer, primary_key=True)
    locode = Column(String)
    name = Column(String)
    scrape_flag = Column(Boolean)
    url = Column(String)

    def __init__(self, args: dict[str, any]):
        self.locode = args["code"]
        self.name = args["name"]
        self.scrape_flag = args["scrape_flag"]
        self.url = args["url"]


class PolarisVessel(Base):
    __tablename__ = "polaris_vessel"

    id = Column(Integer, primary_key=True)
    ais_type = Column(String)
    beam = Column(Integer)
    built_year = Column(Integer)
    callsign = Column(String)
    gross_ton = Column(Integer)
    hot_flag = Column(Boolean)
    imo_code = Column(String)
    length = Column(Integer)
    mmsi_code = Column(String)
    url = Column(String)
    vessel_flag = Column(String)
    vessel_name = Column(String)
    vessel_type = Column(String)

    def __init__(self, args: dict[str, any]):
        self.ais_type = args["ais_type"]
        self.beam = args["beam"]
        self.built_year = args["built_year"]
        self.callsign = args["callsign"]
        self.gross_ton = args["gross_ton"]
        self.hot_flag = False
        self.imo_code = args["imo_code"]
        self.length = args["length"]
        self.mmsi_code = args["mmsi_code"]
        self.url = args["url"]
        self.vessel_flag = args["vessel_flag"]
        self.vessel_name = args["vessel_name"]
        self.vessel_type = "Unknown"

    def __repr__(self):
        return f"PolarisVessel({self.vessel_name} {self.imo_code} {self.vessel_type})"

class PolarisVisit(Base):
    __tablename__ = "polaris_visit"

    id = Column(Integer, primary_key=True)
    active_flag = Column(Boolean)
    date_arrival = Column(Date)
    date_departure = Column(Date)
    imo_code = Column(String)
    in_port = Column(Boolean)
    locode_current = Column(String)
    locode_destination = Column(String)
    locode_last = Column(String)

    def __init__(self, args: dict[str, any]):
        self.active_flag = args.get("active_flag", True)
        self.date_arrival = args["date_arrival"]
        self.date_departure = args["date_departure"]
        self.imo_code = args["imo_code"]
        self.in_port = args["in_port"]
        self.locode_current = args["locode_current"]
        self.locode_destination = args["locode_destination"]
        self.locode_last = args["locode_last"]

    def __repr__(self):
        return f"PolarisVisit({self.imo_code} {self.date_arrival} {self.date_departure})"

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
