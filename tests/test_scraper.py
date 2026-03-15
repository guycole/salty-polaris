"""Tests for salty_polaris.scraper."""

import pytest
import requests

from salty_polaris.scraper import (
    DEFAULT_PORT_CODE,
    VesselFinderScraper,
    VesselRecord,
    _parse_vessels,
)
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

SAMPLE_HTML_WITH_VESSELS = """
<!DOCTYPE html>
<html>
<head><title>Port of Beaufort - Vessels in Port</title></head>
<body>
  <h1>Vessels in Port - USBNC001</h1>
  <table class="ships-list">
    <thead>
      <tr>
        <th>VESSEL</th>
        <th>TYPE</th>
        <th>FLAG</th>
        <th>LOA</th>
        <th>ARRIVED</th>
        <th>DEPARTURE</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><a href="/vessels/SEA-PIONEER-123456789">SEA PIONEER</a></td>
        <td>Bulk Carrier</td>
        <td>US</td>
        <td>189m</td>
        <td>2024-03-10 08:30</td>
        <td>2024-03-15 12:00</td>
      </tr>
      <tr>
        <td><a href="/vessels/OCEAN-STAR-987654321">OCEAN STAR</a></td>
        <td>Container Ship</td>
        <td>MH</td>
        <td>225m</td>
        <td>2024-03-12 14:00</td>
        <td>2024-03-14 18:00</td>
      </tr>
      <tr>
        <td><a href="/vessels/CAPE-HATTERAS-111222333">CAPE HATTERAS</a></td>
        <td>General Cargo</td>
        <td>US</td>
        <td>95m</td>
        <td>2024-03-13 09:15</td>
        <td></td>
      </tr>
    </tbody>
  </table>
</body>
</html>
"""

SAMPLE_HTML_FALLBACK_TABLE = """
<!DOCTYPE html>
<html>
<body>
  <table>
    <tbody>
      <tr>
        <td><a href="/vessels/VESSEL-ONE-000000001">VESSEL ONE</a></td>
        <td>Tanker</td>
        <td>PA</td>
        <td>140m</td>
        <td>2024-03-11 07:00</td>
        <td>2024-03-16 10:00</td>
      </tr>
    </tbody>
  </table>
</body>
</html>
"""

SAMPLE_HTML_NO_TABLE = """
<!DOCTYPE html>
<html>
<body>
  <p>No vessels currently in port.</p>
</body>
</html>
"""

SAMPLE_HTML_EMPTY_TBODY = """
<!DOCTYPE html>
<html>
<body>
  <table class="ships-list">
    <thead>
      <tr><th>VESSEL</th><th>TYPE</th><th>FLAG</th></tr>
    </thead>
    <tbody></tbody>
  </table>
</body>
</html>
"""

SAMPLE_HTML_VESSEL_NO_URL = """
<!DOCTYPE html>
<html>
<body>
  <table class="ships-list">
    <tbody>
      <tr>
        <td>UNNAMED VESSEL</td>
        <td>Fishing</td>
        <td>US</td>
        <td>12m</td>
        <td>2024-03-14 06:00</td>
        <td></td>
      </tr>
    </tbody>
  </table>
</body>
</html>
"""


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


# ---------------------------------------------------------------------------
# VesselRecord tests
# ---------------------------------------------------------------------------


class TestVesselRecord:
    def test_required_field_only(self):
        v = VesselRecord(name="SEA PIONEER")
        assert v.name == "SEA PIONEER"
        assert v.vessel_url is None
        assert v.vessel_type is None
        assert v.flag is None
        assert v.length is None
        assert v.arrival is None
        assert v.departure is None

    def test_all_fields(self):
        v = VesselRecord(
            name="SEA PIONEER",
            vessel_url="https://www.vesselfinder.com/vessels/SEA-PIONEER-123456789",
            vessel_type="Bulk Carrier",
            flag="US",
            length="189m",
            arrival="2024-03-10 08:30",
            departure="2024-03-15 12:00",
        )
        assert v.name == "SEA PIONEER"
        assert v.vessel_type == "Bulk Carrier"
        assert v.flag == "US"
        assert v.length == "189m"
        assert v.arrival == "2024-03-10 08:30"
        assert v.departure == "2024-03-15 12:00"

    def test_repr(self):
        v = VesselRecord(name="SEA PIONEER", vessel_type="Bulk Carrier", flag="US", arrival="2024-03-10")
        assert "SEA PIONEER" in repr(v)
        assert "Bulk Carrier" in repr(v)


# ---------------------------------------------------------------------------
# _parse_vessels tests
# ---------------------------------------------------------------------------


class TestParseVessels:
    def test_parses_three_vessels(self):
        vessels = _parse_vessels(_soup(SAMPLE_HTML_WITH_VESSELS))
        assert len(vessels) == 3

    def test_first_vessel_name(self):
        vessels = _parse_vessels(_soup(SAMPLE_HTML_WITH_VESSELS))
        assert vessels[0].name == "SEA PIONEER"

    def test_first_vessel_url(self):
        vessels = _parse_vessels(_soup(SAMPLE_HTML_WITH_VESSELS))
        assert vessels[0].vessel_url == (
            "https://www.vesselfinder.com/vessels/SEA-PIONEER-123456789"
        )

    def test_first_vessel_type(self):
        vessels = _parse_vessels(_soup(SAMPLE_HTML_WITH_VESSELS))
        assert vessels[0].vessel_type == "Bulk Carrier"

    def test_first_vessel_flag(self):
        vessels = _parse_vessels(_soup(SAMPLE_HTML_WITH_VESSELS))
        assert vessels[0].flag == "US"

    def test_first_vessel_length(self):
        vessels = _parse_vessels(_soup(SAMPLE_HTML_WITH_VESSELS))
        assert vessels[0].length == "189m"

    def test_first_vessel_arrival(self):
        vessels = _parse_vessels(_soup(SAMPLE_HTML_WITH_VESSELS))
        assert vessels[0].arrival == "2024-03-10 08:30"

    def test_first_vessel_departure(self):
        vessels = _parse_vessels(_soup(SAMPLE_HTML_WITH_VESSELS))
        assert vessels[0].departure == "2024-03-15 12:00"

    def test_second_vessel_fields(self):
        vessels = _parse_vessels(_soup(SAMPLE_HTML_WITH_VESSELS))
        v = vessels[1]
        assert v.name == "OCEAN STAR"
        assert v.vessel_type == "Container Ship"
        assert v.flag == "MH"

    def test_third_vessel_empty_departure(self):
        vessels = _parse_vessels(_soup(SAMPLE_HTML_WITH_VESSELS))
        assert vessels[2].departure is None

    def test_fallback_table_no_class(self):
        vessels = _parse_vessels(_soup(SAMPLE_HTML_FALLBACK_TABLE))
        assert len(vessels) == 1
        assert vessels[0].name == "VESSEL ONE"
        assert vessels[0].vessel_type == "Tanker"

    def test_no_table_returns_empty_list(self):
        vessels = _parse_vessels(_soup(SAMPLE_HTML_NO_TABLE))
        assert vessels == []

    def test_empty_tbody_returns_empty_list(self):
        vessels = _parse_vessels(_soup(SAMPLE_HTML_EMPTY_TBODY))
        assert vessels == []

    def test_vessel_without_anchor(self):
        vessels = _parse_vessels(_soup(SAMPLE_HTML_VESSEL_NO_URL))
        assert len(vessels) == 1
        assert vessels[0].name == "UNNAMED VESSEL"
        assert vessels[0].vessel_url is None

    def test_vessel_url_is_absolute(self):
        vessels = _parse_vessels(_soup(SAMPLE_HTML_WITH_VESSELS))
        for v in vessels:
            assert v.vessel_url is not None
            assert v.vessel_url.startswith("https://")


# ---------------------------------------------------------------------------
# VesselFinderScraper tests
# ---------------------------------------------------------------------------


class TestVesselFinderScraper:
    def test_default_port_code(self):
        scraper = VesselFinderScraper()
        assert scraper.port_code == DEFAULT_PORT_CODE

    def test_custom_port_code(self):
        scraper = VesselFinderScraper("USLAX001")
        assert scraper.port_code == "USLAX001"

    def test_url_construction(self):
        scraper = VesselFinderScraper("USBNC001")
        assert scraper.url == "https://www.vesselfinder.com/ports/USBNC001"

    def test_custom_port_url(self):
        scraper = VesselFinderScraper("USLAX001")
        assert scraper.url == "https://www.vesselfinder.com/ports/USLAX001"

    def test_parse_delegates_to_parse_vessels(self):
        scraper = VesselFinderScraper()
        vessels = scraper.parse(SAMPLE_HTML_WITH_VESSELS)
        assert len(vessels) == 3
        assert vessels[0].name == "SEA PIONEER"

    def test_scrape_uses_fetch_and_parse(self, mocker):
        scraper = VesselFinderScraper("USBNC001")
        mocker.patch.object(scraper, "fetch", return_value=SAMPLE_HTML_WITH_VESSELS)
        vessels = scraper.scrape()
        assert len(vessels) == 3
        scraper.fetch.assert_called_once()

    def test_fetch_raises_on_http_error(self, mocker):
        scraper = VesselFinderScraper("USBNC001")
        mock_response = mocker.MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404")
        mocker.patch("requests.get", return_value=mock_response)
        with pytest.raises(requests.HTTPError):
            scraper.fetch()

    def test_fetch_sends_user_agent(self, mocker):
        scraper = VesselFinderScraper("USBNC001")
        mock_response = mocker.MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = SAMPLE_HTML_WITH_VESSELS
        mock_get = mocker.patch("requests.get", return_value=mock_response)
        scraper.fetch()
        call_kwargs = mock_get.call_args.kwargs
        headers_sent = call_kwargs.get("headers", {})
        assert "User-Agent" in headers_sent

    def test_custom_headers(self):
        custom = {"User-Agent": "TestBot/1.0"}
        scraper = VesselFinderScraper(headers=custom)
        assert scraper.headers == custom

    def test_custom_timeout(self):
        scraper = VesselFinderScraper(timeout=60)
        assert scraper.timeout == 60
