import requests

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

def fetch_ephemeris(body_id, start_date, stop_date, step_size="2d"):

    center = "500@0" if body_id == "10" else "500@399"

    params = {
        "format": "text",
        "COMMAND": body_id,
        "MAKE_EPHEM": "YES",
        "TABLE_TYPE": "OBSERVER",
        "EPHEM_TYPE": "OBSERVER",
        "CENTER": center,
        "START_TIME": start_date,
        "STOP_TIME": stop_date,
        "STEP_SIZE": step_size,
        "QUANTITIES": "1",
        "CSV_FORMAT": "YES"
    }

    response = requests.get(HORIZONS_URL, params=params, timeout=30)

    if response.status_code != 200:
        raise RuntimeError(f"Horizons HTTP error {response.status_code}")

    text = response.text

    if "$$SOE" not in text:
        raise RuntimeError("Horizons did not generate ephemeris table")

    lines = text.splitlines()

    ephemeris = []
    capture = False

    for line in lines:

        if "$$SOE" in line:
            capture = True
            continue

        if "$$EOE" in line:
            break

        if capture:
            parts = line.split(",")

            if len(parts) >= 2:
                try:
                    date = parts[0].strip()
                    lon = float(parts[1].strip())
                    ephemeris.append({
                        "date": date,
                        "longitude_deg": lon
                    })
                except:
                    continue

    if not ephemeris:
        raise RuntimeError("Parsed zero ephemeris rows")

    return ephemeris
