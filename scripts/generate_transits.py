import sys
import os
import json
import datetime
import swisseph as swe

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.bodies.horizons_engine import fetch, fetch_numbered
from scripts.bodies.miriade_engine import fetch_miriade
from scripts.bodies.swiss_engine import get_planet, get_asteroid


PLANETS = [
    "Sun","Moon","Mercury","Venus","Mars",
    "Jupiter","Saturn","Uranus","Neptune","Pluto"
]

ASTEROIDS = {
    "Ceres":1,
    "Pallas":2,
    "Juno":3,
    "Vesta":4
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


def resolve_planet(body,jd):

    r = fetch(body,jd)

    if r:
        return r

    r = fetch_miriade(body,jd)

    if r:
        return r

    r = get_planet(body,jd)

    if r:
        lon,lat = r
        return lon,lat,"swiss"

    return None,None,"missing"


def resolve_minor(name,number,jd):

    r = fetch_numbered(number,jd)

    if r:
        return r

    r = fetch_miriade(name,jd)

    if r:
        return r

    r = get_asteroid(number,jd)

    if r:
        lon,lat = r
        return lon,lat,"swiss"

    return None,None,"missing"


def compute_harmonics(objects):

    harmonics={}

    for body,data in objects.items():

        if data["ecl_lon_deg"] is None:
            continue

        lon=data["ecl_lon_deg"]

        harmonics[f"{body}_H5"]=(lon*5)%360
        harmonics[f"{body}_H7"]=(lon*7)%360

    return harmonics


def compute_part_of_fortune(objects):

    sun=objects["Sun"]["ecl_lon_deg"]
    moon=objects["Moon"]["ecl_lon_deg"]

    if sun is None or moon is None:
        return None

    return (moon-sun)%360


def generate():

    now=datetime.datetime.utcnow()

    week=[]

    for i in range(7):

        t=now+datetime.timedelta(days=i)

        jd=swe.julday(
            t.year,t.month,t.day,
            t.hour+(t.minute/60)
        )

        objects={}

        for body in PLANETS:

            lon,lat,src=resolve_planet(body,jd)

            objects[body]={
                "ecl_lon_deg":lon,
                "ecl_lat_deg":lat,
                "used_source":src
            }

        for name,num in ASTEROIDS.items():

            lon,lat,src=resolve_minor(name,num,jd)

            objects[name]={
                "ecl_lon_deg":lon,
                "ecl_lat_deg":lat,
                "used_source":src
            }

        for name,num in TNOS.items():

            lon,lat,src=resolve_minor(name,num,jd)

            objects[name]={
                "ecl_lon_deg":lon,
                "ecl_lat_deg":lat,
                "used_source":src
            }

        arabic_parts={
            "Part_of_Fortune":compute_part_of_fortune(objects)
        }

        harmonics=compute_harmonics(objects)

        week.append({
            "timestamp":t.isoformat()+"Z",
            "objects":objects,
            "arabic_parts":arabic_parts,
            "harmonics":harmonics
        })

    out={
        "version":"oracle-weekly-transits",
        "generated_at":datetime.datetime.utcnow().isoformat()+"Z",
        "week_start":week[0]["timestamp"],
        "days":week
    }

    os.makedirs("docs",exist_ok=True)

    with open("docs/current_week.json","w") as f:
        json.dump(out,f,indent=2)


if __name__=="__main__":
    generate()
