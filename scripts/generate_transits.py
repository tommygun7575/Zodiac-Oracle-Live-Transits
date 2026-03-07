import json
from datetime import datetime, timedelta
import os

PLANETS = [
"Sun","Moon","Mercury","Venus","Mars",
"Jupiter","Saturn","Uranus","Neptune","Pluto"
]

ASTEROIDS = [
"Chiron","Ceres","Pallas","Juno","Vesta"
]

TNO = [
"Eris","Sedna","Haumea","Makemake"
]

POSITION_BODIES = PLANETS + ASTEROIDS + TNO
ASPECT_BODIES = PLANETS

ASPECT_DEFINITIONS = {
"conjunction": {"angle":0,"orb":8},
"opposition": {"angle":180,"orb":8},
"square": {"angle":90,"orb":6},
"trine": {"angle":120,"orb":6},
"sextile": {"angle":60,"orb":4}
}


def angle_difference(a,b):

    diff = abs(a-b) % 360

    if diff > 180:
        diff = 360-diff

    return diff


def next_sunday(now):

    days = (6 - now.weekday()) % 7

    if days == 0:
        days = 7

    return now + timedelta(days=days)


def fake_positions():

    # placeholder ephemeris values
    # real implementation should pull from JPL / Swiss / Miriade

    positions = {}

    for body in POSITION_BODIES:

        positions[body] = {
            "lon": (hash(body) % 360),
            "lat":0,
            "retrograde":False,
            "speed":1
        }

    return positions


def detect_aspects(week_positions):

    events = []

    # ***** CRITICAL FIX *****
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
                exact = None
                best = 999

                for day in week_positions:

                    lon1 = day["positions"][b1]["lon"]
                    lon2 = day["positions"][b2]["lon"]

                    diff = angle_difference(lon1,lon2)
                    delta = abs(diff-angle)

                    if delta <= orb:

                        if not active:
                            start = day["timestamp"]
                            active = True

                        if delta < best:
                            best = delta
                            exact = day["timestamp"]

                    else:

                        if active:

                            events.append({
                                "bodies":[b1,b2],
                                "aspect":aspect,
                                "start":start,
                                "exact":exact,
                                "end":day["timestamp"]
                            })

                            active=False
                            best=999

                if active:

                    events.append({
                        "bodies":[b1,b2],
                        "aspect":aspect,
                        "start":start,
                        "exact":exact,
                        "end":week_positions[-1]["timestamp"]
                    })

    return events


def write_json(path,data):

    os.makedirs(os.path.dirname(path),exist_ok=True)

    with open(path,"w") as f:
        json.dump(data,f,indent=2)


def generate():

    now = datetime.utcnow()

    start = next_sunday(now)

    days = []

    for i in range(7):

        d = start + timedelta(days=i)

        positions = fake_positions()

        days.append({
            "timestamp": d.isoformat()+"Z",
            "positions": positions
        })

    aspects = detect_aspects(days)

    data = {
        "version":"ephemeris-v2",
        "week_start":days[0]["timestamp"],
        "days":days,
        "aspect_events":aspects
    }

    write_json("docs/current_week.json",data)

    write_json("docs/_meta.json",{
        "generated_utc":datetime.utcnow().isoformat()+"Z",
        "version":"ephemeris-v2"
    })


if __name__ == "__main__":
    generate()
