#import swisseph as swe
from datetime import datetime
from scripts.utils.coord import equatorial_to_ecliptic

# Extend for custom bodies as necessary
PLANET_CODES = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY, "Venus": swe.VENUS, "Mars": swe.MARS,
    "Jupiter": swe.JUPITER, "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO, "Ceres": 1, "Pallas": 2, "Juno": 3, "Vesta": 4,
    "Chiron": swe.CHIRON if hasattr(swe, "CHIRON") else 15,
    # For asteroids/TNOs provide Swiss numbering as supported
}

def _jd_from_iso(iso_utc_timestamp):
    try:
        dt = datetime.fromisoformat(iso_utc_timestamp.replace('Z', '+00:00'))
        jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60 + dt.second/3600)
        return jd
    except Exception:
        return None

def fetch(body_name, iso_utc_timestamp):
    jd = _jd_from_iso(iso_utc_timestamp)
    if jd is None:
        return None
    planet = PLANET_CODES.get(body_name)
    if planet is None:
        # Try integer: for TNOs/minor planets
        try:
            planet = int(body_name)
        except Exception:
            planet = swe.SUN
    try:
        res, retflags = swe.calc_ut(jd, planet, swe.FLG_SWIEPH | swe.FLG_ECLIPTIC)
        lon, lat, speed_lon = res[0], res[1], res[3]
        retrograde = speed_lon < 0
        return {"lon": lon, "lat": lat, "retrograde": retrograde}
    except Exception:
        try:
            res, retflags = swe.calc_ut(jd, planet, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)
            ra, dec = res[0], res[1]
            lon, lat = equatorial_to_ecliptic(ra, dec)
            return {"lon": lon, "lat": lat, "retrograde": False}
        except Exception:
            return None Swiss Ephemeris Client
# TODO: Implement wrapper for Swiss Ephemeris API.
