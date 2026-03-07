import os
import sys
import json
import time
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from scripts.bodies.horizons_engine import fetch_horizons_position
from scripts.bodies.swiss_engine import fetch_swiss_position
from scripts.bodies.miriade_engine import fetch_miriade_position

REGISTRY = "data/body_registry.json"
OUTPUT = "docs/current_week.json"


def load_registry():

    with open(REGISTRY) as f:
        data = json.load(f)

    bodies = []

    for group in data.values():
        bodies.extend(group)

    return bodies


def resolve_body(body, timestamp):

    try:
        r = fetch_horizons_position(body, timestamp)
        r["used_source"] = "jpl"
        return r
    except:
        pass

    try:
        r = fetch_swiss_position(body, timestamp)
        r["used_source"] = "swiss"
        return r
    except:
        pass

    try:
        r = fetch_miriade_position(body, timestamp)
        r["used_source"] = "miriade"
        return r
    except:
        pass

    return {
        "ecl_lon_deg": None,
        "ecl_lat_deg": None,
        "used_source": "missing"
    }


def compute_arabic_parts(objects):

    parts = {}

    if "Sun" in objects and "Moon" in objects:

        sun = objects["Sun"]["ecl_lon_deg"]
        moon = objects["Moon"]["ecl_lon_deg"]

        if sun is not None and moon is not None:

            fortune = (moon - sun) % 360

            parts["Part_of_Fortune"] = fortune

    return parts


def compute_harmonics(objects):

    harmonics = {}

    for body, data in objects.items():

        lon = data["ecl_lon_deg"]

        if lon is None:
            continue

        harmonics[f"{body}_H5"] = (lon * 5) % 360
        harmonics[f"{body}_H7"] = (lon * 7) % 360

    return harmonics


def compute_day(bodies, timestamp):

    objects = {}

    for body in bodies:

        pos = resolve_body(body, timestamp)

        objects[body] = pos

        time.sleep(0.1)

    parts = compute_arabic_parts(objects)
    harmonics = compute_harmonics(objects)

    return {
        "timestamp": timestamp,
        "objects": objects,
        "arabic_parts": parts,
        "harmonics": harmonics
    }


def next_sunday():

    now = datetime.now(timezone.utc)

    days = (6 - now.weekday()) % 7

    if days == 0:
        days = 7

    return now + timedelta(days=days)


def generate_week():

    bodies = load_registry()

    start = next_sunday()

    week = []

    for i in range(7):

        t = start + timedelta(days=i)

        iso = t.replace(microsecond=0).isoformat().replace("+00:00","Z")

        week.append(compute_day(bodies, iso))

    return week


def main():

    week = generate_week()

    output = {
        "version": "oracle-weekly-transits",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
        "week_start": week[0]["timestamp"],
        "days": week
    }

    os.makedirs("docs", exist_ok=True)

    with open(OUTPUT,"w") as f:
        json.dump(output, f, indent=2)

    print("Weekly transit file generated")


if __name__ == "__main__":
    main()
