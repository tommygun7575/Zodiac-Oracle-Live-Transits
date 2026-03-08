import json
import datetime
import os

from scripts.bodies.horizons_client import fetch_horizons


PLANETS = [
    "Sun","Moon","Mercury","Venus","Mars",
    "Jupiter","Saturn","Uranus","Neptune","Pluto"
]


def zodiac(lon):

    signs = [
        "Aries","Taurus","Gemini","Cancer",
        "Leo","Virgo","Libra","Scorpio",
        "Sagittarius","Capricorn","Aquarius","Pisces"
    ]

    s = int(lon / 30)

    return signs[s], lon % 30


def generate():

    today = datetime.date.today()
    week_later = today + datetime.timedelta(days=7)

    start = today.isoformat()
    stop = week_later.isoformat()

    bodies = {}

    for planet in PLANETS:

        data = fetch_horizons(planet, start, stop)

        if not data:
            continue

        lon = data[0]["lon"] % 360

        sign,deg = zodiac(lon)

        bodies[planet] = {
            "lon": round(lon,6),
            "sign": sign,
            "degree": round(deg,6)
        }

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
