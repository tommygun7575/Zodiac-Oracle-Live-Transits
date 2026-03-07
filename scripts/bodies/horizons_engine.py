import requests
import numpy as np
import time

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

MAX_RETRIES = 6
RETRY_DELAY = 3

session = requests.Session()


def fetch_batch(body_id: str, start: str, stop: str):

    params = {
        "format": "json",
        "COMMAND": body_id,
        "EPHEM_TYPE": "OBSERVER",
        "CENTER": "500@399",
        "REF_SYSTEM": "ICRF",
        "START_TIME": start,
        "STOP_TIME": stop,
        "STEP_SIZE": "1 d",
        "QUANTITIES": "18,20",
        "CSV_FORMAT": "YES"
    }

    last_error = None

    for attempt in range(MAX_RETRIES):

        try:

            r = session.get(HORIZONS_URL, params=params, timeout=60)

            if r.status_code != 200:
                raise RuntimeError(f"Horizons HTTP {r.status_code}")

            data = r.json()

            if "result" not in data:
                raise RuntimeError("Horizons malformed payload")

            text = data["result"]

            if "$$SOE" not in text:
                raise RuntimeError("Horizons returned no ephemeris block")

            rows = parse_ephemeris(text)

            if len(rows) == 0:
                raise RuntimeError("Empty ephemeris")

            return np.array(rows, dtype=float)

        except Exception as e:

            last_error = e

            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                raise RuntimeError(f"Horizons fetch failed: {e}")

    raise RuntimeError(last_error)


def parse_ephemeris(text: str):

    rows = []
    reading = False

    for raw in text.splitlines():

        line = raw.strip()

        if line.startswith("$$SOE"):
            reading = True
            continue

        if line.startswith("$$EOE"):
            break

        if not reading:
            continue

        parts = [p.strip() for p in line.split(",")]

        if len(parts) < 4:
            continue

        try:

            lon = float(parts[3]) % 360.0
            lat = float(parts[4])

            rows.append([lon, lat])

        except Exception:
            continue

    if len(rows) == 0:
        raise RuntimeError("Horizons ephemeris parse produced no rows")

    return rows
