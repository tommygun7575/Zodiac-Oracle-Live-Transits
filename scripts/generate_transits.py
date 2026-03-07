import os
import sys
import json
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------
# allow imports when running inside GitHub runner
# ---------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from scripts.bodies.horizons_engine import fetch_horizons_position
from scripts.bodies.swiss_engine import fetch_swiss_position
from scripts.bodies.miriade_engine import fetch_miriade_position


OUTPUT_FILE = "docs/current_week.json"


MAJOR_BODIES = [
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto"
]


# ---------------------------------------------------
# BODY RESOLUTION ORDER
# JPL → Swiss → Miriade
# ---------------------------------------------------

def resolve_body(body, timestamp):

    # JPL Horizons (PRIMARY SOURCE)
    try:
        result = fetch_horizons_position(body, timestamp)
        if result:
            result["used_source"] = "jpl"
            return result
    except Exception:
        pass

    # Swiss Ephemeris (fallback)
    try:
        result = fetch_swiss_position(body, timestamp)
        if result:
            result["used_source"] = "swiss"
            return result
    except Exception:
        pass

    # Miriade (final fallback)
    try:
        result = fetch_miriade_position(body, timestamp)
        if result:
            result["used_source"] = "miriade"
            return result
    except Exception:
        pass

    return {
        "ecl_lon_deg": None,
        "ecl_lat_deg": None,
        "used_source": "missing"
    }


# ---------------------------------------------------
# COMPUTE ONE DAY OF TRANSITS
# ---------------------------------------------------

def compute_day(timestamp):

    objects = {}

    for body in MAJOR_BODIES:

        position = resolve_body(body, timestamp)

        objects[body] = {
            "ecl_lon_deg": position["ecl_lon_deg"],
            "ecl_lat_deg": position["ecl_lat_deg"],
            "used_source": position["used_source"]
        }

    return {
        "timestamp": timestamp,
        "objects": objects
    }


# ---------------------------------------------------
# FIND NEXT SUNDAY (UTC)
# ---------------------------------------------------

def next_sunday():

    now = datetime.now(timezone.utc)

    days = (6 - now.weekday()) % 7

    if days == 0:
        days = 7

    return now + timedelta(days=days)


# ---------------------------------------------------
# GENERATE WEEKLY TRANSIT DATA
# ---------------------------------------------------

def generate_week():

    start = next_sunday()

    week = []

    for i in range(7):

        t = start + timedelta(days=i)

        iso = t.replace(microsecond=0).isoformat().replace("+00:00", "Z")

        week.append(compute_day(iso))

    return week


# ---------------------------------------------------
# MAIN
# ---------------------------------------------------

def main():

    week_data = generate_week()

    output = {
        "version": "oracle-weekly-transits",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "week_start": week_data[0]["timestamp"],
        "days": week_data
    }

    os.makedirs("docs", exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print("Weekly transit file generated:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
