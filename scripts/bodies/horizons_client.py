import requests
import math
from datetime import datetime, timedelta, timezone

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"


def jd_to_iso(jd_string: str) -> str:
    jd = float(jd_string)
    base = datetime(2000, 1, 1, 12)  # J2000 reference
    dt = base + timedelta(days=jd - 2451545.0)
    return dt.strftime("%Y-%m-%d")


def fetch_horizons(body_name):
    """Fetch current ecliptic longitude for a single body.

    Returns {"lon": float}.
    Raises RuntimeError("Malformed Horizons response") if the API result is missing.
    Raises RuntimeError("No longitude found") if no data rows are parsed.
    """
    now = datetime.now(timezone.utc)
    params = {
        "format": "json",
        "COMMAND": body_name,
        "MAKE_EPHEM": "YES",
        "EPHEM_TYPE": "OBSERVER",
        "CENTER": "500@399",
        "START_TIME": now.strftime("%Y-%m-%d"),
        "STOP_TIME": (now + timedelta(days=1)).strftime("%Y-%m-%d"),
        "STEP_SIZE": "1d",
        "QUANTITIES": "31",
        "CSV_FORMAT": "YES",
    }

    response = requests.get(HORIZONS_URL, params=params, timeout=60)

    if response.status_code != 200:
        raise RuntimeError(f"Horizons HTTP error {response.status_code}")

    try:
        data = response.json()
    except Exception:
        raise RuntimeError("Malformed Horizons response")

    if "result" not in data:
        raise RuntimeError("Malformed Horizons response")

    lines = data["result"].splitlines()
    capture = False

    for line in lines:
        if "$$SOE" in line:
            capture = True
            continue
        if "$$EOE" in line:
            break
        if not capture:
            continue

        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 5:
            try:
                lon = float(parts[4])
                return {"lon": lon}
            except (ValueError, IndexError):
                continue

    raise RuntimeError("No longitude found")


def fetch_jpl(body_id, start_date, stop_date, step_size="1d"):
    """Fetch weekly ecliptic positions from JPL Horizons VECTORS table.

    Returns a list of (lon, lat) tuples, one per step in the date range.
    """
    params = {
        "format": "json",
        "COMMAND": body_id,
        "MAKE_EPHEM": "YES",
        "EPHEM_TYPE": "VECTORS",
        "CENTER": "@0",
        "REF_PLANE": "ECLIPTIC",
        "REF_SYSTEM": "J2000",
        "START_TIME": start_date,
        "STOP_TIME": stop_date,
        "STEP_SIZE": step_size,
        "VEC_TABLE": "3",
        "OUT_UNITS": "AU-D",
        "CSV_FORMAT": "YES",
    }

    response = requests.get(HORIZONS_URL, params=params, timeout=60)

    if response.status_code != 200:
        raise RuntimeError(f"JPL HTTP error {response.status_code}")

    try:
        data = response.json()
    except Exception:
        raise RuntimeError("JPL did not return valid JSON")

    if "result" not in data:
        raise RuntimeError("JPL missing result block")

    lines = data["result"].splitlines()
    capture = False
    results = []

    for line in lines:
        if "$$SOE" in line:
            capture = True
            continue
        if "$$EOE" in line:
            break
        if not capture:
            continue

        parts = [p.strip() for p in line.split(",")]

        # CSV VEC_TABLE=3 layout:
        # column 0 = Julian Day
        # column 2 = X (AU)
        # column 3 = Y (AU)
        # column 4 = Z (AU)

        if len(parts) >= 5:
            try:
                x = float(parts[2])
                y = float(parts[3])
                z = float(parts[4])

                lon = math.degrees(math.atan2(y, x)) % 360
                lat = math.degrees(math.atan2(z, math.hypot(x, y)))

                results.append((lon, lat))
            except Exception:
                continue

    if not results:
        raise RuntimeError("JPL parsed zero rows")

    return results
