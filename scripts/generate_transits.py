import json
import os
from datetime import datetime, timedelta

# REAL primary ephemeris
from scripts.bodies.horizons_engine import fetch as fetch_horizons

# Secondary fallback for bodies Horizons cannot resolve (TNOs, some asteroids)
from scripts.bodies.miriade_engine import fetch as fetch_miriade

# Final fallback (safe no-op stub)
from scripts.bodies.swiss_engine import fetch as fetch_swiss

from scripts.utils.zodiac import zodiac_sign, degree_in_sign
from scripts.utils.harmonics import harmonics
from scripts.fixed_stars import get_fixed_star_positions


# --------------------------------------------------------------------
# BODIES LIST — These will be expanded in Phase 2 Step 3 for real TNOs
# --------------------------------------------------------------------
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


# --------------------------------------------------------------------
# FETCH LOGIC — Horizons → Miriade → Swiss stub
# --------------------------------------------------------------------
def fetch_body_data(body, timestamp):
    # Primary: JPL Horizons (real precision)
    data = fetch_horizons(body, timestamp)

    # Secondary fallback: Miriade (TNOs/asteroids not in Horizons)
    if data is None:
        data = fetch_miriade(body, timestamp)

    # Final fallback: Swiss stub (never harms CI)
    if data is None:
        data = fetch_swiss(body, timestamp)

    return data


# --------------------------------------------------------------------
# COMPUTE TRANSITS FOR ONE TIMESTAMP
# --------------------------------------------------------------------
def compute_transits(ts):
    result = {}

    for body in BODIES:
        ephem = fetch_body_data(body, ts)
        if ephem is None:
            continue

        lon = ephem["lon"]
        lat = ephem.get("lat", 0.0)
        retrograde = ephem.get("retrograde", False)

        sign = zodiac_sign(lon)
        deg = degree_in_sign(lon)

        harm = harmonics(lon)

        result[body] = {
            "lon": lon,
            "lat": lat,
            "retrograde": retrograde,
            "sign": sign,
            "deg": deg,
            "house": None,         # House engine comes in Phase 2 Step 4
            "harmonics": harm
        }

    # Merge fixed stars
    for star in get_fixed_star_positions():
        lon = star["longitude"]
        result[star["name"]] = {
            "lon": lon,
            "lat": 0.0,
            "retrograde": False,
            "sign": zodiac_sign(lon),
            "deg": degree_in_sign(lon),
            "house": None,
            "harmonics": harmonics(lon)
        }

    return result


# --------------------------------------------------------------------
# JSON WRITER
# --------------------------------------------------------------------
def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# --------------------------------------------------------------------
# FEED GENERATION — now / daily / 7-day / weekly rollover
# --------------------------------------------------------------------
def generate_all_feeds():
    now = datetime.utcnow().replace(microsecond=0)
    ts_now = now.isoformat() + "Z"

    ts_list = [now + timedelta(days=i) for i in range(7)]

    feeds = {
        "feed_now.json": [
            {"timestamp": ts_now, "transits": compute_transits(ts_now)}
        ],

        "feed_daily.json": [
            {"timestamp": t.isoformat() + "Z",
             "transits": compute_transits(t.isoformat() + "Z")}
            for t in ts_list
        ],

        "feed_week.json": [
            {"timestamp": t.isoformat() + "Z",
             "transits": compute_transits(t.isoformat() + "Z")}
            for t in ts_list
        ],

        "feed_weekly.json": [
            {"timestamp": t.isoformat() + "Z",
             "transits": compute_transits(t.isoformat() + "Z")}
            for t in ts_list
        ],
    }

    # Write feeds
    for fn, feed_data in feeds.items():
        write_json(os.path.join("docs", fn), feed_data)

    # Metadata
    write_json(os.path.join("docs", "metadata.json"), {
        "generated_utc": datetime.utcnow().isoformat() + "Z",
        "bodies": BODIES,
        "fixed_stars": [star["name"] for star in get_fixed_star_positions()],
    })


if __name__ == "__main__":
    generate_all_feeds()
