import json
import os
from datetime import datetime, timedelta

from scripts.bodies.horizons_engine import fetch as fetch_horizons
from scripts.bodies.miriade_engine import fetch as fetch_miriade
from scripts.bodies.swiss_engine import fetch as fetch_swiss

from scripts.utils.zodiac import zodiac_sign, degree_in_sign
from scripts.utils.harmonics import harmonics

from scripts.utils.houses import (
    julian_date_from_iso,
    compute_ascendant,
    whole_sign_house
)

from scripts.fixed_stars import get_fixed_star_positions


OBSERVER_LAT = 51.4769
OBSERVER_LON = 0.0000


PLANETS = [
"Sun","Moon","Mercury","Venus","Mars",
"Jupiter","Saturn","Uranus","Neptune","Pluto"
]

ASTEROIDS = [
"Chiron","Ceres","Pallas","Juno","Vesta",
"Psyche","Amor","Eros","Astraea","Sappho",
"Hygiea","Karma","Bacchus"
]

TNO = [
"Eris","Sedna","Haumea","Makemake","Quaoar",
"Varuna","Ixion","Orcus","Salacia","Typhon",
"2002 AW197","2003 VS2"
]

POSITION_BODIES = PLANETS + ASTEROIDS + TNO
ASPECT_BODIES = PLANETS + ASTEROIDS + TNO


ASPECT_DEFINITIONS = {
"conjunction": {"angle":0,"orb":8},
"opposition": {"angle":180,"orb":8},
"square": {"angle":90,"orb":6},
"trine": {"angle":120,"orb":6},
"sextile": {"angle":60,"orb":4}
}


def fetch_body_data(body, ts):

    data = fetch_horizons(body, ts)

    if data is None:
        data = fetch_miriade(body, ts)

    if data is None:
        data = fetch_swiss(body, ts)

    return data


def angle_difference(a,b):

    diff = abs(a-b) % 360

    if diff > 180:
        diff = 360-diff

    return diff


def get_next_sunday(dt):

    days_until = (6 - dt.weekday()) % 7

    if days_until == 0:
        days_until = 7

    return dt + timedelta(days=days_until)


def compute_positions(ts):

    jd = julian_date_from_iso(ts)

    asc_lon = compute_ascendant(jd,OBSERVER_LAT,OBSERVER_LON)

    positions = {}

    for body in POSITION_BODIES:

        ephem = fetch_body_data(body,ts)

        if ephem is None:
            continue

        lon = ephem["lon"]

        positions[body] = {

        "lon":lon,
        "lat":ephem.get("lat",0),
        "retrograde":ephem.get("retrograde",False),
        "speed":ephem.get("speed",0),

        "sign":zodiac_sign(lon),
        "deg":degree_in_sign(lon),

        "house":whole_sign_house(lon,asc_lon),

        "harmonics":harmonics(lon)

        }

    stars = get_fixed_star_positions()

    for star in stars:

        lon = star["longitude"]

        positions[star["name"]] = {

        "lon":lon,
        "lat":0,
        "retrograde":False,
        "speed":0,

        "sign":zodiac_sign(lon),
        "deg":degree_in_sign(lon),

        "house":whole_sign_house(lon,asc_lon),

        "harmonics":harmonics(lon)

        }

    return positions


def detect_aspect_events(week_positions):

    events = []

    # FIX: bodies must be read from the positions dictionary
    bodies = [b for b in ASPECT_BODIES if b in week_positions[0]["positions"]]

    for i in range(len(bodies)):

        for j in range(i+1,len(bodies)):

            b1 = bodies[i]
            b2 = bodies[j]

            for aspect,conf in ASPECT_DEFINITIONS.items():

                angle = conf["angle"]
                orb = conf["orb"]

                active = False
                start = None
                exact_time = None
                best_delta = 999

                for day in week_positions:

                    t = day["timestamp"]

                    lon1 = day["positions"][b1]["lon"]
                    lon2 = day["positions"][b2]["lon"]

                    diff = angle_difference(lon1,lon2)

                    delta = abs(diff-angle)

                    if delta <= orb:

                        if not active:
                            active = True
                            start = t

                        if delta < best_delta:
                            best_delta = delta
                            exact_time = t

                    else:

                        if active:

                            events.append({

                            "bodies":[b1,b2],
                            "aspect":aspect,

                            "start":start,
                            "exact":exact_time,
                            "end":t

                            })

                            active=False
                            start=None
                            exact_time=None
                            best_delta=999

                if active:

                    events.append({

                    "bodies":[b1,b2],
                    "aspect":aspect,

                    "start":start,
                    "exact":exact_time,
                    "end":week_positions[-1]["timestamp"]

                    })

    return events


def write_json(path,data):

    os.makedirs(os.path.dirname(path),exist_ok=True)

    with open(path,"w") as f:
        json.dump(data,f,indent=2)


def generate_all_feeds():

    now = datetime.utcnow().replace(microsecond=0)

    next_sun = get_next_sunday(now)

    week_days = [next_sun + timedelta(days=i) for i in range(7)]

    week_positions = []

    for t in week_days:

        ts = t.isoformat()+"Z"

        pos = compute_positions(ts)

        week_positions.append({

        "timestamp":ts,
        "positions":pos

        })

    aspect_events = detect_aspect_events(week_positions)

    feed_weekly = {

    "version":"ephemeris-v2.0",

    "week_start":week_positions[0]["timestamp"],

    "days":week_positions,

    "aspect_events":aspect_events

    }

    write_json("docs/current_week.json",feed_weekly)

    write_json("docs/_meta.json",{

    "generated_utc":datetime.utcnow().isoformat()+"Z",

    "version":"ephemeris-v2.0",

    "location":"Greenwich Observatory",

    "system":"full_oracle_ephemeris"

    })


if __name__ == "__main__":
    generate_all_feeds()
