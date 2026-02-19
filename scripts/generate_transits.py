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

# Aspect engine (Phase 3)
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
# FETCH PIPELINE: Horizons → Miriade → Swiss
# ---------------------------------------------------------------
def fetch_body_data(body, ts):
    data = fetch_horizons(body, ts)
    if data is None:
        data = fetch_miriade(body, ts)
    if data is None:
        data = fetch_swiss(body, ts)
    return data


# ---------------------------------------------------------------
# COMPUTE ALL TRANSITS FOR ONE TIMESTAMP
# ---------------------------------------------------------------
def compute_transits(ts):
    jd = julian_date_from_iso(ts)

    # House framework
    asc_lon = compute_ascendant(jd, OBSERVER_LAT, OBSERVER_LON)
    cusps = whole_sign_cusps(asc_lon)

    positions = {}

    # -------------------------------
    # PLANETS / ASTEROIDS / TNOs
    # -------------------------------
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

    # -------------------------------
    # FIXED STARS
    # -------------------------------
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

    # -------------------------------
    # ASPECT GRID (NEW)
    # -------------------------------
    aspects = compute_all_aspects(positions)

    return {
        "positions": positions,
        "aspects": aspects
    }


# ---------------------------------------------------------------
# HELPERS: JSON writer
# ---------------------------------------------------------------
def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------
# FEED GENERATOR (weekly workflow)
# ---------------------------------------------------------------
def generate_all_feeds():
    now = datetime.utcnow().replace(microsecond=0)
    ts_now = now.isoformat() + "Z"

    ts_list = [now + timedelta(days=i) for i in range(7)]

    # Build the full feed suite
    feeds = {
        "feed_now.json": [
            {"timestamp": ts_now, "transits": compute_transits(ts_now)}
        ],
        "feed_daily.json": [
            {"timestamp": t.isoformat() + "Z", "transits": compute_transits(t.isoformat() + "Z")}
            for t in ts_list
        ],
        "feed_week.json": [
            {"timestamp": t.isoformat() + "Z", "transits": compute_transits(t.isoformat() + "Z")}
            for t in ts_list
        ],
        "feed_weekly.json": [
            {"timestamp": t.isoformat() + "Z", "transits": compute_transits(t.isoformat() + "Z")}
            for t in ts_list
        ]
    }

    # Write feeds
    for fn, feed_data in feeds.items():
        write_json(os.path.join("docs", fn), feed_data)

    # Metadata
    write_json(os.path.join("docs", "metadata.json"), {
        "generated_utc": datetime.utcnow().isoformat() + "Z",
        "bodies": BODIES,
        "fixed_stars": [star["name"] for star in get_fixed_star_positions()]
    })


if __name__ == "__main__":
    generate_all_feeds()
