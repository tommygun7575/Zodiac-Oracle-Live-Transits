import requests

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"


def fetch_horizons(body):

    params = {
        "format": "json",
        "COMMAND": body,
        "EPHEM_TYPE": "OBSERVER",
        "CENTER": "500@399",
        "STEP_SIZE": "1d",
        "QUANTITIES": "18"
    }

    r = requests.get(HORIZONS_URL, params=params, timeout=30)

    if r.status_code != 200:
        raise RuntimeError(f"Horizons request failed for {body} with status {r.status_code}")

    data = r.json()

    if "result" not in data:
        raise RuntimeError("Malformed Horizons response")

    text = data["result"]

    for line in text.split("\n"):

        stripped = line.strip()
        if "," in stripped and stripped[0].isdigit():

            parts = stripped.split(",")
            if len(parts) <= 4:
                continue

            lon = float(parts[4])

            return {"lon": lon}

    raise RuntimeError(f"No ephemeris found for {body}")
