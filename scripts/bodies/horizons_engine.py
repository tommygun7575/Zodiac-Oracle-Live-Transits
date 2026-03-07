import requests
import re
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
    "Pluto": "999"
}


def _parse(text):

    start = None

    lines = text.splitlines()

    for i,l in enumerate(lines):
        if "$$SOE" in l:
            start = i + 1
            break

    if start is None:
        return None

    row = lines[start].split(",")

    try:
        lon = float(row[5])
        lat = float(row[6])
        return lon, lat
    except:
        return None


def fetch(body, jd):

    body_id = BODY_IDS.get(body)

    if not body_id:
        return None

    params = {
        "format": "text",
        "COMMAND": body_id,
        "EPHEM_TYPE": "OBSERVER",
        "CENTER": "500@399",
        "TLIST": jd,
        "QUANTITIES": "18,19"
    }

    try:

        r = requests.get(HORIZONS_URL, params=params, timeout=15)

        parsed = _parse(r.text)

        if not parsed:
            return None

        lon, lat = parsed

        time.sleep(0.5)

        return lon, lat, "jpl"

    except:
        return None


def fetch_numbered(number, jd):

    params = {
        "format": "text",
        "COMMAND": str(number),
        "EPHEM_TYPE": "OBSERVER",
        "CENTER": "500@399",
        "TLIST": jd,
        "QUANTITIES": "18,19"
    }

    try:

        r = requests.get(HORIZONS_URL, params=params, timeout=15)

        parsed = _parse(r.text)

        if not parsed:
            return None

        lon, lat = parsed

        time.sleep(0.5)

        return lon, lat, "jpl"

    except:
        return None
