import unittest
from unittest.mock import patch, Mock

from scripts.bodies.miriade_client import fetch_miriade


class MiriadeClientTests(unittest.TestCase):
    @patch("scripts.bodies.miriade_client.requests.get")
    def test_fetch_miriade_returns_ra_as_lon(self, mock_get):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"data": [{"RA": "210.125"}]}
        mock_get.return_value = response

        result = fetch_miriade("Ceres")

        self.assertEqual({"lon": 210.125}, result)

    @patch("scripts.bodies.miriade_client.requests.get")
    def test_fetch_miriade_raises_for_non_200(self, mock_get):
        response = Mock()
        response.status_code = 500
        mock_get.return_value = response

        with self.assertRaisesRegex(RuntimeError, "Miriade request failed"):
            fetch_miriade("Ceres")


if __name__ == "__main__":
    unittest.main()
