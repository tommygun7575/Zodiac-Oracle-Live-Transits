import requests
import numpy as np

HORIZONS_API = "https://ssd.jpl.nasa.gov/api/horizons.api"


def fetch_batch(body_id, start, stop):

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

    r = requests.get(HORIZONS_API, params=params, timeout=60)

    if r.status_code != 200:
        raise RuntimeError("Horizons request failed")

    data = r.json()

    if "result" not in data:
        raise RuntimeError("Horizons returned no result")

    return parse_ephemeris(data["result"])


def parse_ephemeris(text):

    rows = []
    active = False

    for line in text.splitlines():

        if "$$SOE" in line:
            active = True
            continue

        if "$$EOE" in line:
            break

        if not active:
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
        raise RuntimeError("No ephemeris parsed")

    return np.array(rows)
