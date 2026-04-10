#
# Title: postgres.py
# Description: postgresql support
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
# import sqlalchemy
# from sqlalchemy import and_
# from sqlalchemy import select

import datetime
import time
from sql_table import PolarisLoadLog, PolarisObservation, PolarisPort

import sqlalchemy
from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy import select

from sql_table import (
    PolarisLoadLog,
    PolarisObservation,
    PolarisPort,
    PolarisVessel,
    PolarisVisit
)

class PostGres:
    db_engine = None
    Session = None

    def __init__(self, session: sqlalchemy.orm.session.sessionmaker):
        self.Session = session

    def load_log_insert(self, args: dict[str, any]) -> PolarisLoadLog:
        candidate = PolarisLoadLog(args)

        try:
            with self.Session() as session:
                session.add(candidate)
                session.commit()
        except Exception as error:
            print(error)

        return candidate

    def load_log_select_all(self) -> list[PolarisLoadLog]:
        with self.Session() as session:
            return session.scalars(select(PolarisLoadLog)).all()

    def load_log_select_all_by_date(
        self, target: datetime.date
    ) -> list[PolarisLoadLog]:
        with self.Session() as session:
            return session.scalars(
                select(PolarisLoadLog).filter(
                    func.date(PolarisLoadLog.file_time) == target
                )
            ).all()

    def load_log_select_by_file_name(self, file_name: str) -> PolarisLoadLog:
        with self.Session() as session:
            return session.scalars(
                select(PolarisLoadLog).filter_by(file_name=file_name)
            ).first()

    def observation_insert(self, args: dict[str, any]) -> PolarisObservation:
        candidate = PolarisObservation(args)

        try:
            with self.Session() as session:
                session.add(candidate)
                session.commit()
        except Exception as error:
            print(error)

        return candidate

    def port_select_for_scrape(self) -> list[str]:
        """
        Select all URLs from polaris_port table where scrape_flag is true.
        Returns a list of URLs.
        """
        with self.Session() as session:
            return [
                row.url
                for row in session.scalars(
                    select(PolarisPort).filter_by(scrape_flag=True)
                ).all()
            ]

    def vessel_insert(self, args: dict[str, any]) -> PolarisVessel:
        candidate = PolarisVessel(args)

        try:
            with self.Session() as session:
                session.add(candidate)
                session.commit()
        except Exception as error:
            print(error)

        return candidate

    def vessel_insert_or_update(self, args: dict[str, any]) -> PolarisVessel:
        try:
            print(f"Session class: {self.Session}")
            print(f"DB engine: {self.db_engine}")

            print("xxxxxxxxxxxxxx")
            print(args["observation"]["imo"])
            if args["observation"]["imo"] is None:
                print("IMO code is None, cannot insert or update vessel")
                return None

            with self.Session() as session:
                print(f"Session instance: {session}")
                obs = args["observation"]
                print(f"Observation: {obs}")
                existing = session.scalars(
                    select(PolarisVessel).filter(PolarisVessel.imo_code == obs["imo"])
                ).first()

                if existing is None:
                    print("creating new vessel")
                    candidate = PolarisVessel(
                        {
                            "ais_type": obs["aisType"],
                            "beam": obs["beam"],
                            "built_year": obs["built"],
                            "callsign": obs["callsign"],
                            "gross_ton": obs["grossTon"],
                            "imo_code": obs["imo"],
                            "length": obs["length"],
                            "mmsi_code": obs["mmsi"],
                            "url": obs["vesselUrl"],
                            "vessel_flag": obs["flag"],
                            "vessel_name": obs["name"],
                        }
                    )
                    session.add(candidate)
                else:
                    print("updating existing vessel")
                    existing.ais_type = obs["aisType"]
                    existing.beam = obs["beam"]
                    existing.built_year = obs["built"]
                    existing.callsign = obs["callsign"]
                    existing.gross_ton = obs["grossTon"]
                    existing.length = obs["length"]
                    existing.mmsi_code = obs["mmsi"]
                    existing.url = obs["vesselUrl"]
                    existing.vessel_flag = obs["flag"]
                    existing.vessel_name = obs["name"]

                print("commit")
                session.commit()
                print("commit successful")
                # Return the up-to-date vessel from the DB
                vessel = session.scalars(
                    select(PolarisVessel).filter(
                        PolarisVessel.imo_code == obs["imo_code"]
                    )
                ).first()
                print(f"Returned vessel: {vessel}")
                return vessel
        except Exception as error:
            print(f"Exception in vessel_insert_or_update: {error}")
            return None

    def vessel_insert(self, args: dict[str, any]) -> PolarisVessel:
        candidate = PolarisVessel(args)

        try:
            with self.Session() as session:
                session.add(candidate)
                session.commit()
        except Exception as error:
            print(error)

        return candidate

    def vessel_select_by_imo(self, imo_code: str) -> PolarisVessel:
        with self.Session() as session:
            return session.scalars(
                select(PolarisVessel).filter_by(imo_code=imo_code)
            ).first()

    def visit_insert(self, args: dict[str, any]) -> PolarisVisit:
        args["active_flag"] = True
        candidate = PolarisVisit(args)

        try:
            with self.Session() as session:
                session.add(candidate)
                session.commit()
        except Exception as error:
            print(error)

        return candidate
    
    def visit_update_departure(self, args: dict[str, any]) -> None:
        try:
            with self.Session() as session:
                visit = session.scalars(
                    select(PolarisVisit).filter_by(imo_code=args["imo_code"], active_flag=True)
                ).first()
                if visit:
                    visit.date_departure = args['date_departure']
                    visit.duration_days = args['duration_days']
                    visit.in_port = False
                    visit.locode_destination = args['locode_destination']
                    visit.active_flag = False
                    session.commit()
                    print(f"Updated departure for IMO {args['imo_code']}")
                else:
                    print(f"No active visit found for IMO {args['imo_code']} to update departure.")
        except Exception as error:
            print(f"Error updating departure: {error}")

    def visit_select_by_imo_and_active(self, imo_code: str) -> list[PolarisVisit]:
        with self.Session() as session:
            return session.scalars(
                select(PolarisVisit).filter_by(imo_code=imo_code, active_flag=True)
            ).all()

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
