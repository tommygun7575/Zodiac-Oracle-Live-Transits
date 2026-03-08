import json
import datetime
import os

from scripts.bodies.horizons_client import fetch_horizons
from scripts.bodies.miriade_client import fetch_miriade
from scripts.bodies.mpc_client import fetch_mpc


PLANETS = [
"Sun","Moon","Mercury","Venus","Mars",
"Jupiter","Saturn","Uranus","Neptune","Pluto"
]


def normalize(lon):
    return lon % 360


def fetch_body(body):

    try:
        return fetch_horizons(body)
    except Exception:
        pass

    try:
        return fetch_miriade(body)
    except Exception:
        pass

    try:
        return fetch_mpc(body)
    except Exception:
        pass

    return None


def zodiac(lon):

    signs = [
        "Aries","Taurus","Gemini","Cancer",
        "Leo","Virgo","Libra","Scorpio",
        "Sagittarius","Capricorn","Aquarius","Pisces"
    ]

    s = int(lon/30)

    return signs[s], lon % 30


def generate():

    bodies = {}

    for body in PLANETS:

        r = fetch_body(body)

        if not r:
            continue

        lon = normalize(r["lon"])

        sign,deg = zodiac(lon)

        bodies[body] = {
            "lon":lon,
            "sign":sign,
            "degree":deg
        }

    output = {
        "generated_utc":datetime.datetime.utcnow().isoformat(),
        "bodies":bodies
    }

    os.makedirs("docs",exist_ok=True)

    with open("docs/current_week.json","w") as f:
        json.dump(output,f,indent=2)

    print("Weekly overlay written to docs/current_week.json")


if __name__ == "__main__":
    generate()
