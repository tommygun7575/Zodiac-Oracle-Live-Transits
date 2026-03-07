import requests
import time

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

BODY_IDS = {
    "Sun": "10",
    "Moon": "301",
    "Mercury": "199",
    "Venus": "299",
    "Mars": "499",
    "Jupiter": "599",
    "Saturn": "699",
    "Uranus": "799",
    "Neptune": "899",
    "Pluto": "999",
    "Ceres": "1",
    "Pallas": "2",
    "Juno": "3",
    "Vesta": "4",
    "Eris": "136199",
    "Sedna": "90377",
    "Orcus": "90482",
    "Makemake": "136472",
    "Haumea": "136108",
    "Quaoar": "50000",
    "Ixion": "28978"
}


def fetch_batch(body, start, stop):

    if body not in BODY_IDS:
        raise RuntimeError(f"Unknown body {body}")

    params = {
        "format": "json",
        "COMMAND": BODY_IDS[body],
        "EPHEM_TYPE": "OBSERVER",
        "CENTER": "500@399",
        "START_TIME": start,
        "STOP_TIME": stop,
        "STEP_SIZE": "1 d",
        "QUANTITIES": "1,2,3,4",
        "CSV_FORMAT": "YES"
    }

    for attempt in range(3):

        r = requests.get(HORIZONS_URL, params=params, timeout=60)

        if r.status_code == 200:

            data = r.json()

            if "result" not in data:
                raise RuntimeError("Horizons malformed response")

            rows = parse_ephemeris(data["result"])

            if rows:
                return rows

        time.sleep(2)

    raise RuntimeError(f"Horizons failed for {body}")


def parse_ephemeris(text):

    rows = []
    reading = False

    for line in text.splitlines():

        if "$$SOE" in line:
            reading = True
            continue

        if "$$EOE" in line:
            break

        if reading:

            parts = [p.strip() for p in line.split(",")]

            if len(parts) < 4:
                continue

            try:

                lon = float(parts[3])
                lat = float(parts[4]) if len(parts) > 4 else 0.0

                rows.append((lon, lat))

            except Exception:
                continue

    return rows
