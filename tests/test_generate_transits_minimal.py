import unittest
from unittest.mock import patch

from scripts import generate_transits


class GenerateTransitsMinimalTests(unittest.TestCase):
    @patch("scripts.generate_transits.fetch_mpc")
    @patch("scripts.generate_transits.fetch_miriade")
    @patch("scripts.generate_transits.fetch_horizons")
    def test_fetch_body_fallback_order(self, fetch_horizons, fetch_miriade, fetch_mpc):
        fetch_horizons.side_effect = RuntimeError("horizons down")
        fetch_miriade.return_value = {"lon": 123.0}

        result = generate_transits.fetch_body("Mars")

        self.assertEqual({"lon": 123.0}, result)
        fetch_horizons.assert_called_once_with("Mars")
        fetch_miriade.assert_called_once_with("Mars")
        fetch_mpc.assert_not_called()

    def test_zodiac_calculation(self):
        sign, degree = generate_transits.zodiac(95.5)
        self.assertEqual("Cancer", sign)
        self.assertEqual(5.5, degree)


if __name__ == "__main__":
    unittest.main()
