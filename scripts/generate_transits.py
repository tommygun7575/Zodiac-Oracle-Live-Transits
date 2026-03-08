import json
import datetime
import os
import swisseph as swe

from scripts.bodies.horizons_client import fetch_horizons
from scripts.bodies.miriade_client import fetch_miriade
from scripts.bodies.mpc_client import fetch_mpc


PLANETS = [
    "Sun","Moon","Mercury","Venus","Mars",
    "Jupiter","Saturn","Uranus","Neptune","Pluto"
]

EXTENDED = [
    "Ceres","Chiron","Pallas","Juno","Vesta"
]

TNO = [
    "Eris","Haumea","Makemake","Sedna","Quaoar","Orcus"
]


ASPECTS = [0,60,90,120,180]


FIXED_STARS = {
    "Regulus":150.0,
    "Spica":204.0,
    "Antares":249.5,
    "Aldebaran":69.0,
    "Fomalhaut":334.0
}


def normalize(lon):
    return lon % 360


def zodiac_position(lon):

    signs = [
        "Aries","Taurus","Gemini","Cancer",
        "Leo","Virgo","Libra","Scorpio",
        "Sagittarius","Capricorn","Aquarius","Pisces"
    ]

    sign = int(lon/30)
    degree = lon % 30

    return signs[sign], degree


def compute_harmonics(lon):

    harmonics = {}

    for h in [3,5,7,9]:
        harmonics[f"h{h}"] = (lon*h) % 360

    return harmonics


def detect_star_contacts(body, lon):

    contacts = []

    for star, star_lon in FIXED_STARS.items():

        orb = abs(lon-star_lon)
        orb = min(orb,360-orb)

        if orb < 1.0:

            contacts.append({
                "body": body,
                "star": star,
                "orb": round(orb,3)
            })

    return contacts


def compute_aspects(bodies):

    aspects = []

    names = list(bodies.keys())

    for i in range(len(names)):
        for j in range(i+1,len(names)):

            lon1 = bodies[names[i]]["lon"]
            lon2 = bodies[names[j]]["lon"]

            diff = abs(lon1-lon2)
            diff = min(diff,360-diff)

            for asp in ASPECTS:

                if abs(diff-asp) < 1:

                    aspects.append({
                        "a": names[i],
                        "b": names[j],
                        "type": asp,
                        "orb": round(abs(diff-asp),3)
                    })

    return aspects


def compute_arabic_parts(sun, moon):

    fortune = (moon - sun) % 360
    spirit = (sun - moon) % 360

    return {
        "fortune": fortune,
        "spirit": spirit
    }


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


def generate():

    bodies = {}
    star_contacts = []

    all_bodies = PLANETS + EXTENDED + TNO

    for body in all_bodies:

        result = fetch_body(body)

        if not result:
            continue

        lon = normalize(result["lon"])

        sign, degree = zodiac_position(lon)

        bodies[body] = {
            "lon": lon,
            "sign": sign,
            "degree": degree,
            "harmonics": compute_harmonics(lon)
        }

        star_contacts += detect_star_contacts(body, lon)

    aspects = compute_aspects(bodies)

    sun = bodies["Sun"]["lon"]
    moon = bodies["Moon"]["lon"]

    arabic_parts = compute_arabic_parts(sun, moon)

    output = {
        "generated_utc": datetime.datetime.utcnow().isoformat(),
        "bodies": bodies,
        "aspects": aspects,
        "star_contacts": star_contacts,
        "arabic_parts": arabic_parts
    }

    os.makedirs("docs", exist_ok=True)

    filepath = "docs/current_week.json"

    with open(filepath, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Overlay written to {filepath}")


if __name__ == "__main__":
    generate()
