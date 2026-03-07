import json
import os
import datetime
import math

import swisseph as swe

# Optional engines
try:
    from astroquery.jplhorizons import Horizons
    HORIZONS_AVAILABLE = True
except Exception:
    HORIZONS_AVAILABLE = False

try:
    from scripts.bodies.miriade_engine import fetch as miriade_fetch
    MIRI_AVAILABLE = True
except Exception:
    MIRI_AVAILABLE = False


OUTPUT_FILE = "docs/current_week.json"


BODIES = [
    "Sun","Moon","Mercury","Venus","Mars",
    "Jupiter","Saturn","Uranus","Neptune","Pluto"
]

ASTEROIDS = {
    "Ceres": 1,
    "Pallas": 2,
    "Juno": 3,
    "Vesta": 4,
}

CENTaurs = {
    "Chiron": 2060,
    "Pholus": 5145,
    "Nessus": 7066,
}

TNOS = {
    "Eris": 136199,
    "Haumea": 136108,
    "Makemake": 136472,
    "Sedna": 90377,
    "Orcus": 90482,
    "Quaoar": 50000,
    "Ixion": 28978
}

FIXED_STARS = {
    "Regulus": 150.0,
    "Spica": 204.0,
    "Aldebaran": 69.0,
    "Antares": 249.0
}


# ---------- Horizons primary ----------

def horizons_position(body, jd):

    if not HORIZONS_AVAILABLE:
        return None

    try:
        obj = Horizons(id=body, location='500@10', epochs=jd)
        vec = obj.vectors()

        x = float(vec['x'][0])
        y = float(vec['y'][0])
        z = float(vec['z'][0])

        lon = math.degrees(math.atan2(y,x)) % 360
        lat = math.degrees(math.atan2(z, math.sqrt(x*x+y*y)))

        return lon, lat, "horizons"

    except Exception:
        return None


# ---------- Swiss fallback ----------

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


def swiss_position(body, jd):

    try:
        code = SWISS_MAP.get(body)
        if code is None:
            return None

        pos, _ = swe.calc_ut(jd, code)

        lon = pos[0]
        lat = pos[1]

        return lon, lat, "swiss"

    except Exception:
        return None


# ---------- Miriade fallback ----------

def miriade_position(body, jd):

    if not MIRI_AVAILABLE:
        return None

    try:
        data = miriade_fetch(body, jd)
        return data["lon"], data["lat"], "miriade"

    except Exception:
        return None


# ---------- Resolver ----------

def resolve(body, jd):

    r = horizons_position(body, jd)
    if r:
        return r

    r = swiss_position(body, jd)
    if r:
        return r

    r = miriade_position(body, jd)
    if r:
        return r

    return None, None, "missing"


# ---------- Harmonics ----------

def harmonics(lon):

    return {
        "H5": (lon * 5) % 360,
        "H7": (lon * 7) % 360
    }


# ---------- Arabic Part ----------

def part_of_fortune(sun, moon):

    return (moon - sun) % 360


# ---------- Main generator ----------

def generate():

    now = datetime.datetime.utcnow()
    start = now

    days = []

    for i in range(7):

        t = start + datetime.timedelta(days=i)

        jd = swe.julday(
            t.year,
            t.month,
            t.day,
            t.hour + t.minute/60.0
        )

        objects = {}
        harmonic_map = {}

        sun_lon = None
        moon_lon = None

        for body in BODIES:

            lon, lat, source = resolve(body, jd)

            objects[body] = {
                "ecl_lon_deg": lon,
                "ecl_lat_deg": lat,
                "used_source": source
            }

            if lon is not None:
                h = harmonics(lon)
                harmonic_map[f"{body}_H5"] = h["H5"]
                harmonic_map[f"{body}_H7"] = h["H7"]

            if body == "Sun":
                sun_lon = lon
            if body == "Moon":
                moon_lon = lon


        # fixed stars

        for star, lon in FIXED_STARS.items():

            objects[star] = {
                "ecl_lon_deg": lon,
                "ecl_lat_deg": 0,
                "used_source": "catalog"
            }


        # asteroids

        for name in ASTEROIDS:
            objects[name] = {
                "ecl_lon_deg": None,
                "ecl_lat_deg": None,
                "used_source": "pending_ephemeris"
            }


        # TNOs

        for name in TNOS:
            objects[name] = {
                "ecl_lon_deg": None,
                "ecl_lat_deg": None,
                "used_source": "pending_ephemeris"
            }


        arabic = {}

        if sun_lon and moon_lon:
            arabic["Part_of_Fortune"] = part_of_fortune(sun_lon, moon_lon)


        days.append({

            "timestamp": t.isoformat()+"Z",
            "objects": objects,
            "arabic_parts": arabic,
            "harmonics": harmonic_map

        })


    data = {

        "version": "oracle-weekly-transits",
        "generated_at": datetime.datetime.utcnow().isoformat()+"Z",
        "week_start": start.isoformat()+"Z",
        "days": days

    }


    os.makedirs("docs", exist_ok=True)

    with open(OUTPUT_FILE,"w") as f:
        json.dump(data,f,indent=2)


if __name__ == "__main__":
    generate()
