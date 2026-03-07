import requests
import json
from datetime import datetime, timedelta
import os

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

# JPL Horizons body IDs
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

ASTEROIDS = {
    "Ceres": "1",
    "Pallas": "2",
    "Juno": "3",
    "Vesta": "4",
    "Chiron": "2060"
}

TNO = {
    "Eris": "136199",
    "Haumea": "136108",
    "Makemake": "136472",
    "Sedna": "90377"
}

ALL_BODIES = {**BODIES, **ASTEROIDS, **TNO}

ASPECTS = {
    "conjunction": {"angle":0,"orb":8},
    "opposition": {"angle":180,"orb":8},
    "square": {"angle":90,"orb":6},
    "trine": {"angle":120,"orb":6},
    "sextile": {"angle":60,"orb":4}
}


def zodiac_sign(lon):

    signs = [
        "Aries","Taurus","Gemini","Cancer",
        "Leo","Virgo","Libra","Scorpio",
        "Sagittarius","Capricorn","Aquarius","Pisces"
    ]

    return signs[int(lon//30)]


def degree_in_sign(lon):

    return round(lon % 30,3)


def angle_diff(a,b):

    d = abs(a-b) % 360

    if d > 180:
        d = 360-d

    return d


def fetch_horizons(body_id, timestamp):

    params = {
        "format": "json",
        "COMMAND": body_id,
        "EPHEM_TYPE": "OBSERVER",
        "CENTER": "500@399",
        "START_TIME": timestamp,
        "STOP_TIME": timestamp,
        "STEP_SIZE": "1d",
        "QUANTITIES": "1"
    }

    r = requests.get(HORIZONS_URL, params=params)

    data = r.json()

    text = data["result"]

    for line in text.split("\n"):
        if "Ecl. Lon." in line:
            lon = float(line.split()[-1])
            return lon

    return None


def get_next_sunday(now):

    days = (6-now.weekday())%7

    if days == 0:
        days = 7

    return now + timedelta(days=days)


def compute_positions(timestamp):

    positions = {}

    for name,body_id in ALL_BODIES.items():

        lon = fetch_horizons(body_id,timestamp)

        if lon is None:
            continue

        positions[name] = {
            "lon":lon,
            "lat":0,
            "retrograde":False,
            "speed":0,
            "sign":zodiac_sign(lon),
            "deg":degree_in_sign(lon)
        }

    return positions


def detect_aspects(days):

    events=[]

    bodies=list(BODIES.keys())

    for i in range(len(bodies)):
        for j in range(i+1,len(bodies)):

            b1=bodies[i]
            b2=bodies[j]

            for asp,conf in ASPECTS.items():

                angle=conf["angle"]
                orb=conf["orb"]

                active=False
                start=None
                exact=None
                best=999

                for d in days:

                    lon1=d["positions"][b1]["lon"]
                    lon2=d["positions"][b2]["lon"]

                    diff=angle_diff(lon1,lon2)
                    delta=abs(diff-angle)

                    if delta<=orb:

                        if not active:
                            start=d["timestamp"]
                            active=True

                        if delta<best:
                            best=delta
                            exact=d["timestamp"]

                    else:

                        if active:

                            events.append({
                                "bodies":[b1,b2],
                                "aspect":asp,
                                "start":start,
                                "exact":exact,
                                "end":d["timestamp"]
                            })

                            active=False
                            best=999

                if active:

                    events.append({
                        "bodies":[b1,b2],
                        "aspect":asp,
                        "start":start,
                        "exact":exact,
                        "end":days[-1]["timestamp"]
                    })

    return events


def write_json(path,data):

    os.makedirs(os.path.dirname(path),exist_ok=True)

    with open(path,"w") as f:
        json.dump(data,f,indent=2)


def generate_week():

    now=datetime.utcnow()

    start=get_next_sunday(now)

    days=[]

    for i in range(7):

        t=start+timedelta(days=i)

        ts=t.isoformat()+"Z"

        pos=compute_positions(ts)

        days.append({
            "timestamp":ts,
            "positions":pos
        })

    aspects=detect_aspects(days)

    data={
        "version":"oracle-live-ephemeris",
        "week_start":days[0]["timestamp"],
        "days":days,
        "aspect_events":aspects
    }

    write_json("docs/current_week.json",data)

    write_json("docs/_meta.json",{
        "generated_utc":datetime.utcnow().isoformat()+"Z"
    })


if __name__=="__main__":
    generate_week()
