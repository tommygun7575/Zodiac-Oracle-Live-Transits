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
        "EPHEM_TYPE": "VECTORS",
        "CENTER": "500@10",
        "REF_PLANE": "ECLIPTIC",
        "START_TIME": start,
        "STOP_TIME": stop,
        "STEP_SIZE": "1 d"
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

            rows = parse_vectors(text)

            if len(rows) == 0:
                raise RuntimeError("Empty vector output")

            return np.array(rows, dtype=float)

        except Exception as e:

            last_error = e

            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                raise RuntimeError(f"Horizons fetch failed: {e}")

    raise RuntimeError(f"Horizons failure: {last_error}")


def parse_vectors(text: str):

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

        if "X =" in line and "Y =" in line and "Z =" in line:

            parts = line.replace("=", " ").replace(",", " ").split()

            try:

                x = float(parts[parts.index("X") + 1])
                y = float(parts[parts.index("Y") + 1])
                z = float(parts[parts.index("Z") + 1])

                lon = np.degrees(np.arctan2(y, x)) % 360
                lat = np.degrees(np.arctan2(z, np.sqrt(x*x + y*y)))

                rows.append([lon, lat])

            except Exception:
                continue

    if len(rows) == 0:
        raise RuntimeError("Horizons vector parse produced no rows")

    return rows
