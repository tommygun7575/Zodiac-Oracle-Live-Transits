import requests
import json
from datetime import datetime, timedelta
import swisseph as swe
import math

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
    "Pluto": "999"
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

    rows = []
    reading = False

    for line in text.splitlines():

        if "$$SOE" in line:
            reading = True
            continue

        if "$$EOE" in line:
            break

        if reading:
            parts = [x.strip() for x in line.split(",")]

            try:
                lon = float(parts[3])
                lat = float(parts[4])
                rows.append((lon, lat))
            except:
                continue

    return rows


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

    r = requests.get(HORIZONS_URL, params=params, timeout=30)

    if r.status_code != 200:
        raise RuntimeError("JPL request failed")

    data = r.json()

    rows = parse_horizons(data["result"])

    if not rows:
        raise RuntimeError("JPL returned empty")

    return rows


def fetch_miriade(body, date):

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

    swe.set_ephe_path(".")

    dt = datetime.fromisoformat(date)
    jd = swe.julday(dt.year, dt.month, dt.day)

    planet = SWISS_MAP.get(body)

    if planet is None:
        raise RuntimeError("Swiss unsupported")

    pos, _ = swe.calc_ut(jd, planet)

    return pos[0], pos[1]


def resolve_body(body, start_date):

    start = start_date.strftime("%Y-%m-%d")
    stop = (start_date + timedelta(days=6)).strftime("%Y-%m-%d")

    try:

        rows = fetch_jpl(BODIES[body], start, stop)

        return [
            {"lon": lon, "lat": lat, "source": "JPL"}
            for lon, lat in rows
        ]

    except Exception as e:

        print(f"[WARN] JPL failed for {body}: {e}")

    results = []

    for i in range(7):

        date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")

        try:

            lon, lat = fetch_miriade(body, date)

            results.append({
                "lon": lon,
                "lat": lat,
                "source": "Miriade"
            })

        except:

            lon, lat = fetch_swiss(body, date)

            results.append({
                "lon": lon,
                "lat": lat,
                "source": "Swiss"
            })

    return results


def calc_arabic_parts(data):

    parts = []

    for i in range(7):

        sun = data["Sun"][i]["lon"]
        moon = data["Moon"][i]["lon"]

        fortune = (moon - sun) % 360

        parts.append({
            "part_of_fortune": fortune
        })

    return parts


def calc_harmonics(data):

    harmonics = []

    for i in range(7):

        sun = data["Sun"][i]["lon"]

        harmonics.append({
            "sun_h5": (sun * 5) % 360,
            "sun_h7": (sun * 7) % 360
        })

    return harmonics


def calc_fixed_stars():

    return {
        "Regulus": 150.0,
        "Spica": 204.0,
        "Aldebaran": 69.0,
        "Antares": 249.0
    }


def main():

    start_date = datetime.utcnow()

    bodies = {}

    for body in BODIES:

        print("Resolving", body)

        bodies[body] = resolve_body(body, start_date)

    data = {
        "generated": datetime.utcnow().isoformat(),
        "bodies": bodies
    }

    data["arabic_parts"] = calc_arabic_parts(bodies)

    data["harmonics"] = calc_harmonics(bodies)

    data["fixed_stars"] = calc_fixed_stars()

    data["tnos"] = {}
    data["asteroids"] = {}
    data["minor_bodies"] = {}
    data["aether_planets"] = {}

    with open("docs/current_week.json", "w") as f:

        json.dump(data, f, indent=2)

    print("current_week.json written")


if __name__ == "__main__":
    main()
