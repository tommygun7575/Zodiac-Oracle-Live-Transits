import unittest
from datetime import datetime
from unittest.mock import patch

from scripts import generate_transits

_N = generate_transits.SLOTS_PER_WEEK  # 28
_JPL_N = [(10.5, 1.2)] * _N
_MIRIADE_N = [(20.5, -0.2)] * _N


class ResolveBodyOrderTests(unittest.TestCase):
    def setUp(self):
        self.start_date = datetime(2026, 3, 8)
        self.snapshots = generate_transits.week_snapshot_datetimes(self.start_date)

    @patch("scripts.generate_transits.fetch_swiss")
    @patch("scripts.generate_transits.fetch_miriade")
    @patch("scripts.generate_transits.fetch_jpl")
    def test_uses_jpl_first_with_mapped_id(self, fetch_jpl, fetch_miriade, fetch_swiss):
        fetch_jpl.return_value = _JPL_N
        result = generate_transits.resolve_body("Mercury", self.start_date)
        self.assertEqual(fetch_jpl.call_count, 1)
        args, kwargs = fetch_jpl.call_args
        self.assertEqual(args[0], "199")
        step = kwargs.get("step_size") if kwargs else None
        if step is None and len(args) > 3:
            step = args[3]
        self.assertEqual(step, "6h")
        fetch_miriade.assert_not_called()
        fetch_swiss.assert_not_called()
        self.assertEqual(len(result), _N)
        self.assertTrue(all(e["source"] == "JPL" and e["lon"] == 10.5 for e in result))

    @patch("scripts.generate_transits.fetch_swiss")
    @patch("scripts.generate_transits.fetch_miriade")
    @patch("scripts.generate_transits.fetch_jpl")
    def test_falls_back_to_miriade_after_jpl_failure(self, fetch_jpl, fetch_miriade, fetch_swiss):
        fetch_jpl.side_effect = RuntimeError("jpl down")
        fetch_miriade.return_value = _MIRIADE_N
        result = generate_transits.resolve_body("Mercury", self.start_date)
        fetch_miriade.assert_called_once()
        fetch_swiss.assert_not_called()
        self.assertEqual(len(result), _N)
        self.assertTrue(all(e["source"] == "Miriade" for e in result))

    @patch("scripts.generate_transits.fetch_swiss")
    @patch("scripts.generate_transits.fetch_miriade")
    @patch("scripts.generate_transits.fetch_jpl")
    def test_falls_back_to_swiss_after_jpl_and_miriade_failure(self, fetch_jpl, fetch_miriade, fetch_swiss):
        fetch_jpl.side_effect = RuntimeError("jpl down")
        fetch_miriade.side_effect = RuntimeError("miriade down")
        fetch_swiss.return_value = (42.0, 0.42)
        result = generate_transits.resolve_body("Mercury", self.start_date)
        self.assertEqual(fetch_swiss.call_count, _N)
        self.assertEqual(len(result), _N)
        self.assertTrue(all(e["source"] == "Swiss" for e in result))

    @patch("scripts.generate_transits.fetch_swiss")
    @patch("scripts.generate_transits.fetch_miriade")
    @patch("scripts.generate_transits.fetch_jpl")
    def test_body_without_jpl_id_skips_jpl_falls_back_to_miriade(self, fetch_jpl, fetch_miriade, fetch_swiss):
        fetch_miriade.return_value = [(5.0, 0.5)] * _N
        result = generate_transits.resolve_body("UnknownBody", self.start_date)
        fetch_jpl.assert_not_called()
        fetch_miriade.assert_called_once()
        self.assertEqual(len(result), _N)
        self.assertTrue(all(e["source"] == "Miriade" for e in result))

    @patch("scripts.generate_transits.fetch_swiss")
    @patch("scripts.generate_transits.fetch_miriade")
    @patch("scripts.generate_transits.fetch_jpl")
    def test_body_without_jpl_id_falls_back_to_swiss_when_miriade_fails(self, fetch_jpl, fetch_miriade, fetch_swiss):
        fetch_miriade.side_effect = RuntimeError("miriade down")
        fetch_swiss.return_value = (7.0, 0.7)
        result = generate_transits.resolve_body("UnknownBody", self.start_date)
        fetch_jpl.assert_not_called()
        self.assertEqual(fetch_swiss.call_count, _N)
        self.assertTrue(all(e["source"] == "Swiss" for e in result))

    @patch("scripts.generate_transits.fetch_swiss")
    @patch("scripts.generate_transits.fetch_miriade")
    @patch("scripts.generate_transits.fetch_jpl")
    def test_body_without_jpl_id_returns_nulls_when_all_sources_fail(self, fetch_jpl, fetch_miriade, fetch_swiss):
        fetch_miriade.side_effect = RuntimeError("miriade down")
        fetch_swiss.side_effect = RuntimeError("swiss down")
        result = generate_transits.resolve_body("UnknownBody", self.start_date)
        self.assertEqual(len(result), _N)
        self.assertTrue(all(e["lon"] is None and e["source"] == "none" for e in result))

    @patch("scripts.generate_transits.fetch_swiss")
    @patch("scripts.generate_transits.fetch_miriade")
    @patch("scripts.generate_transits.fetch_jpl")
    def test_per_day_gap_filling_jpl_partial_miriade_fills_gaps(self, fetch_jpl, fetch_miriade, fetch_swiss):
        fetch_jpl.return_value = [(10.0, 0.1), (11.0, 0.2), (12.0, 0.3)]
        miriade = [(None, None)] * 3 + [(20.0 + i, 0.4) for i in range(_N - 3)]
        fetch_miriade.return_value = miriade
        result = generate_transits.resolve_body("Mercury", self.start_date)
        self.assertEqual(result[0]["source"], "JPL")
        self.assertEqual(result[3]["source"], "Miriade")
        self.assertEqual(len(result), _N)

    @patch("scripts.generate_transits.fetch_swiss")
    @patch("scripts.generate_transits.fetch_miriade")
    @patch("scripts.generate_transits.fetch_jpl")
    def test_small_body_jpl_id_uses_semicolon(self, fetch_jpl, fetch_miriade, fetch_swiss):
        fetch_jpl.return_value = [(10.0, 0.5)] * _N
        generate_transits.resolve_body("Ceres", self.start_date)
        self.assertEqual(fetch_jpl.call_args[0][0], "1;")

    def test_jpl_ids_for_all_small_bodies_use_semicolons(self):
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
            "Astraea": "5;",
            "Sappho": "80;",
            "Karma": "3811;",
            "Bacchus": "2063;",
            "Hygiea": "10;",
            "Nessus": "7066;",
            "Varuna": "20000;",
            "Typhon": "42355;",
            "Salacia": "120347;",
            "2002 AW197": "55565;",
            "2003 VS2": "84922;",
            "Asbolus": "8405;",
            "Gonggong": "225088;",
            "Huya": "38628;",
            "Hylonome": "10370;",
        }
        for body, expected_id in small_bodies.items():
            self.assertEqual(
                generate_transits.BODIES[body],
                expected_id,
                msg=f"{body} should have JPL id '{expected_id}'",
            )

    def test_week_snapshots_are_4_per_day(self):
        stamps = generate_transits.week_snapshot_datetimes(datetime(2026, 10, 4))
        self.assertEqual(len(stamps), 28)
        hours = sorted({s.hour for s in stamps})
        self.assertEqual(hours, [0, 6, 12, 18])
