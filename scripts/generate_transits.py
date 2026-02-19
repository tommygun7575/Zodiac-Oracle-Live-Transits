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

# House system engine (Whole Sign + Placidus support)
from scripts.utils.houses import (
    julian_date_from_iso,
    compute_ascendant,
    whole_sign_cusps,
    whole_sign_house
)

from scripts.fixed_stars import get_fixed_star_positions


# ---------------------------------------------------------------
# GLOBAL LOCATION FOR FEED — Greenwich Observatory (Prime Meridian)
# ---------------------------------------------------------------
OBSERVER_LAT = 51.4769     # degrees North
OBSERVER_LON = 0.0000      # degrees East


# --------------------------------------------------------------------
# BODIES LIST — Planets + Asteroids + TNOs
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

    # Secondary: Miriade for bodies Horizons cannot resolve
    if data is None:
        data = fetch_miriade(body, timestamp)

    # Final fallback: Swiss stub
    if data is None:
        data = fetch_swiss(body, timestamp)

    return data


# --------------------------------------------------------------------
# COMPUTE TRANSITS FOR ONE TIMESTAMP (WITH HOUSES)
# --------------------------------------------------------------------
def compute_transits(ts):
    jd = julian_date_from_iso(ts)

    # Compute Ascendant for Greenwich-based feed
    asc_lon = compute_ascendant(jd, OBSERVER_LAT, OBSERVER_LON)

    # Whole Sign cusps for global feed
    cusps = whole_sign_cusps(asc_lon)

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

        # Whole Sign house assignment
        house = whole_sign_house(lon, asc_lon)

        result[body] = {
            "lon": lon,
            "lat": lat,
            "retrograde": retrograde,
            "sign": sign,
            "deg": deg,
            "house": house,
            "harmonics": harm
        }

    # Merge fixed stars (also assigned whole sign houses)
    for star in get_fixed_star_positions():
        lon = star["longitude"]
        result[star["name"]] = {
            "lon": lon,
            "lat": 0.0,
            "retrograde": False,
            "sign": zodiac_sign(lon),
            "deg": degree_in_sign(lon),
            "house": whole_sign_house(lon, asc_lon),
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
