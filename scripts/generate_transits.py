import json
import datetime
import os
import time

from scripts.bodies.horizons_client import fetch_horizons


PLANETS = [
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto"
]


SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces"
]


def zodiac(lon):

    lon = lon % 360
    sign_index = int(lon // 30)
    degree = lon % 30

    return SIGNS[sign_index], degree


def generate():

    today = datetime.date.today()
    week_later = today + datetime.timedelta(days=7)

    start = today.isoformat()
    stop = week_later.isoformat()

    print(f"Generating weekly transits {start} → {stop}")

    bodies = {}

    for planet in PLANETS:

        try:

            print(f"Requesting {planet} from Horizons")

            data = fetch_horizons(planet, start, stop)

            # prevent JPL API rate limit
            time.sleep(1)

            if not data or len(data) == 0:
                print(f"{planet} returned no data")
                continue

            lon = data[0].get("lon")

            if lon is None:
                print(f"{planet} longitude missing")
                continue

            lon = lon % 360

            sign, degree = zodiac(lon)

            bodies[planet] = {
                "lon": round(lon, 6),
                "sign": sign,
                "degree": round(degree, 6)
            }

            print(f"{planet} OK")

        except Exception as e:

            print(f"{planet} failed: {e}")

            continue

    output = {
        "generated_utc": datetime.datetime.utcnow().isoformat(),
        "bodies": bodies
    }

    os.makedirs("docs", exist_ok=True)

    output_path = "docs/current_week.json"

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Weekly overlay written to {output_path}")


if __name__ == "__main__":
    generate()
