import requests

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

def fetch_ephemeris(body_id, start_date, stop_date, step_size="2d"):

    params = {
        "format": "json",
        "COMMAND": body_id,
        "MAKE_EPHEM": "YES",
        "EPHEM_TYPE": "VECTORS",
        "CENTER": "@0",
        "REF_PLANE": "ECLIPTIC",
        "REF_SYSTEM": "J2000",
        "START_TIME": start_date,
        "STOP_TIME": stop_date,
        "STEP_SIZE": step_size,
        "VEC_TABLE": "3",
        "OUT_UNITS": "AU-D",
        "CSV_FORMAT": "YES"
    }

    response = requests.get(HORIZONS_URL, params=params, timeout=60)

    if response.status_code != 200:
        raise RuntimeError(f"Horizons HTTP error {response.status_code}")

    data = response.json()

    if "result" not in data:
        raise RuntimeError("Horizons did not return result block")

    lines = data["result"].splitlines()

    capture = False
    ephemeris = []

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
                    date = parts[0].split()[0]
                    x = float(parts[2])
                    y = float(parts[3])

                    # Convert vector to ecliptic longitude
                    import math
                    lon = math.degrees(math.atan2(y, x)) % 360

                    ephemeris.append({
                        "date": date,
                        "longitude_deg": lon
                    })

                except:
                    continue

    if not ephemeris:
        raise RuntimeError("No ephemeris rows parsed")

    return ephemeris
