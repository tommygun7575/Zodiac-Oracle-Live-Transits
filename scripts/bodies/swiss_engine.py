"""
Swiss Ephemeris Engine
Provides real Swiss Ephemeris positions via pyswisseph.
Falls back gracefully when a body is not supported.
"""

import os
import sys
from datetime import timezone
from pathlib import Path

import swisseph as swe
from dateutil import parser


PLANET_CODES = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
    "Chiron": swe.CHIRON,
    "Ceres": swe.CERES,
    "Pallas": swe.PALLAS,
    "Juno": swe.JUNO,
    "Vesta": swe.VESTA,
}

# Allow overriding ephemeris data path if present
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EPHE_PATH = PROJECT_ROOT / "ephe"
EPHE_PATH = Path(os.environ.get("SWISSEPH_EPHE_PATH", DEFAULT_EPHE_PATH))
HAS_EPHE_FILES = EPHE_PATH.is_dir()
EPHE_FLAG = swe.FLG_SWIEPH if HAS_EPHE_FILES else swe.FLG_MOSEPH
if HAS_EPHE_FILES:
    swe.set_ephe_path(str(EPHE_PATH))

MICROSECONDS_PER_SECOND = 1_000_000
SECONDS_PER_HOUR = 3600.0
MICROSECONDS_PER_HOUR = MICROSECONDS_PER_SECOND * SECONDS_PER_HOUR

_warned_bodies = set()


def _jd_from_iso(iso_utc_timestamp):
    try:
        dt = parser.isoparse(iso_utc_timestamp)
    except ValueError as exc:
        print(f"[WARN] SwissEphem unable to parse timestamp '{iso_utc_timestamp}': {exc}", file=sys.stderr)
        return None

    if dt.tzinfo is not None:
        # Swiss Ephemeris expects UTC; drop tzinfo after normalizing
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)

    return swe.julday(
        dt.year,
        dt.month,
        dt.day,
        dt.hour
        + dt.minute / 60.0
        + (dt.second / SECONDS_PER_HOUR)  # convert seconds to hours directly
        + (dt.microsecond / MICROSECONDS_PER_HOUR)  # microseconds → hours
    )


def fetch(body_name, iso_utc_timestamp):
    """
    Returns:
        {
            "lon": float,
            "lat": float,
            "retrograde": bool,
            "speed": float
        }
    or None if computation is not available.
    """
    code = PLANET_CODES.get(body_name)
    if code is None:
        return None

    jd = _jd_from_iso(iso_utc_timestamp)
    if jd is None:
        return None

    try:
        values, _ = swe.calc_ut(jd, code, EPHE_FLAG | swe.FLG_SPEED)
        lon, lat, dist, lon_speed, lat_speed, dist_speed = values
        retrograde = lon_speed < 0
        return {
            "lon": float(lon),
            "lat": float(lat),
            "retrograde": retrograde,
            "speed": float(lon_speed)
        }
    except (swe.Error, ValueError, TypeError) as exc:
        if body_name not in _warned_bodies:
            print(f"[WARN] SwissEphem calc failed for {body_name}: {exc}", file=sys.stderr)
            _warned_bodies.add(body_name)
        return None
