import json
from datetime import datetime, timedelta
from scripts.bodies.horizons_engine import fetch as fetch_horizons
from scripts.bodies.miriade_engine import fetch as fetch_miriade
from scripts.bodies.swiss_engine import fetch as fetch_swiss
from scripts.utils.zodiac import zodiac_sign, degree_in_sign
from scripts.utils.harmonics import harmonics
from scripts.fixed_stars import get_fixed_star_positions
import os

BODIES = [
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Chiron",
    "Ceres", "Pallas", "Juno", "Vesta", "Psyche", "Amor", "Eros", "Astraea", "Sappho", "Hygiea", "Karma", "Bacchus",
    "Eris", "Sedna", "Haumea", "Makemake", "Quaoar", "Varuna", "Ixion", "Orcus", "Salacia", "Typhon", "2002 AW197", "2003 VS2"
]
# Add or update as needed

def fetch_body_data(body, timestamp):
    data = fetch_horizons(body, timestamp)
    if data is None:
        data = fetch_miriade(body, timestamp)
    if data is None:
        data = fetch_swiss(body, timestamp)
    return data

def compute_transits(ts):
    # Output strictly follows: { body: { lon, lat, retrograde, sign, deg_in_sign, harmonics, ... } }
    result = {}
    for body in BODIES:
        ephem = fetch_body_data(body, ts)
        if ephem is None:
            continue
        lon = ephem["lon"]
        lat = ephem["lat"]
        retrograde = ephem["retrograde"]
        sign = zodiac_sign(lon)
        deg = degree_in_sign(lon)
        harm = harmonics(lon)
        # No actual house calculation; put None for now. Add if implemented.
        result[body] = {
            "lon": lon, "lat": lat, "retrograde": retrograde,
            "sign": sign, "deg": deg, "house": None,
            "harmonics": harm
        }
    # Add fixed stars, placeholder harmonics
    for star in get_fixed_star_positions():
        lon = star["longitude"]
        sign = zodiac_sign(lon)
        deg = degree_in_sign(lon)
        result[star["name"]] = {
            "lon": lon, "lat": 0.0, "retrograde": False,
            "sign": sign, "deg": deg, "house": None,
            "harmonics": harmonics(lon)
        }
    return result

def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def generate_all_feeds():
    now = datetime.utcnow().replace(microsecond=0)
    ts_now = now.isoformat() + "Z"
    ts_list = [now + timedelta(days=i) for i in range(7)]
    # Single now, daily (7 days), week, weekly
    feeds = {
        "feed_now.json": [{"timestamp": ts_now, "transits": compute_transits(ts_now)}],
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
    for fn, feed_data in feeds.items():
        write_json(os.path.join("docs", fn), feed_data)

    # Optional metadata
    write_json(os.path.join("docs", "metadata.json"), {
        "generated_utc": datetime.utcnow().isoformat() + "Z",
        "bodies": BODIES,
        "fixed_stars": [star["name"] for star in get_fixed_star_positions()],
    })

if __name__ == "__main__":
    generate_all_feeds()
