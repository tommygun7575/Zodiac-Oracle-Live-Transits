import requests

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"


def fetch_jpl(body_id, start_date, stop_date, step_size="2d"):

    params = {
        "format": "json",
        "COMMAND": body_id,
        "MAKE_EPHEM": "YES",
        "EPHEM_TYPE": "OBSERVER",
        "CENTER": "500@399",          # Earth center
        "START_TIME": start_date,
        "STOP_TIME": stop_date,
        "STEP_SIZE": step_size,
        "QUANTITIES": "2",            # Ecliptic longitude
        "CSV_FORMAT": "YES"
    }

    r = requests.get(HORIZONS_URL, params=params, timeout=60)

    if r.status_code != 200:
        raise RuntimeError(f"JPL HTTP {r.status_code}")

    data = r.json()

    if "result" not in data:
        raise RuntimeError("JPL no ephemeris block")

    lines = data["result"].splitlines()

    ephemeris = {}
    capture = False

    for line in lines:

        if "$$SOE" in line:
            capture = True
            continue

        if "$$EOE" in line:
            break

        if not capture:
            continue

        line = line.strip()

        if not line:
            continue

        # CSV row format example:
        # 2026-Mar-09 00:00, 123.4567
        parts = line.split(",")

        if len(parts) < 2:
            continue

        try:
            date_str = parts[0].strip().split()[0]
            lon = float(parts[1].strip())

            ephemeris[date_str] = lon

        except Exception:
            continue

    if not ephemeris:
        raise RuntimeError("JPL parsed zero rows")

    return ephemeris
