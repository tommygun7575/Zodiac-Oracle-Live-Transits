import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import swisseph as swe
import time

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"
MIRIADE_URL = "https://ssp.imcce.fr/webservices/miriade/api/ephemcc.php"

swe.set_ephe_path(".")


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
    "Ceres": "1;",
    "Pallas": "2;",
    "Juno": "3;",
    "Vesta": "4;",
    "Eris": "136199;",
    "Sedna": "90377;",
    "Orcus": "90482;",
    "Makemake": "136472;",
    "Haumea": "136108;",
    "Quaoar": "50000;",
    "Ixion": "28978;"
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
    "Pluto": swe.PLUTO,
    "Ceres": swe.AST_OFFSET + 1,
    "Pallas": swe.AST_OFFSET + 2,
    "Juno": swe.AST_OFFSET + 3,
    "Vesta": swe.AST_OFFSET + 4,
}


JPL_CACHE = {}


def parse_horizons(text):

    rows = []
    reading = False

    for line in text.splitlines():

        if "$$SOE" in line:
            reading = True
            continue

        if "$$EOE" in line:
            break

        if not reading:
            continue

        line = line.strip()

        if not line:
            continue

        if "," in line:
            parts = [p.strip() for p in line.split(",")]
        else:
            parts = line.split()

        numeric = []

        for p in parts:
            try:
                numeric.append(float(p))
            except ValueError:
                pass

        if len(numeric) >= 2:
            lon = numeric[-2]
            lat = numeric[-1]
            rows.append((lon, lat))

    if not rows:
        raise RuntimeError("Horizons parse returned no rows")

    return rows


def fetch_jpl(body_id, start, stop):

    cache_key = f"{body_id}_{start}"

    if cache_key in JPL_CACHE:
        return JPL_CACHE[cache_key]

    params = {
        "format": "text",
        "COMMAND": body_id,
        "EPHEM_TYPE": "OBSERVER",
        "CENTER": "500@399",
        "START_TIME": start,
        "STOP_TIME": stop,
        "STEP_SIZE": "1 d",
        "QUANTITIES": "31",
        "CSV_FORMAT": "YES",
        "ANG_FORMAT": "DEG"
    }

    for attempt in range(3):

        r = requests.get(HORIZONS_URL, params=params, timeout=30)

        if r.status_code == 200:

            try:

                rows = parse_horizons(r.text)

                if rows:
                    JPL_CACHE[cache_key] = rows
                    return rows

            except Exception as e:
                print(f"[WARN] Horizons parse error: {e}")

        time.sleep(2)

    raise RuntimeError("JPL request failed")


def fetch_miriade(body, start_date):

    params = {
        "name": body,
        "type": "object",
        "epoch": start_date.strftime("%Y-%m-%dT00:00:00"),
        "nbd": 7,
        "step": "1d",
        "observer": "500",
        "tcoor": "2",
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
        except Exception:
            results.append((None, None))
            continue

        results.append((lon, lat))

    while len(results) < 7:
        results.append((None, None))

    return results


def fetch_swiss(body, date):

    dt = datetime.fromisoformat(date)
    jd = swe.julday(dt.year, dt.month, dt.day)

    planet = SWISS_MAP.get(body)

    if planet is None:
        raise RuntimeError("Swiss unsupported body")

    pos, _ = swe.calc_ut(jd, planet)

    return pos[0], pos[1]


def _missing_indices(results):
    return [i for i, r in enumerate(results) if r["lon"] is None]


def resolve_body(body, start_date):

    start = start_date.strftime("%Y-%m-%d")
    stop = (start_date + timedelta(days=6)).strftime("%Y-%m-%d")

    body_id = BODIES.get(body)

    results = [{"lon": None, "lat": None, "source": "none"} for _ in range(7)]

    if body_id:

        try:

            rows = fetch_jpl(body_id, start, stop)

            for i, (lon, lat) in enumerate(rows[:7]):
                results[i] = {"lon": lon, "lat": lat, "source": "JPL"}

        except Exception as e:
            print(f"[WARN] JPL failed for {body}: {e}")

    missing = _missing_indices(results)

    if missing:

        try:

            rows = fetch_miriade(body, start_date)

            for i, (lon, lat) in enumerate(rows[:7]):

                if i in missing and lon is not None:
                    results[i] = {"lon": lon, "lat": lat, "source": "Miriade"}

        except Exception as e:
            print(f"[WARN] Miriade failed for {body}: {e}")

    for i in _missing_indices(results):

        date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")

        try:

            lon, lat = fetch_swiss(body, date)

            results[i] = {"lon": lon, "lat": lat, "source": "Swiss"}

        except Exception as e:
            print(f"[WARN] All sources failed for {body} on {date}: {e}")

    return results


def calc_arabic_parts(data):

    parts = []

    for i in range(7):

        try:

            sun = data["Sun"][i]["lon"]
            moon = data["Moon"][i]["lon"]

            if sun is None or moon is None:
                parts.append({"part_of_fortune": None})
            else:
                parts.append({"part_of_fortune": (moon - sun) % 360})

        except:
            parts.append({"part_of_fortune": None})

    return parts


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

        except:
            harmonics.append({"sun_h5": None, "sun_h7": None})

    return harmonics


def main():

    start_date = datetime.utcnow()

    bodies = {}

    with ThreadPoolExecutor(max_workers=3) as executor:

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

    data["arabic_parts"] = calc_arabic_parts(bodies)
    data["harmonics"] = calc_harmonics(bodies)

    with open("docs/current_week.json", "w") as f:
        json.dump(data, f, indent=2)

    print("current_week.json written")


if __name__ == "__main__":
    main()
