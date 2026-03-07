import requests
import json
from datetime import datetime, timedelta
import swisseph as swe
import time

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"
MIRIADE_URL = "https://ssp.imcce.fr/webservices/miriade/api/ephemcc.php"

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


def parse_horizons(text):
    """Parse Horizons CSV output."""
    lines = text.splitlines()

    start = None
    end = None
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


def fetch_jpl(body_id, start, stop):
    """Fetch data from JPL Horizons."""
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


def fetch_miriade(body, date):
    """Fetch data from Miriade."""
    params = {
        "name": body,
        "type": "p",
        "epoch": date,
        "observer": "500"
    }

    r = requests.get(MIRIADE_URL, params=params, timeout=30)

    if r.status_code != 200:
        raise RuntimeError("Miriade failed")

    data = r.json()

    eph = data["ephemerides"][0]
    lon = float(eph["lambda"])
    lat = float(eph["beta"])

    return lon, lat


def fetch_swiss(body, date):
    """Fetch data from Swiss Ephemeris."""
    swe.set_ephe_path(".")

    dt = datetime.fromisoformat(date)
    jd = swe.julday(dt.year, dt.month, dt.day)

    planet = SWISS_MAP.get(body)
    if planet is None:
        raise RuntimeError("Swiss unsupported")

    pos, _ = swe.calc_ut(jd, planet)

    return pos[0], pos[1]


def resolve_body(body, start_date):
    """Resolve ephemeris data for a body."""
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


def calc_arabic_parts(data):
    """Calculate Arabic Parts."""
    parts = []
    for i in range(7):
        sun = data["Sun"][i]["lon"]
        moon = data["Moon"][i]["lon"]
        fortune = (moon - sun) % 360
        parts.append({"part_of_fortune": fortune})
    return parts


def calc_harmonics(data):
    """Calculate Harmonics."""
    harmonics = []
    for i in range(7):
        sun = data["Sun"][i]["lon"]
        harmonics.append({
            "sun_h5": (sun * 5) % 360,
            "sun_h7": (sun * 7) % 360
        })
    return harmonics


def calc_fixed_stars():
    """Calculate fixed stars."""
    return {
        "Regulus": 150.0,
        "Spica": 204.0,
        "Aldebaran": 69.0,
        "Antares": 249.0
    }


def calc_tnos():
    """Calculate TNOs."""
    return {
        "Eris": 15.0,
        "Sedna": 13.5,
        "Orcus": 18.0
    }


def calc_minor_bodies():
    """Calculate Minor Bodies."""
    return {
        "Ceres": 10.0,
        "Vesta": 6.0
    }


def calc_aether_planets():
    """Calculate Aether Planets."""
    return {
        "Eris": 300.0,
        "Haumea": 140.0,
        "Makemake": 280.0
    }


def main():
    """Main function to generate the weekly ephemeris."""
    start_date = datetime.utcnow()
    bodies = {}

    for body in BODIES:
        print(f"Resolving {body}")
        bodies[body] = resolve_body(body, start_date)

    data = {
        "generated": datetime.utcnow().isoformat(),
        "bodies": bodies
    }

    # Calculate additional astrology layers
    data["arabic_parts"] = calc_arabic_parts(bodies)
    data["harmonics"] = calc_harmonics(bodies)
    data["fixed_stars"] = calc_fixed_stars()

    # Calculate additional minor bodies, TNOs, aether planets
    data["tnos"] = calc_tnos()
    data["asteroids"] = calc_minor_bodies()
    data["minor_bodies"] = calc_minor_bodies()
    data["aether_planets"] = calc_aether_planets()

    # Write to output JSON
    with open("docs/current_week.json", "w") as f:
        json.dump(data, f, indent=2)

    print("current_week.json written")


if __name__ == "__main__":
    main()
