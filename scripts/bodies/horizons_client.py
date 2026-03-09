import requests
import math
from datetime import datetime, timedelta

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"


def jd_to_iso(jd_string: str) -> str:
    jd = float(jd_string)
    base = datetime(2000, 1, 1, 12)  # J2000 reference
    dt = base + timedelta(days=jd - 2451545.0)
    return dt.strftime("%Y-%m-%d")


def fetch_jpl(body_id, start_date, stop_date, step_size="2d"):

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
        "CSV_FORMAT": "YES"
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
    ephemeris = {}

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

        if len(parts) >= 4:
            try:
                jd_raw = parts[0]
                x = float(parts[2])
                y = float(parts[3])

                lon = math.degrees(math.atan2(y, x)) % 360
                iso_date = jd_to_iso(jd_raw)

                ephemeris[iso_date] = lon

            except Exception:
                continue

    if not ephemeris:
        raise RuntimeError("JPL parsed zero rows")

    return ephemeris
