import requests

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"


def fetch_ephemeris(body_id, start, stop, step_size):

    params = {
        "format": "json",
        "COMMAND": body_id,
        "EPHEM_TYPE": "OBSERVER",
        "CENTER": "500@399",
        "START_TIME": start,
        "STOP_TIME": stop,
        "STEP_SIZE": step_size,
        "QUANTITIES": "18",
        "CSV_FORMAT": "YES"
    }

    response = requests.get(HORIZONS_URL, params=params, timeout=60)
    data = response.json()

    if "error" in data:
        raise RuntimeError(data["error"])

    return parse_ephemeris(data["result"])


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
            parts = line.split(",")
            date = parts[0].strip()

            # Normalize longitude immediately
            lon = float(parts[3].strip()) % 360.0

            rows.append({
                "date": date,
                "longitude_deg": lon
            })

    return rows
