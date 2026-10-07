import unittest
from unittest.mock import patch, Mock

from scripts.bodies.horizons_client import fetch_horizons, fetch_jpl


class HorizonsClientTests(unittest.TestCase):
    @patch("scripts.bodies.horizons_client.requests.get")
    def test_fetch_jpl_requests_observer_q31_and_parses_lon_lat(self, mock_get):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "result": (
                " Date__(UT)__HR:MN, , ,    ObsEcLon,   ObsEcLat,\n"
                "$$SOE\n"
                " 2026-Oct-07 12:00, , , 218.7987123, -2.4681873,\n"
                " 2026-Oct-07 18:00, , , 219.0886256, -2.4930656,\n"
                "$$EOE\n"
            )
        }
        mock_get.return_value = response

        rows = fetch_jpl("199", "2026-10-07T12:00:00Z", "2026-10-07T18:00:00Z", step_size="6h")

        self.assertEqual([(218.7987123, -2.4681873), (219.0886256, -2.4930656)], rows)
        params = mock_get.call_args.kwargs["params"]
        self.assertEqual("OBSERVER", params["EPHEM_TYPE"])
        self.assertEqual("31", params["QUANTITIES"])
        self.assertEqual("500@399", params["CENTER"])
        self.assertNotIn("REF_SYSTEM", params)

    @patch("scripts.bodies.horizons_client.requests.get")
    def test_fetch_horizons_parses_longitude_between_soe_and_eoe(self, mock_get):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "result": (
                "header\n Date__(UT)__HR:MN, , ,    ObsEcLon,   ObsEcLat,\n"
                "$$SOE\n 2026-Mar-08 00:00, , , 123.45, -1.25,\n$$EOE\nfooter"
            )
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
