"""JPL Horizons client for the Zodiac Oracle weekly feed.

FRAME CONTRACT: every longitude/latitude returned here is GEOCENTRIC APPARENT
ecliptic longitude/latitude referred to the TRUE ecliptic & equinox OF DATE
(tropical) — Horizons OBSERVER table, QUANTITIES='31' (ObsEcLon/ObsEcLat),
CENTER='500@399'. This matches Swiss Ephemeris calc_ut default flags and the
Black Zodiac daily/6-month feeds.

(The former fetch_jpl used a VECTORS table with REF_SYSTEM=J2000: geometric,
J2000 ecliptic/equinox, no light-time or aberration -> ~0.37 deg LOW in 2026.)
"""

import math
from datetime import datetime, timedelta, timezone

import requests

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"


def jd_to_iso(jd_string: str) -> str:
    jd = float(jd_string)
    base = datetime(2000, 1, 1, 12)  # J2000 reference
    dt = base + timedelta(days=jd - 2451545.0)
    return dt.strftime("%Y-%m-%d")


def _observer_q31_params(command, start, stop, step):
    return {
        "format": "json",
        "COMMAND": command,
        "MAKE_EPHEM": "YES",
        "EPHEM_TYPE": "OBSERVER",
        "CENTER": "500@399",
        "START_TIME": start,
        "STOP_TIME": stop,
        "STEP_SIZE": step,
        "QUANTITIES": "31",
        "CSV_FORMAT": "YES",
    }


def parse_q31_rows(result_text):
    """Parse ObsEcLon/ObsEcLat rows between $$SOE/$$EOE.

    Columns are located from the CSV header line. Without a header the
    standard q31 layout is assumed: date, solar-flag, lunar-flag, lon, lat.
    Returns a list of (lon, lat).
    """
    lon_idx, lat_idx = 3, 4
    rows = []
    capture = False
    for line in result_text.splitlines():
        if "ObsEcLon" in line and "ObsEcLat" in line:
            header = [p.strip() for p in line.split(",")]
            lon_idx = header.index("ObsEcLon")
            lat_idx = header.index("ObsEcLat")
            continue
        if "$$SOE" in line:
            capture = True
            continue
        if "$$EOE" in line:
            break
        if not capture:
            continue
        parts = [p.strip() for p in line.split(",")]
        try:
            lon = float(parts[lon_idx])
            lat = float(parts[lat_idx])
        except (ValueError, IndexError):
            continue
        if math.isfinite(lon) and math.isfinite(lat):
            rows.append((lon % 360.0, lat))
    return rows


def fetch_horizons(body_name):
    """Fetch current geocentric apparent ecliptic-of-date longitude.

    Returns {"lon": float}.
    Raises RuntimeError("Malformed Horizons response") if the API result is missing.
    Raises RuntimeError("No longitude found") if no data rows are parsed.
    """
    now = datetime.now(timezone.utc)
    params = _observer_q31_params(
        body_name,
        now.strftime("%Y-%m-%d"),
        (now + timedelta(days=1)).strftime("%Y-%m-%d"),
        "1d",
    )

    response = requests.get(HORIZONS_URL, params=params, timeout=60)

    if response.status_code != 200:
        raise RuntimeError(f"Horizons HTTP error {response.status_code}")

    try:
        data = response.json()
    except Exception:
        raise RuntimeError("Malformed Horizons response")

    if "result" not in data:
        raise RuntimeError("Malformed Horizons response")

    rows = parse_q31_rows(data["result"])
    if not rows:
        raise RuntimeError("No longitude found")
    return {"lon": rows[0][0]}


def fetch_jpl(body_id, start_date, stop_date, step_size="1d"):
    """Fetch geocentric apparent ecliptic-of-date positions (Horizons q31).

    Returns a list of (lon, lat) tuples, one per step in the date range.
    """
    params = _observer_q31_params(body_id, start_date, stop_date, step_size)

    response = requests.get(HORIZONS_URL, params=params, timeout=60)

    if response.status_code != 200:
        raise RuntimeError(f"JPL HTTP error {response.status_code}")

    try:
        data = response.json()
    except Exception:
        raise RuntimeError("JPL did not return valid JSON")

    if "result" not in data:
        raise RuntimeError("JPL missing result block")

    results = parse_q31_rows(data["result"])

    if not results:
        raise RuntimeError("JPL parsed zero rows")

    return results
