import requests
import math
from datetime import datetime, timedelta

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"


def jd_to_iso(jd):
    jd = float(jd)
    base = datetime(2000, 1, 1, 12)
    delta = timedelta(days=jd - 2451545.0)
    dt = base + timedelta(days=jd - 2451545.0)
    return dt.strftime("%Y-%m-%d")


def fetch_jpl(body_id, start_date, stop_date, step_size="2d"):

    params = {
        "format": "json",
        "COMMAND": body_id,
        "MAKE_EPHEM": "YES",
        "EPHEM_TYPE": "VECTORS",
        "CENTER": "500@0",
        "START_TIME": start_date,
        "STOP_TIME": stop_date,
        "STEP_SIZE": step_size,
        "OUT_UNITS": "AU-D",
        "REF_PLANE": "ECLIPTIC",
        "REF_SYSTEM": "J2000"
    }

    r = requests.get(HORIZONS_URL, params=params, timeout=60)

    if r.status_code != 200:
        raise RuntimeError(f"JPL HTTP {r.status_code}")

    data = r.json()

    if "result" not in data:
        raise RuntimeError("JPL no ephemeris")

    lines = data["result"].splitlines()

    ephemeris = {}
    capture = False
    current_jd = None

    for line in lines:

        if "$$SOE" in line:
            capture = True
            continue

        if "$$EOE" in line:
            break

        if not capture:
            continue

        parts = line.strip().split()

        if len(parts) == 2:
            current_jd = parts[0]

        if "X =" in line and "Y =" in line:
            try:
                x = float(line.split("X =")[1].split()[0])
                y = float(line.split("Y =")[1].split()[0])

                lon = math.degrees(math.atan2(y, x))
                if lon < 0:
                    lon += 360

                iso_date = jd_to_iso(current_jd)
                ephemeris[iso_date] = lon

            except:
                continue

    if not ephemeris:
        raise RuntimeError("JPL parsed zero rows")

    return ephemeris
