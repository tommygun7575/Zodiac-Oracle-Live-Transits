import unittest
from datetime import datetime
from unittest.mock import patch

from scripts import generate_transits


class ResolveBodyOrderTests(unittest.TestCase):
    def setUp(self):
        self.start_date = datetime(2026, 3, 8)

    @patch("scripts.generate_transits.fetch_swiss")
    @patch("scripts.generate_transits.fetch_miriade")
    @patch("scripts.generate_transits.fetch_jpl")
    def test_uses_jpl_first_with_mapped_id(self, fetch_jpl, fetch_miriade, fetch_swiss):
        fetch_jpl.return_value = [(10.5, 1.2)]

        result = generate_transits.resolve_body("Mercury", self.start_date)

        fetch_jpl.assert_called_once_with("199", "2026-03-08", "2026-03-14")
        fetch_miriade.assert_not_called()
        fetch_swiss.assert_not_called()
        self.assertEqual(result, [{"lon": 10.5, "lat": 1.2, "source": "JPL"}])

    @patch("scripts.generate_transits.fetch_swiss")
    @patch("scripts.generate_transits.fetch_miriade")
    @patch("scripts.generate_transits.fetch_jpl")
    def test_falls_back_to_miriade_after_jpl_failure(self, fetch_jpl, fetch_miriade, fetch_swiss):
        fetch_jpl.side_effect = RuntimeError("jpl down")
        fetch_miriade.return_value = [(20.5, -0.2)]

        result = generate_transits.resolve_body("Mercury", self.start_date)

        fetch_jpl.assert_called_once_with("199", "2026-03-08", "2026-03-14")
        fetch_miriade.assert_called_once_with("Mercury", self.start_date)
        fetch_swiss.assert_not_called()
        self.assertEqual(result, [{"lon": 20.5, "lat": -0.2, "source": "Miriade"}])

    @patch("scripts.generate_transits.fetch_swiss")
    @patch("scripts.generate_transits.fetch_miriade")
    @patch("scripts.generate_transits.fetch_jpl")
    def test_falls_back_to_swiss_after_jpl_and_miriade_failure(self, fetch_jpl, fetch_miriade, fetch_swiss):
        fetch_jpl.side_effect = RuntimeError("jpl down")
        fetch_miriade.side_effect = RuntimeError("miriade down")
        fetch_swiss.return_value = (42.0, 0.42)

        result = generate_transits.resolve_body("Mercury", self.start_date)

        self.assertEqual(fetch_swiss.call_count, 7)
        self.assertTrue(all(entry["source"] == "Swiss" for entry in result))
        self.assertEqual(len(result), 7)
        self.assertTrue(all(entry["lon"] == 42.0 and entry["lat"] == 0.42 for entry in result))

    @patch("scripts.generate_transits.fetch_swiss")
    @patch("scripts.generate_transits.fetch_miriade")
    @patch("scripts.generate_transits.fetch_jpl")
    def test_raises_for_body_without_jpl_mapping(self, fetch_jpl, fetch_miriade, fetch_swiss):
        with self.assertRaisesRegex(RuntimeError, "No JPL body id configured for UnknownBody"):
            generate_transits.resolve_body("UnknownBody", self.start_date)

        fetch_jpl.assert_not_called()
        fetch_miriade.assert_not_called()
        fetch_swiss.assert_not_called()


if __name__ == "__main__":
    unittest.main()
