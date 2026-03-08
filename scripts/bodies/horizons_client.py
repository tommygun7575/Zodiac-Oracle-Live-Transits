import requests

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"


def fetch_horizons(body):

    params = {
        "format": "json",
        "COMMAND": body,
        "EPHEM_TYPE": "OBSERVER",
        "CENTER": "500@399",
        "STEP_SIZE": "1d",
        "QUANTITIES": "18,20",
        "CSV_FORMAT": "YES"
    }

    r = requests.get(HORIZONS_URL, params=params, timeout=30)

    if r.status_code != 200:
        raise RuntimeError("Horizons request failed")

    data = r.json()

    if "result" not in data:
        raise RuntimeError("Malformed Horizons response")

    text = data["result"]

    reading = False

    for line in text.splitlines():

        if "$$SOE" in line:
            reading = True
            continue

        if "$$EOE" in line:
            break

        if reading:

            parts = line.split(",")

            if len(parts) > 4:

                lon = float(parts[4])

                return {"lon": lon}

    raise RuntimeError("No longitude found")
