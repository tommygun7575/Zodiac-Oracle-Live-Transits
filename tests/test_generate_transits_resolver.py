import unittest
from datetime import datetime
from unittest.mock import patch, call

from scripts import generate_transits

# Convenience: 7 identical tuples used to represent a complete 7-day batch from a source
_JPL_7 = [(10.5, 1.2)] * 7
_MIRIADE_7 = [(20.5, -0.2)] * 7


class ResolveBodyOrderTests(unittest.TestCase):
    def setUp(self):
        self.start_date = datetime(2026, 3, 8)

    @patch("scripts.generate_transits.fetch_swiss")
    @patch("scripts.generate_transits.fetch_miriade")
    @patch("scripts.generate_transits.fetch_jpl")
    def test_uses_jpl_first_with_mapped_id(self, fetch_jpl, fetch_miriade, fetch_swiss):
        """When JPL fills all 7 days, Miriade and Swiss are never called."""
        fetch_jpl.return_value = _JPL_7

        result = generate_transits.resolve_body("Mercury", self.start_date)

        fetch_jpl.assert_called_once_with("199", "2026-03-08", "2026-03-14")
        fetch_miriade.assert_not_called()
        fetch_swiss.assert_not_called()
        self.assertEqual(result, [{"lon": 10.5, "lat": 1.2, "source": "JPL"}] * 7)

    @patch("scripts.generate_transits.fetch_swiss")
    @patch("scripts.generate_transits.fetch_miriade")
    @patch("scripts.generate_transits.fetch_jpl")
    def test_falls_back_to_miriade_after_jpl_failure(self, fetch_jpl, fetch_miriade, fetch_swiss):
        """When JPL raises, Miriade is used for all 7 days; Swiss is never called."""
        fetch_jpl.side_effect = RuntimeError("jpl down")
        fetch_miriade.return_value = _MIRIADE_7

        result = generate_transits.resolve_body("Mercury", self.start_date)

        fetch_jpl.assert_called_once_with("199", "2026-03-08", "2026-03-14")
        fetch_miriade.assert_called_once_with("Mercury", self.start_date)
        fetch_swiss.assert_not_called()
        self.assertEqual(result, [{"lon": 20.5, "lat": -0.2, "source": "Miriade"}] * 7)

    @patch("scripts.generate_transits.fetch_swiss")
    @patch("scripts.generate_transits.fetch_miriade")
    @patch("scripts.generate_transits.fetch_jpl")
    def test_falls_back_to_swiss_after_jpl_and_miriade_failure(self, fetch_jpl, fetch_miriade, fetch_swiss):
        """When both JPL and Miriade fail, Swiss is called once per day (7 times)."""
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
    def test_body_without_jpl_id_skips_jpl_falls_back_to_miriade(self, fetch_jpl, fetch_miriade, fetch_swiss):
        """Bodies with no JPL ID skip JPL entirely and go straight to Miriade."""
        fetch_miriade.return_value = [(5.0, 0.5)] * 7

        result = generate_transits.resolve_body("UnknownBody", self.start_date)

        fetch_jpl.assert_not_called()
        fetch_miriade.assert_called_once_with("UnknownBody", self.start_date)
        fetch_swiss.assert_not_called()
        self.assertEqual(len(result), 7)
        self.assertTrue(all(entry["source"] == "Miriade" for entry in result))

    @patch("scripts.generate_transits.fetch_swiss")
    @patch("scripts.generate_transits.fetch_miriade")
    @patch("scripts.generate_transits.fetch_jpl")
    def test_body_without_jpl_id_falls_back_to_swiss_when_miriade_fails(self, fetch_jpl, fetch_miriade, fetch_swiss):
        """Bodies with no JPL ID that also fail in Miriade are resolved via Swiss."""
        fetch_miriade.side_effect = RuntimeError("miriade down")
        fetch_swiss.return_value = (7.0, 0.7)

        result = generate_transits.resolve_body("UnknownBody", self.start_date)

        fetch_jpl.assert_not_called()
        fetch_miriade.assert_called_once_with("UnknownBody", self.start_date)
        self.assertEqual(fetch_swiss.call_count, 7)
        self.assertTrue(all(entry["source"] == "Swiss" for entry in result))

    @patch("scripts.generate_transits.fetch_swiss")
    @patch("scripts.generate_transits.fetch_miriade")
    @patch("scripts.generate_transits.fetch_jpl")
    def test_body_without_jpl_id_returns_nulls_when_all_sources_fail(self, fetch_jpl, fetch_miriade, fetch_swiss):
        """When no source can resolve a body, result is 7 null entries — no exception raised."""
        fetch_miriade.side_effect = RuntimeError("miriade down")
        fetch_swiss.side_effect = RuntimeError("swiss down")

        result = generate_transits.resolve_body("UnknownBody", self.start_date)

        fetch_jpl.assert_not_called()
        self.assertEqual(len(result), 7)
        self.assertTrue(all(entry["lon"] is None for entry in result))
        self.assertTrue(all(entry["source"] == "none" for entry in result))

    @patch("scripts.generate_transits.fetch_swiss")
    @patch("scripts.generate_transits.fetch_miriade")
    @patch("scripts.generate_transits.fetch_jpl")
    def test_per_day_gap_filling_jpl_partial_miriade_fills_gaps(self, fetch_jpl, fetch_miriade, fetch_swiss):
        """When JPL provides only some days, Miriade fills the missing ones."""
        # JPL provides days 0-2 only
        fetch_jpl.return_value = [(10.0, 0.1), (11.0, 0.2), (12.0, 0.3)]
        # Miriade provides data for days 3-6 (days 0-2 will be skipped since JPL filled them)
        fetch_miriade.return_value = [
            (None, None), (None, None), (None, None),
            (20.0, 0.4), (21.0, 0.5), (22.0, 0.6), (23.0, 0.7),
        ]
        fetch_swiss.side_effect = RuntimeError("should not reach Swiss")

        result = generate_transits.resolve_body("Mercury", self.start_date)

        fetch_miriade.assert_called_once_with("Mercury", self.start_date)
        self.assertEqual(result[0], {"lon": 10.0, "lat": 0.1, "source": "JPL"})
        self.assertEqual(result[1], {"lon": 11.0, "lat": 0.2, "source": "JPL"})
        self.assertEqual(result[2], {"lon": 12.0, "lat": 0.3, "source": "JPL"})
        self.assertEqual(result[3], {"lon": 20.0, "lat": 0.4, "source": "Miriade"})
        self.assertEqual(result[4], {"lon": 21.0, "lat": 0.5, "source": "Miriade"})
        self.assertEqual(result[5], {"lon": 22.0, "lat": 0.6, "source": "Miriade"})
        self.assertEqual(result[6], {"lon": 23.0, "lat": 0.7, "source": "Miriade"})

    @patch("scripts.generate_transits.fetch_swiss")
    @patch("scripts.generate_transits.fetch_miriade")
    @patch("scripts.generate_transits.fetch_jpl")
    def test_per_day_gap_filling_miriade_partial_swiss_fills_remainder(self, fetch_jpl, fetch_miriade, fetch_swiss):
        """When JPL fails and Miriade provides only some days, Swiss fills the rest."""
        fetch_jpl.side_effect = RuntimeError("jpl down")
        # Miriade provides days 0-1; days 2-6 are null
        fetch_miriade.return_value = [
            (20.0, 0.4), (21.0, 0.5),
            (None, None), (None, None), (None, None), (None, None), (None, None),
        ]
        fetch_swiss.return_value = (42.0, 0.42)

        result = generate_transits.resolve_body("Mercury", self.start_date)

        self.assertEqual(result[0], {"lon": 20.0, "lat": 0.4, "source": "Miriade"})
        self.assertEqual(result[1], {"lon": 21.0, "lat": 0.5, "source": "Miriade"})
        for i in range(2, 7):
            self.assertEqual(result[i], {"lon": 42.0, "lat": 0.42, "source": "Swiss"})
        # Swiss called only for the 5 days Miriade left null
        self.assertEqual(fetch_swiss.call_count, 5)

    @patch("scripts.generate_transits.fetch_swiss")
    @patch("scripts.generate_transits.fetch_miriade")
    @patch("scripts.generate_transits.fetch_jpl")
    def test_small_body_jpl_id_uses_semicolon(self, fetch_jpl, fetch_miriade, fetch_swiss):
        """Ceres (asteroid #1) must be requested with id '1;' so JPL resolves it
        as an MPC small body rather than the Mercury system barycenter (NAIF id 1)."""
        fetch_jpl.return_value = [(10.0, 0.5)] * 7

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
