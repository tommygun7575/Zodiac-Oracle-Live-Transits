import requests
import numpy as np
import time

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

MAX_RETRIES = 4
RETRY_DELAY = 2

session = requests.Session()


def fetch_batch(body_id: str, start: str, stop: str):
    """
    Fetch weekly ephemeris from JPL Horizons.

    Returns:
        numpy array of shape (N,2) containing
        [longitude, latitude] for each timestep
    """

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

            response = session.get(
                HORIZONS_URL,
                params=params,
                timeout=60
            )

            if response.status_code == 200:

                data = response.json()

                if "result" not in data:
                    raise RuntimeError("Horizons returned malformed payload")

                return parse_ephemeris(data["result"])

            if response.status_code in (500, 502, 503, 504):

                time.sleep(RETRY_DELAY)
                continue

            raise RuntimeError(
                f"Horizons request failed {response.status_code}"
            )

        except requests.exceptions.RequestException:

            time.sleep(RETRY_DELAY)

    raise RuntimeError("Horizons unavailable after retries")


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

            rows.append((lon, lat))

        except ValueError:
            continue

    if not rows:
        raise RuntimeError("Horizons ephemeris parse produced no rows")

    return np.array(rows, dtype=float)
