import sys
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time

def extract_vessel_details(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.vesselfinder.com/",
        "Connection": "keep-alive",
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    def get_text_by_label(label):
        el = soup.find(lambda tag: tag.name in ["td", "th"] and label.lower() in tag.get_text(strip=True).lower())
        if el and el.find_next_sibling("td"):
            return el.find_next_sibling("td").get_text(strip=True)
        return None

    # Vessel name (from page title or h1)
    name = None
    h1 = soup.find("h1")
    if h1:
        name = h1.get_text(strip=True)
    if not name:
        name = soup.title.get_text(strip=True).split("|")[0].strip() if soup.title else None

    # Main details
    # Handle case where IMO/MMSI are on the same row, e.g. "9759886 / 369040000"
    imo = None
    mmsi = None
    # Try to get both from a combined row first
    imo_mmsi = get_text_by_label("IMO / MMSI")
    if imo_mmsi and "/" in imo_mmsi:
        parts = [x.strip() for x in imo_mmsi.split("/", 1)]
        if len(parts) == 2:
            imo, mmsi = parts
    if not imo:
        imo = get_text_by_label("IMO")
    if not mmsi:
        mmsi = get_text_by_label("MMSI")
    callsign = get_text_by_label("Callsign")
    flag = get_text_by_label("Flag")
    ais_type = get_text_by_label("AIS Type") or get_text_by_label("Type")


    # Last/Next port info (look for specific HTML structure)
    last_port_name = None
    last_port_departure = None
    next_port_name = None
    next_port_arrival = None

    # Find Last Port block
    last_port_label = soup.find("div", class_="vilabel", string=lambda s: s and "last port" in s.lower())
    if last_port_label:
        # The next <a> is the port name
        port_a = last_port_label.find_next("a")
        if port_a:
            last_port_name = port_a.get_text(strip=True)
        # The next <div class="_value"> is the departure date
        value_div = last_port_label.find_next("div", class_="_value")
        if value_div:
            # Look for "ATD: ..." in the text
            text = value_div.get_text(" ", strip=True)
            if "ATD:" in text:
                last_port_departure = text.split("ATD:", 1)[1].split("(")[0].strip()

    # Try to find next port info in a similar way (if present)
    next_port_label = soup.find("div", class_="vilabel", string=lambda s: s and "next port" in s.lower())
    if next_port_label:
        port_a = next_port_label.find_next("a")
        if port_a:
            next_port_name = port_a.get_text(strip=True)
        value_div = next_port_label.find_next("div", class_="_value")
        if value_div:
            text = value_div.get_text(" ", strip=True)
            if "ETA:" in text:
                next_port_arrival = text.split("ETA:", 1)[1].split("(")[0].strip()

    return {
        "name": name,
        "imo": imo,
        "mmsi": mmsi,
        "callsign": callsign,
        "flag": flag,
        "ais_type": ais_type,
        "last_port_name": last_port_name,
        "last_port_departure": last_port_departure,
        "next_port_name": next_port_name,
        "next_port_arrival": next_port_arrival,
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: python vessels.py <vessel-details-url>")
        sys.exit(1)
    url = sys.argv[1]
    details = extract_vessel_details(url)
    timestamp = int(time.time())
    parsed = urlparse(url)
    imo = details.get("imo") or "unknown"
    # Remove spaces and slashes from output filename (replace with underscores)
    safe_imo = str(imo).replace(" ", "_").replace("/", "_")
    out_path = f"/tmp/vessel_{safe_imo}_{timestamp}.json"
    with open(out_path, "w") as f:
        json.dump(details, f, indent=2)
    print(f"Wrote vessel details to {out_path}")

if __name__ == "__main__":
    main()
