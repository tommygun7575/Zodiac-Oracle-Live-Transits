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
    "Aries","Taurus","Gemini","Cancer",
    "Leo","Virgo","Libra","Scorpio",
    "Sagittarius","Capricorn","Aquarius","Pisces"
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

    bodies = {}

    for planet in PLANETS:

        try:

            print(f"Fetching {planet}")

            data = fetch_horizons(planet, start, stop)

            time.sleep(1)

            if not data:
                print(f"{planet} returned no data")
                continue

            lon = data[0]["lon"] % 360

            sign, degree = zodiac(lon)

            bodies[planet] = {
                "lon": round(lon, 6),
                "sign": sign,
                "degree": round(degree, 6)
            }

        except Exception as e:

            print(f"{planet} failed: {e}")
            continue


    output = {
        "generated_utc": datetime.datetime.utcnow().isoformat(),
        "bodies": bodies
    }

    os.makedirs("docs", exist_ok=True)

    with open("docs/current_week.json", "w") as f:
        json.dump(output, f, indent=2)

    print("Generated docs/current_week.json")


if __name__ == "__main__":
    generate()
