# salty-polaris

Scrape ships currently in port from [VesselFinder](https://www.vesselfinder.com) port pages.

## Installation

```bash
pip install -r requirements.txt
pip install -e .
```

## Usage

### Command line

```bash
# Scrape the default port (USBNC001 – Beaufort, NC)
python -m salty_polaris

# Scrape a specific port
python -m salty_polaris USLAX001

# Output results as JSON
python -m salty_polaris USBNC001 --json

# Enable verbose logging
python -m salty_polaris USBNC001 --verbose
```

### Python API

```python
from salty_polaris import VesselFinderScraper

scraper = VesselFinderScraper("USBNC001")
vessels = scraper.scrape()

for v in vessels:
    print(v.name, v.vessel_type, v.flag, v.arrival)
```

`VesselRecord` fields:

| Field | Description |
|-------|-------------|
| `name` | Vessel name |
| `vessel_url` | Full URL to the vessel page on VesselFinder |
| `vessel_type` | Ship type (e.g. Bulk Carrier, Container Ship) |
| `flag` | Flag state (ISO 2-letter country code) |
| `length` | Length overall (LOA) |
| `arrival` | Arrival timestamp |
| `departure` | Expected departure timestamp |

## Development

```bash
pip install -r requirements-dev.txt
pytest
```

## Port codes

VesselFinder uses UN/LOCODE format port codes, e.g.:

| Code | Port |
|------|------|
| `USBNC001` | Beaufort, NC, USA |
| `USLAX001` | Los Angeles, CA, USA |
| `USNYC001` | New York, NY, USA |
