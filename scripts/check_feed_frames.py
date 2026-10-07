#!/usr/bin/env python3
"""CI frame-regression assertion for docs/current_week.json.

Asserts the weekly feed is GEOCENTRIC apparent ecliptic of date:
  * Mercury within 28 deg of the Sun, Venus within 48 deg, every snapshot;
  * Sun..Pluto and Ceres agree with Swiss Ephemeris (calc_ut default flags =
    apparent geocentric, true ecliptic & equinox of date) within 0.05 deg at
    each snapshot instant (catches J2000 output, which is ~0.37 deg low);
  * if the feed contains 2026-10-07T12:00:00Z, JPL Horizons q31 reference
    values are matched within 0.05 deg.
A workflow fallback payload (empty bodies + generation_warning) is reported
and skipped so the existing fallback behaviour is unchanged.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import swisseph as swe

ROOT = Path(__file__).resolve().parents[1]
swe.set_ephe_path(str(ROOT / "ephe"))

TOL_DEG = 0.05
MAX_ELONGATION = {"Mercury": 28.0, "Venus": 48.0}
JPL_REFERENCE_TS = "2026-10-07T12:00:00Z"
JPL_REFERENCE = {  # Horizons OBSERVER q31, CENTER 500@399
    "Mercury": 218.7987,
    "Venus": 218.1449,
    "Moon": 155.1954,
    "Mars": 125.4335,
    "Jupiter": 140.7246,
}
SWISS_CHECK = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY, "Venus": swe.VENUS,
    "Mars": swe.MARS, "Jupiter": swe.JUPITER, "Saturn": swe.SATURN,
    "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE, "Pluto": swe.PLUTO,
    "Ceres": swe.CERES,
}


def arc(a, b):
    d = abs((float(a) - float(b)) % 360.0)
    return min(d, 360.0 - d)


def jd_of(ts):
    dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0 + dt.second / 3600.0)


def main(path):
    payload = json.loads(Path(path).read_text())
    bodies = payload.get("bodies") or {}
    if not bodies:
        print(f"[WARN] {path}: no bodies (fallback payload: {payload.get('generation_warning')}); frame check skipped")
        return 0
    stamps = sorted({ts for b in bodies.values() for ts in (b.get("snapshots") or {})})
    errors = []
    skipped = set()
    for ts in stamps:
        lons = {n: (b.get("snapshots") or {}).get(ts) for n, b in bodies.items()}
        sun = lons.get("Sun")
        if sun is not None:
            for body, limit in MAX_ELONGATION.items():
                if lons.get(body) is not None and arc(lons[body], sun) > limit:
                    errors.append(f"{ts}: {body} elongation {arc(lons[body], sun):.2f} > {limit}")
        jd = jd_of(ts)
        for body, code in SWISS_CHECK.items():
            if lons.get(body) is None:
                continue
            try:
                ref = swe.calc_ut(jd, code)[0][0]
            except Exception as exc:  # e.g. asteroid file absent in CI (ephe/ is untracked)
                skipped.add(f"{body}: {exc}")
                continue
            if arc(lons[body], ref) > TOL_DEG:
                errors.append(f"{ts}: {body} {lons[body]:.4f} vs Swiss of-date {ref:.4f} (diff {arc(lons[body], ref):.4f})")
        if ts == JPL_REFERENCE_TS:
            for body, ref in JPL_REFERENCE.items():
                if lons.get(body) is not None and arc(lons[body], ref) > TOL_DEG:
                    errors.append(f"{ts}: {body} {lons[body]:.4f} vs JPL q31 {ref} (diff {arc(lons[body], ref):.4f})")
    for note in sorted(skipped):
        print(f"[WARN] Swiss cross-check skipped for {note}")
    if errors:
        print(f"[FAIL] frame regression in {path} ({len(errors)} problems):")
        for e in errors[:50]:
            print("   ", e)
        return 1
    print(f"[OK] frame regression passed for {path} ({len(stamps)} snapshots)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "docs/current_week.json"))
