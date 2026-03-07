import requests
import numpy as np

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"


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

    response = requests.get(HORIZONS_URL, params=params, timeout=60)

    if response.status_code != 200:
        raise RuntimeError(f"Horizons request failed {response.status_code}")

    data = response.json()

    if "result" not in data:
        raise RuntimeError("Horizons returned malformed response")

    return parse_ephemeris(data["result"])


def parse_ephemeris(text: str):

    rows = []
    reading = False

    for line in text.splitlines():

        if "$$SOE" in line:
            reading = True
            continue

        if "$$EOE" in line:
            break

        if not reading:
            continue

        parts = line.split(",")

        if len(parts) < 5:
            continue

        try:
            lon = float(parts[3])
            lat = float(parts[4])
        except:
            continue

        rows.append((lon, lat))

    if len(rows) == 0:
        raise RuntimeError("No ephemeris rows parsed from Horizons")

    return np.array(rows)
