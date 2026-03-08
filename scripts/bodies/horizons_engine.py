import requests
import time

HORIZONS_URL = "https://ssd-api.jpl.nasa.gov/horizons.api"

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
    "Ceres": "1;",
    "Pallas": "2;",
    "Juno": "3;",
    "Vesta": "4;",
    "Eris": "136199;",
    "Sedna": "90377;",
    "Orcus": "90482;",
    "Makemake": "136472;",
    "Haumea": "136108;",
    "Quaoar": "50000;",
    "Ixion": "28978;"
}


def parse_ephemeris(text):

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

        parts = [p.strip() for p in line.split(",")]

        if len(parts) < 5:
            continue

        try:
            lon = float(parts[3])
            lat = float(parts[4])
            rows.append((lon, lat))
        except:
            rows.append((None, None))

    return rows


def fetch_batch(body, start, stop):

    if body not in BODY_IDS:
        raise RuntimeError(f"Unknown body {body}")

    params = {
        "format": "text",
        "COMMAND": BODY_IDS[body],
        "EPHEM_TYPE": "OBSERVER",
        "CENTER": "500@399",
        "START_TIME": start,
        "STOP_TIME": stop,
        "STEP_SIZE": "1 d",
        "QUANTITIES": "31",
        "CSV_FORMAT": "YES",
        "ANG_FORMAT": "DEG"
    }

    for attempt in range(3):

        r = requests.get(HORIZONS_URL, params=params, timeout=60)

        if r.status_code == 200:

            rows = parse_ephemeris(r.text)

            if rows:
                return rows

        if attempt < 2:
            time.sleep(2)

    raise RuntimeError(f"Horizons failed for {body}")
