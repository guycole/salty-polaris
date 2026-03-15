"""Command-line entry point for salty-polaris."""

import argparse
import json
import logging
import sys
from dataclasses import asdict

import requests

from salty_polaris.scraper import DEFAULT_PORT_CODE, VesselFinderScraper


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Scrape ships in port from VesselFinder."
    )
    parser.add_argument(
        "port_code",
        nargs="?",
        default=DEFAULT_PORT_CODE,
        help=f"VesselFinder port LOCODE (default: {DEFAULT_PORT_CODE})",
    )
    parser.add_argument(
        "--json",
        dest="output_json",
        action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    scraper = VesselFinderScraper(args.port_code)
    try:
        vessels = scraper.scrape()
    except requests.Timeout:
        logging.error("Request timed out while fetching %s", scraper.url)
        sys.exit(1)
    except requests.ConnectionError as exc:
        logging.error("Network error while fetching %s: %s", scraper.url, exc)
        sys.exit(1)
    except requests.HTTPError as exc:
        logging.error("HTTP error from %s: %s", scraper.url, exc)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        logging.error("Unexpected error during scrape: %s", exc)
        sys.exit(1)

    if args.output_json:
        print(json.dumps([asdict(v) for v in vessels], indent=2))
    else:
        if not vessels:
            print(f"No vessels found in port {args.port_code}.")
        else:
            print(f"Vessels in port {args.port_code} ({len(vessels)} found):\n")
            header = f"{'VESSEL':<40} {'TYPE':<20} {'FLAG':<6} {'LOA':<6} {'ARRIVED':<20} {'DEPARTS':<20}"
            print(header)
            print("-" * len(header))
            for v in vessels:
                print(
                    f"{v.name:<40} "
                    f"{(v.vessel_type or ''):<20} "
                    f"{(v.flag or ''):<6} "
                    f"{(v.length or ''):<6} "
                    f"{(v.arrival or ''):<20} "
                    f"{(v.departure or ''):<20}"
                )

    return 0


if __name__ == "__main__":
    sys.exit(main())
