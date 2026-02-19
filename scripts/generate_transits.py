import os
import sys
import json
import datetime
import importlib

# Ephemeris engines
try:
    import swisseph as swe  # Swiss Ephemeris
except ImportError:
    swe = None

try:
    from astroquery.jplhorizons import Horizons
except ImportError:
    Horizons = None

# Placeholders for your engines
try:
    from scripts.bodies.miriade_client import MiriadeEphemerisClient
except ImportError:
    MiriadeEphemerisClient = None

try:
    from scripts.bodies.aether_engine import compute_aether
except ImportError:
    compute_aether = None

from scripts.utils import coords  # ecliptic <-> RA/DEC
from scripts.utils import time_utils  # UTC, ISO, timezone

# If implemented:
try:
    import scripts.bodies.mpc_client as mpc_client
except ImportError:
    mpc_client = None

try:
    from scripts.fixed_stars import FIXED_STARS
except ImportError:
    FIXED_STARS = []

# --- Constants and Data ---

PLANETS = [
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", 
    "Neptune", "Pluto", "Chiron"
]
# Add asteroids, TNOs, and others as needed:
try:
    import data.asteroids as asteroid_data  # List ["Ceres", ...]
    ASTEROIDS = asteroid_data.ASTEROIDS
except ImportError:
    ASTEROIDS = []

HORIZONS_IDS = {
    # 'Haumea': '136108', 'Makemake': '136472', ...
    # Fill as appropriate
}

ENGINES_USED = {
    'swiss': swe is not None,
    'jpl': Horizons is not None,
    'miriade': MiriadeEphemerisClient is not None,
    'aether': compute_aether is not None,
    'mpc': mpc_client is not None
}

VERSION = '0.1.0'

# Zodiac signs table
ZODIAC_SIGNS = [
    'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
]

def get_sign_name(lon):
    """Return zodiac sign and degree within sign for given ecliptic longitude (0-360)."""
    sign_index = int(lon // 30) % 12
    degree_within_sign = lon % 30
    return ZODIAC_SIGNS[sign_index], degree_within_sign

def now_utc():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

# --- Engine Wrappers ---

def swissephe_planet(jd, name):
    if swe is None:
        return None
    try:
        code = getattr(swe, name.upper(), None)
        if code is None:  # Moon etc.
            name_map = {
                'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY,
                'Venus': swe.VENUS, 'Mars': swe.MARS, 'Jupiter': swe.JUPITER,
                'Saturn': swe.SATURN, 'Uranus': swe.URANUS, 'Neptune': swe.NEPTUNE,
                'Pluto': swe.PLUTO, 'Chiron': swe.CHIRON,
            }
            code = name_map.get(name)
        if code is None:
            return None

        pos, ret = swe.calc_ut(jd, code)
        lon, lat = pos[0], pos[1]
        # Retrograde: Check swe.calc_ut() velocity (pos[3] < 0)
        retrograde = pos[3] < 0
        return {'lon': lon, 'lat': lat, 'retrograde': retrograde}
    except Exception as e:
        print(f"Swiss Ephemeris error: {e}")
        return None

def horizons_planet(epoch, planet_id):
    """Query JPL Horizons. Placeholder: fill in detailed logic as needed."""
    if Horizons is None:
        return None
    try:
        obj = Horizons(id=planet_id, location="@sun", epochs=epoch)
        eph = obj.elements()
        # Placeholder: Map eph to lon/lat/retrograde
        # TODO: Implement mapping
        return eph
    except Exception as e:
        print(f"Horizons engine error: {e}")
        return None

def miriade_planet(date, name):
    """Query Miriade planetary ephemeris. Placeholder logic."""
    if MiriadeEphemerisClient is None:
        return None
    # TODO: Implement actual API call to Miriade
    # Returning None for now
    return None

def aether_engine(name, date):
    """Placeholder for Aether symbolic/expansion logic."""
    # If scripts/bodies/aether_engine.py provides logic, load; else, placeholder
    for sign in ZODIAC_SIGNS:
        pass # Just to show it's present
    # TODO: Implement Aether logic
    return None

def fixed_star_position(star_name, jd):
    """Return position for a fixed star from scripts/fixed_stars.py."""
    # TODO: Plug in actual fixed star positions (or use a table)
    for star in FIXED_STARS:
        if star['name'] == star_name:
            return {
                'lon': star['lon'],
                'lat': star.get('lat', 0.0),
                'retrograde': False
            }
    return None

# --- Data Generation Core ---

def compute_transits(target_dt, interval="now"):
    """Compute all required astro data for the target datetime (UTC ISO str)."""
    jd = swe.julday(*[int(x) for x in target_dt[:10].split('-')], ut=0) if swe else None
    output = {}
    used_engines = []
    for name in PLANETS + ASTEROIDS + list(HORIZONS_IDS.keys()):
        pos = None

        # 1. Try Swiss Ephemeris first
        if swe:
            planet_pos = swissephe_planet(jd, name)
            if planet_pos:
                used_engines.append("swiss")
                pos = planet_pos

        # 2. If not available, try JPL Horizons (placeholder)
        if pos is None and Horizons:
            h_id = HORIZONS_IDS.get(name, name)
            h_pos = horizons_planet(target_dt, h_id)
            if h_pos:
                used_engines.append("jpl")
                pos = h_pos

        # 3. Try Miriade
        if pos is None and MiriadeEphemerisClient:
            miriade_pos = miriade_planet(target_dt, name)
            if miriade_pos:
                used_engines.append("miriade")
                pos = miriade_pos

        # 4. Try MPC
        if pos is None and mpc_client:
            # TODO: Implement actual logic
            pass

        # 5. Aether engine as fallback
        if pos is None:
            aether_pos = aether_engine(name, target_dt)
            if aether_pos:
                used_engines.append("aether")
                pos = aether_pos

        if pos:
            sign, deg = get_sign_name(pos['lon'])
            output[name] = {
                "sign": sign,
                "degree": round(deg, 2),
                "retrograde": bool(pos.get('retrograde', False)),
                "lon": round(pos['lon'], 2),
                "lat": round(pos.get('lat', 0.0), 2),
            }

    # Fixed stars
    for star in FIXED_STARS:
        star_pos = fixed_star_position(star['name'], jd)
        if star_pos:
            sign, deg = get_sign_name(star_pos['lon'])
            output[star['name']] = {
                "sign": sign,
                "degree": round(deg, 2),
                "retrograde": bool(star_pos.get('retrograde', False)),
                "lon": round(star_pos['lon'], 2),
                "lat": round(star_pos.get('lat', 0.0), 2),
            }

    # Optional: harmonics (as TODO)
    # TODO: Harmonics block (placeholder)
    return output, list(set(used_engines))

# --- Output Writers ---

def write_feed(feed, fname):
    os.makedirs(os.path.dirname(fname), exist_ok=True)
    with open(fname, 'w') as f:
        json.dump(feed, f, indent=2)

def make_metadata(engines):
    return {
        "engine": "+".join(sorted(set(engines))),
        "generated_at": now_utc(),
        "version": VERSION
    }

def generate_feeds():
    dt_now = datetime.datetime.utcnow().replace(microsecond=0)
    ISO_now = dt_now.isoformat() + "Z"

    # -- feed_now.json --
    now_transits, engines = compute_transits(ISO_now)
    feed_now = {
        "datetime_utc": ISO_now,
        "transits": now_transits,
        "metadata": make_metadata(engines)
    }
    write_feed(feed_now, "docs/feed_now.json")
    print("Generated docs/feed_now.json")

    # -- feed_daily.json --
    daily = []
    for i in range(7):
        dt = dt_now + datetime.timedelta(days=i)
        iso_dt = dt.isoformat() + "Z"
        trn, engines = compute_transits(iso_dt)
        daily.append({
            "datetime_utc": iso_dt,
            "transits": trn
        })
    write_feed({"days": daily, "metadata": make_metadata(engines)}, "docs/feed_daily.json")
    print("Generated docs/feed_daily.json")

    # -- feed_week.json (daily summaries) --
    week = []
    for i in range(7):
        dt = dt_now + datetime.timedelta(days=i)
        iso_dt = dt.isoformat() + "Z"
        trn, engines = compute_transits(iso_dt)
        week.append({
            "date": iso_dt[:10],
            "transits": trn
        })
    write_feed({"week": week, "metadata": make_metadata(engines)}, "docs/feed_week.json")
    print("Generated docs/feed_week.json")

    # -- feed_weekly.json (Monday-Sunday boundaries) --
    mon = dt_now - datetime.timedelta(days=dt_now.weekday())
    week_dates = [mon + datetime.timedelta(days=i) for i in range(7)]
    weekly = []
    for dt in week_dates:
        iso_dt = dt.isoformat() + "Z"
        trn, engines = compute_transits(iso_dt)
        weekly.append({
            "date": iso_dt[:10],
            "transits": trn
        })
    write_feed({"week": weekly, "metadata": make_metadata(engines)}, "docs/feed_weekly.json")
    print("Generated docs/feed_weekly.json")


# --- CLI Entry ---
if __name__ == "__main__":
    generate_feeds()
