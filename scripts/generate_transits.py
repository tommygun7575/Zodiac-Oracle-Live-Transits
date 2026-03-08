import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import swisseph as swe
import time

# Define the URLs for the services
HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"
MIRIADE_URL = "https://ssp.imcce.fr/webservices/miriade/api/ephemcc.php"

# Define the celestial bodies and their IDs
BODIES = {
    "Sun": "10",
    "Moon": "301",
    "Mercury": "199",
    "Venus": "299",
    "Mars": "499",
    "Jupiter": "599",
    "Saturn": "699",
    "Uranus": "799",
    "Neptune": "899",
    "Pluto": "999",
    "Ceres": "1",
    "Pallas": "2",
    "Juno": "3",
    "Vesta": "4",
    "Eris": "136199",
    "Sedna": "90377",
    "Orcus": "90482",
    "Makemake": "136472",
    "Haumea": "136108",
    "Quaoar": "50000",
    "Ixion": "28978"
}

# Initialise Swiss Ephemeris path once at module load
swe.set_ephe_path(".")

# Swiss Ephemeris constants
SWISS_MAP = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO
}

# Parse Horizons API response
def parse_horizons(text):
    lines = text.splitlines()
    start, end = None, None

    for i, line in enumerate(lines):
        if "$$SOE" in line:
            start = i + 1
        if "$$EOE" in line:
            end = i
            break

    header_line = None
    for line in lines:
        if "EclLon" in line and "EclLat" in line:
            header_line = line
            break

    if not header_line:
        raise RuntimeError("Could not locate Horizons header")

    headers = [h.strip() for h in header_line.split(",")]

    lon_index = headers.index("EclLon")
    lat_index = headers.index("EclLat")

    rows = []
    for line in lines[start:end]:
        parts = [p.strip() for p in line.split(",")]
        try:
            lon = float(parts[lon_index])
            lat = float(parts[lat_index])
            rows.append((lon, lat))
        except:
            continue

    return rows

# Fetch data from JPL Horizons
def fetch_jpl(body_id, start, stop):
    params = {
        "format": "json",
        "COMMAND": body_id,
        "EPHEM_TYPE": "OBSERVER",
        "CENTER": "500@399",
        "START_TIME": start,
        "STOP_TIME": stop,
        "STEP_SIZE": "1 d",
        "QUANTITIES": "18,20",
        "CSV_FORMAT": "YES"
    }

    retries = 3
    for _ in range(retries):
        r = requests.get(HORIZONS_URL, params=params, timeout=30)
        if r.status_code == 200:
            data = r.json()
            text = data.get("result")
            if not text:
                raise RuntimeError("Malformed JPL response")
            return parse_horizons(text)

        time.sleep(2)

    raise RuntimeError("JPL request failed")

# Fetch data from Miriade
def fetch_miriade(body, date):
    params = {
        "name": body,
        "type": "p",
        "epoch": date,
        "observer": "500"
    }

    r = requests.get(MIRIADE_URL, params=params, timeout=30)

    if r.status_code != 200:
        raise RuntimeError("Miriade request failed")

    data = r.json()
    eph = data["ephemerides"][0]
    lon = float(eph["lambda"])
    lat = float(eph["beta"])

    return lon, lat

# Fetch data from Swiss Ephemeris
def fetch_swiss(body, date):
    dt = datetime.fromisoformat(date)
    jd = swe.julday(dt.year, dt.month, dt.day)

    planet = SWISS_MAP.get(body)
    if planet is None:
        raise RuntimeError("Swiss unsupported body")

    pos, _ = swe.calc_ut(jd, planet)

    return pos[0], pos[1]

# Resolve body data using JPL, Miriade, and Swiss fallback
def resolve_body(body, start_date):
    start = start_date.strftime("%Y-%m-%d")
    stop = (start_date + timedelta(days=6)).strftime("%Y-%m-%d")

    try:
        rows = fetch_jpl(BODIES[body], start, stop)
        return [{"lon": lon, "lat": lat, "source": "JPL"} for lon, lat in rows]
    except Exception as e:
        print(f"[WARN] JPL failed for {body}: {e}")

    results = []
    for i in range(7):
        date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        try:
            lon, lat = fetch_miriade(body, date)
            results.append({"lon": lon, "lat": lat, "source": "Miriade"})
        except Exception:
            lon, lat = fetch_swiss(body, date)
            results.append({"lon": lon, "lat": lat, "source": "Swiss"})

    return results

# Calculate Arabic Parts
def calc_arabic_parts(data):
    parts = []
    for i in range(7):
        sun = data["Sun"][i]["lon"]
        moon = data["Moon"][i]["lon"]
        fortune = (moon - sun) % 360
        parts.append({"part_of_fortune": fortune})
    return parts

# Calculate Harmonics
def calc_harmonics(data):
    harmonics = []
    for i in range(7):
        sun = data["Sun"][i]["lon"]
        harmonics.append({
            "sun_h5": (sun * 5) % 360,
            "sun_h7": (sun * 7) % 360
        })
    return harmonics

# Main function to generate weekly ephemeris
def main():
    start_date = datetime.utcnow()
    bodies = {}

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(resolve_body, body, start_date): body for body in BODIES}
        for future in as_completed(futures):
            body = futures[future]
            try:
                bodies[body] = future.result()
                print(f"Resolved {body}")
            except Exception as e:
                print(f"[ERROR] Failed to resolve {body}: {e}")

    data = {
        "generated": start_date.isoformat(),
        "bodies": bodies
    }

    # Calculate additional astrology layers
    data["arabic_parts"] = calc_arabic_parts(bodies)
    data["harmonics"] = calc_harmonics(bodies)

    # Write to output JSON
    with open("docs/current_week.json", "w") as f:
        json.dump(data, f, indent=2)

    print("current_week.json written")


if __name__ == "__main__":
    main()
