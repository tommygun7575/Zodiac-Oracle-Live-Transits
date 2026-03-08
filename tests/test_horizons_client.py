import unittest
from unittest.mock import patch, Mock

from scripts.bodies.horizons_client import fetch_horizons


class HorizonsClientTests(unittest.TestCase):
    @patch("scripts.bodies.horizons_client.requests.get")
    def test_fetch_horizons_parses_longitude_between_soe_and_eoe(self, mock_get):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "result": "header\n$$SOE\n2026-Mar-08,00:00,foo,bar,123.45,baz\n$$EOE\nfooter"
        }
        mock_get.return_value = response

        result = fetch_horizons("Mars")

        self.assertEqual({"lon": 123.45}, result)

    @patch("scripts.bodies.horizons_client.requests.get")
    def test_fetch_horizons_raises_for_malformed_response(self, mock_get):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {}
        mock_get.return_value = response

        with self.assertRaisesRegex(RuntimeError, "Malformed Horizons response"):
            fetch_horizons("Mars")

    @patch("scripts.bodies.horizons_client.requests.get")
    def test_fetch_horizons_raises_when_no_longitude_found(self, mock_get):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"result": "header\n$$SOE\n$$EOE\nfooter"}
        mock_get.return_value = response

        with self.assertRaisesRegex(RuntimeError, "No longitude found"):
            fetch_horizons("Mars")


if __name__ == "__main__":
    unittest.main()
