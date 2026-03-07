import requests
import numpy as np
import time


HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

MAX_RETRIES = 5
RETRY_DELAY = 2


session = requests.Session()


def fetch_batch(body_id: str, start: str, stop: str):

    params = {
        "format": "json",
        "COMMAND": body_id,
        "EPHEM_TYPE": "OBSERVER",
        "CENTER": "500@399",
        "START_TIME": start,
        "STOP_TIME": stop,
        "STEP_SIZE": "1 d",
        "QUANTITIES": "18,20",
        "CSV_FORMAT": "YES"
    }

    last_error = None

    for attempt in range(MAX_RETRIES):

        try:

            response = session.get(
                HORIZONS_URL,
                params=params,
                timeout=60
            )

            if response.status_code != 200:
                raise RuntimeError(f"Horizons HTTP {response.status_code}")

            data = response.json()

            if "result" not in data:
                raise RuntimeError("Horizons malformed response")

            text = data["result"]

            if "$$SOE" not in text:
                raise RuntimeError("Horizons returned no ephemeris block")

            rows = parse_ephemeris(text)

            if len(rows) == 0:
                raise RuntimeError("Ephemeris returned empty")

            return np.array(rows, dtype=float)

        except Exception as e:

            last_error = e

            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                raise RuntimeError(f"Horizons fetch failed: {e}")

    raise RuntimeError(f"Horizons failure: {last_error}")


def parse_ephemeris(text: str):

    rows = []

    reading = False

    for raw in text.splitlines():

        line = raw.strip()

        if not line:
            continue

        if line.startswith("$$SOE"):
            reading = True
            continue

        if line.startswith("$$EOE"):
            break

        if not reading:
            continue

        parts = [p.strip() for p in line.split(",")]

        if len(parts) < 2:
            continue

        numeric = []

        for p in parts:
            try:
                numeric.append(float(p))
            except ValueError:
                continue

        if len(numeric) < 2:
            continue

        lon = numeric[0] % 360.0
        lat = numeric[1]

        rows.append([lon, lat])

    if len(rows) == 0:
        raise RuntimeError("Horizons ephemeris parse produced no rows")

    return rows
