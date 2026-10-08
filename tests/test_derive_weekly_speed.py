"""Weekly 6h-difference derived speed layer (synthetic feed)."""
import unittest

from scripts.derive_weekly_speed import derive, expected_slots, wrap180


def _feed(lon_fn):
    slots = expected_slots("2026-10-04", "2026-10-10")
    bodies = {}
    for name, fn in lon_fn.items():
        bodies[name] = {"source": "JPL", "snapshots": {s: fn(i) % 360 for i, s in enumerate(slots)}, "data": {}}
    return {"week_start": "2026-10-04", "week_end": "2026-10-10", "generated_utc": "x",
            "snapshot_schedule_utc": {"hours": [0, 6, 12, 18]}, "bodies": bodies}


class TestWeeklyDerived(unittest.TestCase):
    def test_centered_speed_across_wrap(self):
        f = _feed({"Moon": lambda i: 350 + 3.25 * i, "Regulus": lambda i: 150.2, "Saturn": lambda i: 8.0 - 0.0005 * i})
        out = derive(f)
        sp = out["bodies"]["Moon"]["speed_deg_per_day"]
        self.assertTrue(all(abs(x - 13.0) < 1e-9 for x in sp))
        self.assertEqual("weekly_6h_difference", out["bodies"]["Moon"]["speed_source"])
        self.assertTrue(out["bodies"]["Moon"]["crosses_0_360"])
        self.assertEqual(["fixed"] * 28, out["bodies"]["Regulus"]["motion"])
        self.assertEqual([], out["bodies"]["Regulus"]["station_events"])
        self.assertTrue(out["all_passed"])
        self.assertEqual("retrograde", out["bodies"]["Saturn"]["motion"][5])

    def test_missing_snapshot_fails(self):
        f = _feed({"Moon": lambda i: 10 + 3.25 * i})
        f["bodies"]["Moon"]["snapshots"].pop("2026-10-06T12:00:00Z")
        out = derive(f)
        self.assertFalse(out["all_passed"])

    def test_wrap180(self):
        self.assertAlmostEqual(2.0, wrap180(1 - 359))


if __name__ == "__main__":
    unittest.main()
