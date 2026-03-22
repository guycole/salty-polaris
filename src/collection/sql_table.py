#
# Title: sql_table.py
# Description: database table definitions
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import BigInteger, Boolean, Date, DateTime, Float, Integer, String

from sqlalchemy.orm import registry
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.declarative import declared_attr

mapper_registry = registry()


class Base(DeclarativeBase):
    pass

class LoadLog(Base):
    """load_log table definition"""

    __tablename__ = "heeler_load_log"

    id = Column(Integer, primary_key=True)
    file_name = Column(String)
    file_time = Column(DateTime)
    file_type = Column(String)
    load_time = Column(DateTime)
    obs_quantity = Column(Integer)
    platform = Column(String)

    def __init__(self, args: dict[str, any]):
        self.file_name = args["file_name"]
        self.file_time = args["file_time"]
        self.file_type = args["file_type"]
        self.load_time = datetime.now()
        self.obs_quantity = args["obs_quantity"]
        self.platform = args["platform"]

    def __repr__(self):
        return f"load_log({self.file_name} {self.file_time} {self.platform})"

class PolarisVessel(Base):
    __tablename__ = "polaris_vessel"

    id = Column(Integer, primary_key=True)
    ais_type = Column(String)
    beam = Column(Integer)
    built_year = Column(Integer)
    callsign = Column(String)
    gross_ton = Column(Integer)
    imo_code = Column(String)
    length = Column(Integer)
    mmsi_code = Column(String)
    scrape_flag = Column(Boolean)
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
        self.imo_code = args["imo_code"]
        self.length = args["length"]
        self.mmsi_code = args["mmsi_code"]
        self.scrape_flag = False
        self.url = args["url"]
        self.vessel_flag = args["vessel_flag"]
        self.vessel_name = args["vessel_name"]
        self.vessel_type = "Unknown"

    def __repr__(self):
        return f"PolarisVessel({self.vessel_name} {self.imo_code} {self.vessel_type})"


# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
