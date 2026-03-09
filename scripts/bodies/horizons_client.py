import requests

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

def fetch_ephemeris(body_id, start_date, stop_date, step_size="2d"):

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
        "QUANTITIES": "1",
        "ANG_FORMAT": "DEG",
        "CSV_FORMAT": "YES"
    }

    response = requests.get(HORIZONS_URL, params=params, timeout=30)

    if response.status_code != 200:
        raise RuntimeError(f"Horizons HTTP error {response.status_code}")

    data = response.json()

    if "error" in data:
        raise RuntimeError(data["error"])

    if "result" not in data:
        raise RuntimeError("No result block")

    lines = data["result"].splitlines()

    header_index = None
    lon_index = None
    ephemeris = []
    capture = False

    # Find header row
    for i, line in enumerate(lines):
        if "Date__(UT)__HR:MN" in line:
            header_index = i
            headers = [h.strip() for h in line.split(",")]

            for idx, col in enumerate(headers):
                if "EclLon" in col or "ObsEcLon" in col:
                    lon_index = idx
                    break
            break

    if lon_index is None:
        raise RuntimeError("Longitude column not found in Horizons output")

    # Parse data rows
    for line in lines:

        if "$$SOE" in line:
            capture = True
            continue

        if "$$EOE" in line:
            break

        if capture:
            parts = [p.strip() for p in line.split(",")]

            if len(parts) > lon_index:
                try:
                    date = parts[0]
                    lon = float(parts[lon_index])
                    ephemeris.append({
                        "date": date,
                        "longitude_deg": lon
                    })
                except:
                    continue

    if not ephemeris:
        raise RuntimeError("Parsed zero rows from Horizons response")

    return ephemeris
