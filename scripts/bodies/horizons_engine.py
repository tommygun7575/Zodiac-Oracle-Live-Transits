import requests
import re

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"


def _parse(text):

    # Horizons ecliptic longitude / latitude pattern
    m = re.search(r"EclLon\s*=\s*([-0-9.]+).*?EclLat\s*=\s*([-0-9.]+)", text)

    if not m:
        return None

    lon = float(m.group(1))
    lat = float(m.group(2))

    return lon, lat


def fetch(body, jd):

    params = {
        "format": "text",
        "COMMAND": body,
        "EPHEM_TYPE": "OBSERVER",
        "CENTER": "500@399",
        "TLIST": jd,
        "QUANTITIES": "1,2"
    }

    try:

        r = requests.get(HORIZONS_URL, params=params, timeout=10)

        parsed = _parse(r.text)

        if not parsed:
            return None

        lon, lat = parsed

        return lon, lat, "horizons"

    except:
        return None


def fetch_numbered(number, jd):

    params = {
        "format": "text",
        "COMMAND": str(number),
        "EPHEM_TYPE": "OBSERVER",
        "CENTER": "500@399",
        "TLIST": jd,
        "QUANTITIES": "1,2"
    }

    try:

        r = requests.get(HORIZONS_URL, params=params, timeout=10)

        parsed = _parse(r.text)

        if not parsed:
            return None

        lon, lat = parsed

        return lon, lat, "horizons"

    except:
        return None
