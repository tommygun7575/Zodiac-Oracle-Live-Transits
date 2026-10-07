"""Frame regression: weekly bodies must be GEOCENTRIC apparent ecliptic OF DATE.

Guards against the former J2000 VECTORS path (~0.37 deg low in 2026) and any
heliocentric/Sun-centred output.
"""
import unittest
from datetime import datetime

from scripts.bodies.miriade_engine import parse_angle
from scripts.generate_transits import fetch_swiss

REF = datetime(2026, 10, 7, 12, 0, 0)
# JPL Horizons OBSERVER QUANTITIES='31', CENTER='500@399', 2026-10-07 12:00 UTC
JPL_Q31 = {
    "Mercury": 218.7987,
    "Venus": 218.1449,
    "Moon": 155.1954,
    "Mars": 125.4335,
    "Jupiter": 140.7246,
}


def arc(a, b):
    d = abs((a - b) % 360.0)
    return min(d, 360.0 - d)


class FrameRegressionTests(unittest.TestCase):
    def test_swiss_fallback_matches_jpl_q31(self):
        for body, ref in JPL_Q31.items():
            lon, _ = fetch_swiss(body, REF)
            self.assertLess(arc(lon, ref), 0.05, f"{body}: {lon} vs {ref}")

    def test_inner_planet_elongation_limits(self):
        sun, _ = fetch_swiss("Sun", REF)
        merc, _ = fetch_swiss("Mercury", REF)
        venus, _ = fetch_swiss("Venus", REF)
        self.assertLessEqual(arc(merc, sun), 28.0)
        self.assertLessEqual(arc(venus, sun), 48.0)

    def test_miriade_sexagesimal(self):
        self.assertLess(arc(parse_angle("+218:47:55.13162"), JPL_Q31["Mercury"]), 0.05)
        self.assertAlmostEqual(parse_angle("-02:28:10.6779"), -2.46963, places=4)


if __name__ == "__main__":
    unittest.main()
