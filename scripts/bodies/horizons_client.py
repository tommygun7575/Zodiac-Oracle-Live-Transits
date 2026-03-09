import requests

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

def fetch_ephemeris(body_id, start_date, stop_date, step_size="2d"):
    """
    Fetch geocentric ecliptic longitude from JPL Horizons.
    """

    # Sun must use barycenter
    center = "500@0" if body_id == "10" else "500@399"

    params = {
        "format": "json",
        "COMMAND": body_id,
        "MAKE_EPHEM": "YES",
        "EPHEM_TYPE": "OBSERVER",
        "CENTER": center,
        "START_TIME": start_date,
        "STOP_TIME": stop_date,
        "STEP_SIZE": step_size,
        "QUANTITIES": "4",      # ecliptic longitude
        "REF_SYSTEM": "ECLIPTIC",
        "OUT_UNITS": "DEG",
        "CSV_FORMAT": "YES"
    }

    response = requests.get(HORIZONS_URL, params=params)
    data = response.json()

    if "error" in data:
        raise RuntimeError(data["error"])

    if "result" not in data:
        raise RuntimeError("No result block from Horizons")

    lines = data["result"].splitlines()

    ephemeris = []
    capture = False

    for line in lines:

        if "$$SOE" in line:
            capture = True
            continue

        if "$$EOE" in line:
            break

        if capture:
            parts = [p.strip() for p in line.split(",")]

            if len(parts) >= 5:
                try:
                    date = parts[0]
                    lon = float(parts[4])
                    ephemeris.append({
                        "date": date,
                        "longitude_deg": lon
                    })
                except:
                    continue

    if not ephemeris:
        raise RuntimeError("No ephemeris rows parsed")

    return ephemeris
