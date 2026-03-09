import requests

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"


# Map numeric IDs to Horizons-recognized commands
MAJOR_BODY_NAMES = {
    "10": "Sun",
    "301": "Moon",
    "199": "Mercury",
    "299": "Venus",
    "499": "Mars",
    "599": "Jupiter",
    "699": "Saturn",
    "799": "Uranus",
    "899": "Neptune",
    "999": "Pluto"
}


def resolve_command(body_id: str) -> str:
    if body_id in MAJOR_BODY_NAMES:
        return MAJOR_BODY_NAMES[body_id]
    else:
        # Small bodies must use DES format
        return f"DES={body_id};"


def fetch_jpl(body_id, start_date, stop_date, step_size="2d"):

    command = resolve_command(body_id)

    params = {
        "format": "json",
        "COMMAND": command,
        "OBJ_DATA": "NO",
        "MAKE_EPHEM": "YES",
        "EPHEM_TYPE": "OBSERVER",
        "CENTER": "500@399",
        "START_TIME": start_date,
        "STOP_TIME": stop_date,
        "STEP_SIZE": step_size,
        "QUANTITIES": "2",
        "CSV_FORMAT": "YES"
    }

    r = requests.get(HORIZONS_URL, params=params, timeout=60)

    if r.status_code != 200:
        raise RuntimeError(f"JPL HTTP {r.status_code}")

    data = r.json()

    if "result" not in data:
        raise RuntimeError("JPL no ephemeris block")

    lines = data["result"].splitlines()

    ephemeris = {}
    capture = False

    for line in lines:

        if "$$SOE" in line:
            capture = True
            continue

        if "$$EOE" in line:
            break

        if not capture:
            continue

        line = line.strip()

        if not line:
            continue

        parts = line.split(",")

        if len(parts) < 2:
            continue

        try:
            date_str = parts[0].strip().split()[0]
            lon = float(parts[1].strip())

            ephemeris[date_str] = lon

        except Exception:
            continue

    if not ephemeris:
        raise RuntimeError("JPL parsed zero rows")

    return ephemeris
