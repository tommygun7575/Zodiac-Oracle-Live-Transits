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

    payload = r.json()

    if "result" not in payload:
        raise RuntimeError("Horizons response malformed")

    text = payload["result"]

    return parse_ephemeris(text)


def parse_ephemeris(text):

    rows = []

    if "$$SOE" not in text or "$$EOE" not in text:
        return rows

    start = text.index("$$SOE") + 5
    end = text.index("$$EOE")

    block = text[start:end].strip().splitlines()

    for line in block:

        parts = line.split(",")

        if len(parts) < 5:
            continue

        try:

            date = parts[0].strip()
            lon = float(parts[4])

            rows.append({
                "date": date,
                "lon": lon
            })

        except ValueError:
            continue

    return rows
