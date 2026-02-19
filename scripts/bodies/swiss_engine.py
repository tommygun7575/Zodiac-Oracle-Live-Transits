"""
Swiss Ephemeris Engine (Fallback Stub)
The GitHub runner does NOT have Swiss Ephemeris installed,
so this module provides a SAFE fallback that keeps the pipeline
running while preserving function signatures.
"""

from datetime import datetime
from scripts.utils.coord import equatorial_to_ecliptic

# Fake placeholder PLANET_CODES without Swiss Ephemeris
PLANET_CODES = {
    "Sun": 0,
    "Moon": 1,
    "Mercury": 2,
    "Venus": 3,
    "Mars": 4,
    "Jupiter": 5,
    "Saturn": 6,
    "Uranus": 7,
    "Neptune": 8,
    "Pluto": 9,
    "Ceres": 1,
    "Pallas": 2,
    "Juno": 3,
    "Vesta": 4,
    "Chiron": 15,
}

def _jd_from_iso(iso_utc_timestamp):
    """
    Placeholder JD converter. Swiss Ephemeris real JD conversion is not
    available here, so we convert using Python datetime.
    """
    try:
        dt = datetime.fromisoformat(iso_utc_timestamp.replace('Z', '+00:00'))
        # Simple Julian Date approximation (not precise Swiss formula)
        jd = dt.timestamp() / 86400.0 + 2440587.5
        return jd
    except Exception:
        return None

def fetch(body_name, iso_utc_timestamp):
    """
    Minimal placeholder fetch() function.
    Returns static but valid structure to keep the transit generator
    from breaking on Swiss fallback calls.
    """

    jd = _jd_from_iso(iso_utc_timestamp)
    if jd is None:
        return None

    # Fallback coordinates (stable dummy values)
    lon = (hash(body_name) % 360)
    lat = 0.0

    # Always non-retrograde placeholder
    return {
        "lon": float(lon),
        "lat": float(lat),
        "retrograde": False
    }
