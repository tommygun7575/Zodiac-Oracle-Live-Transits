import requests


HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"


def fetch_ephemeris(body_id, start_date, stop_date, step_size="2d"):
    """
    Fetch heliocentric ecliptic longitude from JPL Horizons.
    """

    # Sun must use barycenter as center
    center = "500@0" if body_id == "10" else "500@399"

    params = {
        "format": "json",
        "COMMAND": body_id,
        "EPHEM_TYPE": "OBSERVER",
        "CENTER": center,
        "START_TIME": start_date,
        "STOP_TIME": stop_date,
        "STEP_SIZE": step_size,
        "QUANTITIES": "1",   # Ecliptic longitude
        "ANG_FORMAT": "DEG",
        "CSV_FORMAT": "YES"
    }

    response = requests.get(HORIZONS_URL, params=params)
    data = response.json()

    if "error" in data:
        raise RuntimeError(f"Horizons API error: {data['error']}")

    if "result" not in data:
        raise RuntimeError("Horizons returned no result block")

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

            if len(parts) >= 2:
                try:
                    date = parts[0]
                    lon = float(parts[1])
                    ephemeris.append({
                        "date": date,
                        "longitude_deg": lon
                    })
                except ValueError:
                    continue

    if not ephemeris:
        raise RuntimeError("No ephemeris rows parsed from Horizons")

    return ephemeris
