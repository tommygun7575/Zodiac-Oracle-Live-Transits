import requests
import json
from datetime import datetime, timedelta
import swisseph as swe

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

    if "result" not in data:
        raise RuntimeError("Malformed JPL response")

    rows = parse_horizons(data["result"])

    if not rows:
        raise RuntimeError("JPL returned empty data")

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
        raise RuntimeError("Miriade request failed")

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
        raise RuntimeError("Swiss unsupported body")

    pos, _ = swe.calc_ut(jd, planet)

    lon = pos[0]
    lat = pos[1]

    return lon, lat


def resolve_body(body, start_date):

    start = start_date.strftime("%Y-%m-%d")
    stop = (start_date + timedelta(days=6)).strftime("%Y-%m-%d")

    results = []

    try:

        rows = fetch_jpl(BODIES[body], start, stop)

        for lon, lat in rows:
            results.append({
                "lon": lon,
                "lat": lat,
                "source": "JPL"
            })

        print(f"[OK] {body} via JPL")

        return results

    except Exception as e:

        print(f"[WARN] JPL failed for {body}: {e}")


    for i in range(7):

        date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")

        try:

            lon, lat = fetch_miriade(body, date)

            results.append({
                "lon": lon,
                "lat": lat,
                "source": "Miriade"
            })

            print(f"[OK] {body} via Miriade")

        except Exception:

            try:

                lon, lat = fetch_swiss(body, date)

                results.append({
                    "lon": lon,
                    "lat": lat,
                    "source": "Swiss"
                })

                print(f"[OK] {body} via Swiss")

            except Exception:

                raise RuntimeError(f"No data for {body}")

    return results


def main():

    start_date = datetime.utcnow()

    output = {
        "generated": datetime.utcnow().isoformat(),
        "bodies": {}
    }

    for body in BODIES.keys():

        output["bodies"][body] = resolve_body(body, start_date)

    with open("docs/current_week.json", "w") as f:

        json.dump(output, f, indent=2)

    print("current_week.json written")


if __name__ == "__main__":
    main()
