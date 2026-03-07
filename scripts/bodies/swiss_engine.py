import swisseph as swe

swe.set_ephe_path(".")

PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO
}

def get_planet(body, jd):

    if body not in PLANETS:
        return None

    try:

        lon, lat, _ = swe.calc_ut(jd, PLANETS[body])

        return lon, lat

    except:

        return None


def get_asteroid(number, jd):

    try:

        lon, lat, _ = swe.calc_ut(jd, number + swe.AST_OFFSET)

        return lon, lat

    except:

        return None
