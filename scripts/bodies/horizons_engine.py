import requests
import time

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

NAIF_IDS = {
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

def _parse_lonlat(text):

    lines = text.splitlines()

    start = None
    for i,l in enumerate(lines):
        if "$$SOE" in l:
            start = i+1
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

    if body not in NAIF_IDS:
        return None

    params = {
        "format": "text",
        "COMMAND": NAIF_IDS[body],
        "EPHEM_TYPE": "OBSERVER",
        "CENTER": "500@399",
        "TLIST": jd,
        "QUANTITIES": "18,19"
    }

    try:

        r = requests.get(HORIZONS_URL, params=params, timeout=20)

        parsed = _parse_lonlat(r.text)

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

        r = requests.get(HORIZONS_URL, params=params, timeout=20)

        parsed = _parse_lonlat(r.text)

        if not parsed:
            return None

        lon, lat = parsed

        time.sleep(0.5)

        return lon, lat, "jpl"

    except:
        return None
