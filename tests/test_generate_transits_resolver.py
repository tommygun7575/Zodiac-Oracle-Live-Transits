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

    @patch("scripts.generate_transits.fetch_swiss")
    @patch("scripts.generate_transits.fetch_miriade")
    @patch("scripts.generate_transits.fetch_jpl")
    def test_small_body_jpl_id_uses_semicolon(self, fetch_jpl, fetch_miriade, fetch_swiss):
        """Ceres (asteroid #1) must be requested with id '1;' so JPL resolves it
        as an MPC small body rather than the Mercury system barycenter (NAIF id 1)."""
        fetch_jpl.return_value = [(10.0, 0.5)]

        generate_transits.resolve_body("Ceres", self.start_date)
        fetch_jpl.assert_called_once_with("1;", "2026-03-08", "2026-03-14")

    def test_jpl_ids_for_all_small_bodies_use_semicolons(self):
        """Verify every small body in BODIES uses a semicolon-suffixed ID so JPL
        resolves them as MPC catalog entries rather than planet-system barycenters."""
        small_bodies = {
            "Ceres": "1;",
            "Pallas": "2;",
            "Juno": "3;",
            "Vesta": "4;",
            "Eris": "136199;",
            "Sedna": "90377;",
            "Orcus": "90482;",
            "Makemake": "136472;",
            "Haumea": "136108;",
            "Quaoar": "50000;",
            "Ixion": "28978;",
        }
        for body, expected_id in small_bodies.items():
            self.assertEqual(
                generate_transits.BODIES[body],
                expected_id,
                msg=f"{body} should have JPL id '{expected_id}', got '{generate_transits.BODIES[body]}'",
            )


if __name__ == "__main__":
    unittest.main()
