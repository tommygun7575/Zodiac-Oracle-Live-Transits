"""Backward-compat checks mirroring NOLWELL TransitParser behavior."""
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from scripts import generate_transits
from scripts.bodies.aether_engine import compute_aether_longitudes, VERIFIED_AETHER


def _android_transit_parser_select(data_keys, today=None):
    """Mirror TransitParser: prefer today YYYY-MM-DD else max key."""
    today = today or datetime.utcnow().strftime("%Y-%m-%d")
    keys = list(data_keys)
    if not keys:
        return None
    return today if today in keys else max(keys)


class AndroidContractTests(unittest.TestCase):
    def test_required_top_level_keys(self):
        payload = generate_transits._new_output_template("2026-10-04", "2026-10-10")
        required = {
            "generated_utc", "week_start", "week_end", "engine_version",
            "coverage", "resolved", "total_targets", "missing",
            "bodies", "arabic_parts", "fixed_star_conjunctions",
        }
        self.assertTrue(required.issubset(payload.keys()))

    def test_pack_body_series_keeps_date_keys_and_adds_snapshots(self):
        start = datetime(2026, 10, 4)
        snaps = generate_transits.week_snapshot_datetimes(start)
        entries = [
            {"lon": 100.0 + i * 0.1, "lat": 0.0, "source": "JPL",
             "timestamp": generate_transits.snapshot_iso(s)}
            for i, s in enumerate(snaps)
        ]
        packed = generate_transits._pack_body_series(entries, snaps)
        self.assertIn("source", packed)
        self.assertIn("data", packed)
        self.assertIn("snapshots", packed)
        # Daily keys are YYYY-MM-DD only
        for key in packed["data"]:
            self.assertEqual(len(key), 10)
            self.assertRegex(key, r"^\d{4}-\d{2}-\d{2}$")
        self.assertEqual(len(packed["data"]), 7)
        self.assertEqual(len(packed["snapshots"]), 28)
        # Android selector finds today or max
        today = "2026-10-06"
        active = _android_transit_parser_select(packed["data"].keys(), today=today)
        self.assertEqual(active, today)
        self.assertTrue(isinstance(packed["data"][active], float))

    def test_arabic_parts_not_asc_equals_sun(self):
        parts = generate_transits.compute_arabic_parts({"Sun": 10.0, "Moon": 20.0})
        self.assertEqual(parts.get("status"), "unavailable")
        self.assertNotIn("Fortune", parts)

    def test_aether_three_formulas_only(self):
        vals = compute_aether_longitudes(10, 20, 30, 60, 100, 40)
        self.assertEqual(list(vals.keys()), list(VERIFIED_AETHER))
        self.assertAlmostEqual(vals["Aetheric_SunMoon_Midpoint"], 30.0)
        self.assertAlmostEqual(vals["Aetheric_Jovian_Arc"], 60.0)
        self.assertAlmostEqual(vals["Aetheric_Elemental_Balance"], (20 + 30 + 60) / 3.0)

    def test_validator_rejects_iso_keys_inside_data(self):
        payload = generate_transits._new_output_template("2026-10-04", "2026-10-10")
        payload["bodies"]["Sun"] = {
            "source": "JPL",
            "data": {"2026-10-04T00:00:00Z": 100.0},
        }
        self.assertFalse(generate_transits._is_valid_output_payload(payload))

    def test_validator_accepts_legacy_shape(self):
        payload = generate_transits._new_output_template("2026-10-04", "2026-10-10")
        payload["bodies"]["Sun"] = {
            "source": "Swiss",
            "data": {
                "2026-10-04": 191.0,
                "2026-10-05": 192.0,
                "2026-10-06": 193.0,
                "2026-10-07": 194.0,
                "2026-10-08": 195.0,
                "2026-10-09": 196.0,
                "2026-10-10": 197.0,
            },
            "snapshots": {"2026-10-04T00:00:00Z": 191.0},
        }
        self.assertTrue(generate_transits._is_valid_output_payload(payload))
        self.assertTrue(generate_transits._android_can_read(payload))

    @patch("scripts.generate_transits.get_fixed_star_week", return_value=[])
    @patch("scripts.generate_transits.resolve_body")
    def test_main_emits_android_readable_feed(self, mock_resolve, _mock_stars):
        from datetime import timedelta
        start = datetime(2026, 10, 4)
        snaps = generate_transits.week_snapshot_datetimes(start)

        def fake_resolve(name, start_date, snapshots=None):
            snapshots = snapshots or snaps
            return [
                {
                    "lon": 10.0 + i * 0.01,
                    "lat": 0.0,
                    "source": "JPL",
                    "timestamp": generate_transits.snapshot_iso(s),
                }
                for i, s in enumerate(snapshots)
            ]

        mock_resolve.side_effect = fake_resolve
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "current_week.json"
            with patch(
                "scripts.generate_transits.get_week_range",
                return_value=(start.date(), start.date() + timedelta(days=6)),
            ):
                generate_transits.main(output_path=out)
            payload = json.loads(out.read_text())
            self.assertTrue(generate_transits._is_valid_output_payload(payload))
            self.assertTrue(generate_transits._android_can_read(payload))
            sun = payload["bodies"]["Sun"]
            self.assertEqual(len(sun["data"]), 7)
            self.assertEqual(len(sun["snapshots"]), 28)
            self.assertEqual(payload["arabic_parts"].get("status"), "unavailable")
            self.assertIn("snapshot_schedule_utc", payload)
            self.assertEqual(payload["houses"]["system"], "Placidus")
            for aether in VERIFIED_AETHER:
                self.assertIn(aether, payload["bodies"])


if __name__ == "__main__":
    unittest.main()
