import requests
import numpy as np
import time

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

MAX_RETRIES = 4
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

    for attempt in range(MAX_RETRIES):

        try:
            response = session.get(HORIZONS_URL, params=params, timeout=60)

            if response.status_code == 200:

                data = response.json()

                if "result" not in data:
                    raise RuntimeError("Horizons malformed payload")

                text = data["result"]

                if "$$SOE" not in text:
                    raise RuntimeError("Horizons returned no ephemeris block")

                return parse_ephemeris(text)

            if response.status_code in (500, 502, 503, 504):
                time.sleep(RETRY_DELAY)
                continue

            raise RuntimeError(f"Horizons request failed {response.status_code}")

        except requests.exceptions.RequestException:
            time.sleep(RETRY_DELAY)

    raise RuntimeError("Horizons unavailable after retries")


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

        if not line:
            continue

        parts = [p.strip() for p in line.split(",")]

        if len(parts) < 3:
            continue

        floats = []

        for p in parts:
            try:
                floats.append(float(p))
            except:
                continue

        if len(floats) < 2:
            continue

        lon = floats[0]
        lat = floats[1]

        rows.append((lon, lat))

    if len(rows) == 0:
        raise RuntimeError("Horizons ephemeris parse produced no rows")

    return np.array(rows, dtype=float)
