import json
import os
from datetime import datetime, timedelta

# Ephemeris fetch engines
from scripts.bodies.horizons_engine import fetch as fetch_horizons
from scripts.bodies.miriade_engine import fetch as fetch_miriade
from scripts.bodies.swiss_engine import fetch as fetch_swiss

# Core utilities
from scripts.utils.zodiac import zodiac_sign, degree_in_sign
from scripts.utils.harmonics import harmonics

# House engine (Greenwich global baseline)
from scripts.utils.houses import (
    julian_date_from_iso,
    compute_ascendant,
    whole_sign_cusps,
    whole_sign_house
)

# Fixed-star pull
from scripts.fixed_stars import get_fixed_star_positions

# Aspect engine
from scripts.utils.aspects import compute_all_aspects


# ---------------------------------------------------------------
# GLOBAL FEED OBSERVER LOCATION — Greenwich Observatory
# ---------------------------------------------------------------
OBSERVER_LAT = 51.4769
OBSERVER_LON = 0.0000


# ---------------------------------------------------------------
# BODIES LIST
# ---------------------------------------------------------------
BODIES = [
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
    "Chiron", "Ceres", "Pallas", "Juno", "Vesta",
    "Psyche", "Amor", "Eros", "Astraea", "Sappho",
    "Hygiea", "Karma", "Bacchus",
    "Eris", "Sedna", "Haumea", "Makemake", "Quaoar",
    "Varuna", "Ixion", "Orcus", "Salacia", "Typhon",
    "2002 AW197", "2003 VS2"
]


# ---------------------------------------------------------------
# FETCH ENGINE: Horizons → Miriade → Swiss
# ---------------------------------------------------------------
def fetch_body_data(body, ts):
    data = fetch_horizons(body, ts)
    if data is None:
        data = fetch_miriade(body, ts)
    if data is None:
        data = fetch_swiss(body, ts)
    return data


# ---------------------------------------------------------------
# NEXT SUNDAY CALCULATOR
# ---------------------------------------------------------------
def get_next_sunday(dt):
    # Monday=0 ... Sunday=6
    days_until = (6 - dt.weekday()) % 7
    if days_until == 0:
        days_until = 7
    return dt + timedelta(days=days_until)


# ---------------------------------------------------------------
# COMPUTE ALL TRANSITS FOR ONE TIMESTAMP
# ---------------------------------------------------------------
def compute_transits(ts):
    jd = julian_date_from_iso(ts)

    # House structure
    asc_lon = compute_ascendant(jd, OBSERVER_LAT, OBSERVER_LON)
    cusps = whole_sign_cusps(asc_lon)

    positions = {}

    # Main bodies
    for body in BODIES:
        ephem = fetch_body_data(body, ts)
        if ephem is None:
            continue

        lon = ephem["lon"]
        lat = ephem.get("lat", 0.0)
        retrograde = ephem.get("retrograde", False)
        speed = ephem.get("speed", 0.0)

        sign = zodiac_sign(lon)
        deg = degree_in_sign(lon)
        harm = harmonics(lon)
        house = whole_sign_house(lon, asc_lon)

        positions[body] = {
            "lon": lon,
            "lat": lat,
            "retrograde": retrograde,
            "speed": speed,
            "sign": sign,
            "deg": deg,
            "house": house,
            "harmonics": harm
        }

    # Fixed stars
    for star in get_fixed_star_positions():
        lon = star["longitude"]
        positions[star["name"]] = {
            "lon": lon,
            "lat": 0.0,
            "retrograde": False,
            "speed": 0.0,
            "sign": zodiac_sign(lon),
            "deg": degree_in_sign(lon),
            "house": whole_sign_house(lon, asc_lon),
            "harmonics": harmonics(lon)
        }

    # Aspects
    aspects = compute_all_aspects(positions)

    return {
        "positions": positions,
        "aspects": aspects
    }


# ---------------------------------------------------------------
# JSON WRITER
# ---------------------------------------------------------------
def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------
# FEED GENERATOR — WEEKLY PIPELINE
# ---------------------------------------------------------------
def generate_all_feeds():
    now = datetime.utcnow().replace(microsecond=0)
    ts_now = now.isoformat() + "Z"

    # Determine Sunday→Saturday window
    next_sun = get_next_sunday(now)
    week_days = [(next_sun + timedelta(days=i)) for i in range(7)]

    # feed_now.json
    feed_now = [
        {
            "version": "ephemeris-v1.0",
            "timestamp": ts_now,
            "transits": compute_transits(ts_now)
        }
    ]

    # feed_daily.json (next Sunday + 6 following days)
    feed_daily = [
        {
            "version": "ephemeris-v1.0",
            "timestamp": t.isoformat() + "Z",
            "transits": compute_transits(t.isoformat() + "Z")
        }
        for t in week_days
    ]

    # current_week.json — APP PRIMARY FILE
    feed_weekly = {
        "version": "ephemeris-v1.0",
        "week_start": next_sun.isoformat() + "Z",
        "days": [
            {
                "timestamp": t.isoformat() + "Z",
                "transits": compute_transits(t.isoformat() + "Z")
            }
            for t in week_days
        ]
    }

    # Write outputs
    write_json(os.path.join("docs", "feed_now.json"), feed_now)
    write_json(os.path.join("docs", "feed_daily.json"), feed_daily)
    write_json(os.path.join("docs", "current_week.json"), feed_weekly)

    # Metadata
    write_json(os.path.join("docs", "_meta.json"), {
        "generated_utc": datetime.utcnow().isoformat() + "Z",
        "version": "ephemeris-v1.0",
        "location": "Greenwich Observatory",
        "includes": {
            "positions": True,
            "aspects": True,
            "houses": True,
            "harmonics": True
        }
    })


if __name__ == "__main__":
    generate_all_feeds()
