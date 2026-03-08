from datetime import datetime
from unittest import TestCase
from unittest.mock import patch

from scripts import generate_transits


class _MockResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code

    def json(self):
        return self._data


class GenerateTransitsTests(TestCase):
    @patch("scripts.generate_transits.requests.get")
    def test_fetch_miriade_supports_ephemerides_format(self, mock_get):
        mock_get.return_value = _MockResponse(
            {"ephemerides": [{"lambda": "10.5", "beta": "-1.2"}]}
        )

        lon, lat = generate_transits.fetch_miriade("Mars", "2026-03-08")

        self.assertEqual(lon, 10.5)
        self.assertEqual(lat, -1.2)

    @patch("scripts.generate_transits.requests.get")
    def test_fetch_miriade_supports_data_format(self, mock_get):
        mock_get.return_value = _MockResponse(
            {"data": [{"EclLon": "220.25", "EclLat": "1.75"}]}
        )

        lon, lat = generate_transits.fetch_miriade("Mars", "2026-03-08")

        self.assertEqual(lon, 220.25)
        self.assertEqual(lat, 1.75)

    @patch("scripts.generate_transits.fetch_swiss", side_effect=RuntimeError("no swiss"))
    @patch("scripts.generate_transits.fetch_miriade", side_effect=RuntimeError("no miriade"))
    @patch("scripts.generate_transits.fetch_jpl", side_effect=RuntimeError("no jpl"))
    def test_resolve_body_returns_unavailable_when_all_sources_fail(
        self, _mock_jpl, _mock_miriade, _mock_swiss
    ):
        rows = generate_transits.resolve_body("Ceres", datetime(2026, 3, 8))

        self.assertEqual(len(rows), 7)
        self.assertTrue(all(row["source"] == "Unavailable" for row in rows))
        self.assertTrue(all(row["lon"] is None and row["lat"] is None for row in rows))
