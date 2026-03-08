import requests

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
    "Pluto": "999"
}


def fetch_horizons(body, start, stop):

    body_id = BODY_IDS[body]

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

    r = requests.get(HORIZONS_URL, params=params, timeout=60)

    if r.status_code != 200:
        raise RuntimeError("Horizons request failed")

    data = r.json()

    if "result" not in data:
        raise RuntimeError("Malformed Horizons response")

    return parse_ephemeris(data["result"])


def parse_ephemeris(text):

    reading = False
    rows = []

    for line in text.splitlines():

        if "$$SOE" in line:
            reading = True
            continue

        if "$$EOE" in line:
            break

        if reading:

            parts = line.split(",")

            if len(parts) > 4:

                try:
                    rows.append({
                        "date": parts[0].strip(),
                        "lon": float(parts[4])
                    })
                except:
                    pass

    return rows
