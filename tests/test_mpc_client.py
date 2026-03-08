import unittest
from unittest.mock import Mock, patch

from scripts.bodies.mpc_client import fetch_mpc


class MPCClientTests(unittest.TestCase):
    @patch("scripts.bodies.mpc_client.requests.get")
    def test_fetch_mpc_returns_node_as_lon(self, mock_get):
        response = Mock()
        response.status_code = 200
        response.json.return_value = [{"node": "123.45"}]
        mock_get.return_value = response

        result = fetch_mpc("Ceres")

        self.assertEqual({"lon": 123.45}, result)

    @patch("scripts.bodies.mpc_client.requests.get")
    def test_fetch_mpc_raises_for_non_200(self, mock_get):
        response = Mock()
        response.status_code = 503
        mock_get.return_value = response

        with self.assertRaisesRegex(RuntimeError, "MPC request failed"):
            fetch_mpc("Ceres")

    @patch("scripts.bodies.mpc_client.requests.get")
    def test_fetch_mpc_raises_for_empty_response(self, mock_get):
        response = Mock()
        response.status_code = 200
        response.json.return_value = []
        mock_get.return_value = response

        with self.assertRaisesRegex(RuntimeError, "Empty MPC response"):
            fetch_mpc("Ceres")


if __name__ == "__main__":
    unittest.main()
