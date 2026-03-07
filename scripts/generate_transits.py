import json
import datetime
import math
import swisseph as swe

from scripts.bodies.swiss_engine import get_planet, get_asteroid
from scripts.bodies.horizons_engine import get_body, get_numbered_object

OUTPUT = "docs/current_week.json"

MAJOR_BODIES = [
    "Sun","Moon","Mercury","Venus","Mars",
    "Jupiter","Saturn","Uranus","Neptune","Pluto"
]

ASTEROIDS = {
    "Ceres":1,
    "Pallas":2,
    "Juno":3,
    "Vesta":4,
}

CENTAURS = {
    "Chiron":2060,
    "Pholus":5145,
    "Nessus":7066
}

TNOS = {
    "Eris":136199,
    "Haumea":136108,
    "Makemake":136472,
    "Sedna":90377,
    "Orcus":90482,
    "Quaoar":50000,
    "Ixion":28978
}

FIXED_STARS = {
    "Regulus":150.0,
    "Spica":204.0,
    "Aldebaran":69.0,
    "Antares":249.0
}

def harmonics(lon):
    return {
        "H5": (lon*5) % 360,
        "H7": (lon*7) % 360
    }

def resolve_major(body, jd):

    r = get_body(body, jd)
    if r:
        return r

    r = get_planet(body, jd)
    if r:
        return r

    return None, None, "missing"

def resolve_numbered(name, number, jd):

    r = get_numbered_object(number, jd)
    if r:
        return r

    r = get_asteroid(number, jd)
    if r:
        return r

    return None, None, "missing"

def generate():

    now = datetime.datetime.utcnow()
    days = []

    for d in range(7):

        t = now + datetime.timedelta(days=d)

        jd = swe.julday(
            t.year,
            t.month,
            t.day,
            t.hour + t.minute/60
        )

        objects = {}
        harmonic_map = {}

        sun = None
        moon = None

        for body in MAJOR_BODIES:

            lon, lat, src = resolve_major(body, jd)

            objects[body] = {
                "ecl_lon_deg": lon,
                "ecl_lat_deg": lat,
                "used_source": src
            }

            if lon is not None:
                h = harmonics(lon)
                harmonic_map[f"{body}_H5"] = h["H5"]
                harmonic_map[f"{body}_H7"] = h["H7"]

            if body == "Sun":
                sun = lon
            if body == "Moon":
                moon = lon

        for name,num in ASTEROIDS.items():

            lon,lat,src = resolve_numbered(name,num,jd)

            objects[name] = {
                "ecl_lon_deg": lon,
                "ecl_lat_deg": lat,
                "used_source": src
            }

        for name,num in CENTAURS.items():

            lon,lat,src = resolve_numbered(name,num,jd)

            objects[name] = {
                "ecl_lon_deg": lon,
                "ecl_lat_deg": lat,
                "used_source": src
            }

        for name,num in TNOS.items():

            lon,lat,src = resolve_numbered(name,num,jd)

            objects[name] = {
                "ecl_lon_deg": lon,
                "ecl_lat_deg": lat,
                "used_source": src
            }

        for star,lon in FIXED_STARS.items():

            objects[star] = {
                "ecl_lon_deg": lon,
                "ecl_lat_deg":0,
                "used_source":"catalog"
            }

        arabic = {}

        if sun and moon:
            arabic["Part_of_Fortune"] = (moon - sun) % 360

        days.append({
            "timestamp": t.isoformat()+"Z",
            "objects": objects,
            "arabic_parts": arabic,
            "harmonics": harmonic_map
        })

    data = {
        "version":"oracle-weekly-transits",
        "generated_at": datetime.datetime.utcnow().isoformat()+"Z",
        "week_start": now.isoformat()+"Z",
        "days": days
    }

    with open(OUTPUT,"w") as f:
        json.dump(data,f,indent=2)

if __name__ == "__main__":
    generate()
