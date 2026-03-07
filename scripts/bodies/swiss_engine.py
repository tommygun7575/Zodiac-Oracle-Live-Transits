import os
import swisseph as swe

# Use Moshier fallback if no ephemeris files exist
EPHE_PATH = os.getenv("SWISSEPH_EPHE_PATH", "ephe")
os.makedirs(EPHE_PATH, exist_ok=True)
swe.set_ephe_path(EPHE_PATH)

PLANET_MAP = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
}

def get_planet(body, jd):
    try:
        code = PLANET_MAP[body]
        pos, _ = swe.calc_ut(jd, code)
        return pos[0], pos[1], "swiss"
    except Exception:
        return None

def get_asteroid(number, jd):
    try:
        pos, _ = swe.calc_ut(jd, swe.AST_OFFSET + number)
        return pos[0], pos[1], "swiss"
    except Exception:
        return None
