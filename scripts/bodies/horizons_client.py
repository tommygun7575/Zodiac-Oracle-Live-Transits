import requests

HORIZONS_URL = "https://ssd.jpl.nasa.gov/horizons_batch.cgi"

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
        "batch": 1,
        "COMMAND": body_id,
        "CENTER": "500@399",
        "MAKE_EPHEM": "YES",
        "TABLE_TYPE": "OBSERVER",
        "START_TIME": start,
        "STOP_TIME": stop,
        "STEP_SIZE": "1 d",
        "QUANTITIES": "18,20",
        "CSV_FORMAT": "YES"
    }

    r = requests.get(HORIZONS_URL, params=params, timeout=60)

    if r.status_code != 200:
        raise RuntimeError("Horizons request failed")

    return parse_ephemeris(r.text)


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

            rows.append({
                "date": parts[0].strip(),
                "lon": float(parts[4])
            })

        except ValueError:
            continue

    return rows
