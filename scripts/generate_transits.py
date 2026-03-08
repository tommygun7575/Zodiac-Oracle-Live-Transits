import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import swisseph as swe
import time

# Define the URLs for the services
HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"
MIRIADE_URL = "https://ssp.imcce.fr/webservices/miriade/api/ephemcc.php"

# Set ephemeris path once at module level
swe.set_ephe_path(".")

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
    "Pluto": swe.PLUTO,
    "Ceres": swe.AST_OFFSET + 1,
    "Pallas": swe.AST_OFFSET + 2,
    "Juno": swe.AST_OFFSET + 3,
    "Vesta": swe.AST_OFFSET + 4,
}

# Parse Horizons plain-text CSV response using fixed column indices
def parse_horizons(text):
    rows = []
    reading = False

    for line in text.splitlines():
        if "$$SOE" in line:
            reading = True
            continue
        if "$$EOE" in line:
            break
        if reading:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 5:
                continue
            try:
                lon = float(parts[3])
                lat = float(parts[4])
                rows.append((lon, lat))
            except (ValueError, IndexError):
                continue

    return rows

# Fetch data from JPL Horizons
def fetch_jpl(body_id, start, stop):
    params = {
        "format": "text",
        "COMMAND": body_id,
        "EPHEM_TYPE": "OBSERVER",
        "CENTER": "500@399",
        "START_TIME": start,
        "STOP_TIME": stop,
        "STEP_SIZE": "1 d",
        "QUANTITIES": "18,20",
        "CSV_FORMAT": "YES",
        "ANG_FORMAT": "DEG"
    }

    for attempt in range(2):
        r = requests.get(HORIZONS_URL, params=params, timeout=20)
        if r.status_code == 200:
            rows = parse_horizons(r.text)
            if rows:
                return rows
        if attempt < 1:
            time.sleep(2)

    raise RuntimeError("JPL request failed")

# Fetch data from Miriade (single batched request for all 7 days)
def fetch_miriade(body, start_date):
    params = {
        "name": body,
        "type": "object",
        "epoch": start_date.strftime("%Y-%m-%dT00:00:00"),
        "nbd": 7,
        "step": "1d",
        "observer": "500",
        "mime": "json"
    }

    r = requests.get(MIRIADE_URL, params=params, timeout=30)

    if r.status_code != 200:
        raise RuntimeError("Miriade request failed")

    data = r.json()
    entries = data.get("data", [])
    results = []
    for entry in entries[:7]:
        try:
            lon = float(entry["EclLon"])
            lat = float(entry["EclLat"])
        except (KeyError, IndexError, TypeError, ValueError) as e:
            raise RuntimeError(f"Miriade response parse failed: {e}")
        results.append((lon, lat))
    return results

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
    body_id = BODIES.get(body)

    if body_id is None:
        raise RuntimeError(f"No JPL body id configured for {body}")

    try:
        rows = fetch_jpl(body_id, start, stop)
        return [{"lon": lon, "lat": lat, "source": "JPL"} for lon, lat in rows]
    except Exception as e:
        print(f"[WARN] JPL failed for {body}: {e}")

    try:
        rows = fetch_miriade(body, start_date)
        return [{"lon": lon, "lat": lat, "source": "Miriade"} for lon, lat in rows]
    except Exception as e:
        print(f"[WARN] Miriade failed for {body}: {e}")

    results = []
    for i in range(7):
        date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        try:
            lon, lat = fetch_swiss(body, date)
            results.append({"lon": lon, "lat": lat, "source": "Swiss"})
        except Exception as e:
            print(f"[WARN] All sources failed for {body} on {date}: {e}")
            results.append({"lon": None, "lat": None, "source": "none"})

    return results

# Calculate Arabic Parts
def calc_arabic_parts(data):
    parts = []
    for i in range(7):
        try:
            sun = data["Sun"][i]["lon"]
            moon = data["Moon"][i]["lon"]
            if sun is None or moon is None:
                parts.append({"part_of_fortune": None})
            else:
                fortune = (moon - sun) % 360
                parts.append({"part_of_fortune": fortune})
        except Exception as e:
            print(f"[WARN] arabic_parts calculation failed at index {i}: {e}")
            parts.append({"part_of_fortune": None})
    return parts

# Calculate Harmonics
def calc_harmonics(data):
    harmonics = []
    for i in range(7):
        try:
            sun = data["Sun"][i]["lon"]
            if sun is None:
                harmonics.append({"sun_h5": None, "sun_h7": None})
            else:
                harmonics.append({
                    "sun_h5": (sun * 5) % 360,
                    "sun_h7": (sun * 7) % 360
                })
        except Exception as e:
            print(f"[WARN] harmonics calculation failed at index {i}: {e}")
            harmonics.append({"sun_h5": None, "sun_h7": None})
    return harmonics

# Main function to generate weekly ephemeris
def main():
    start_date = datetime.utcnow()
    bodies = {}

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        for body in BODIES:
            print(f"Resolving {body}")
            futures[executor.submit(resolve_body, body, start_date)] = body
        for future in as_completed(futures):
            body = futures[future]
            try:
                bodies[body] = future.result()
            except Exception as e:
                print(f"[ERROR] Failed to resolve {body}: {e}")
                bodies[body] = []

    data = {
        "generated": datetime.utcnow().isoformat(),
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
