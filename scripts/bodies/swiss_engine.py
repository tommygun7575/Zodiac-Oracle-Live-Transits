import swisseph as swe

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

ASTEROID_IDS = {
    "Ceres": 1,
    "Pallas": 2,
    "Juno": 3,
    "Vesta": 4,
    "Chiron": 2060,
    "Pholus": 5145,
    "Nessus": 7066,
    "Quaoar": 50000,
    "Orcus": 90482,
    "Sedna": 90377,
    "Ixion": 28978
}


def get_planet(name, jd):

    try:

        pid = PLANETS[name]

        pos, _ = swe.calc_ut(jd, pid)

        lon = pos[0]
        lat = pos[1]

        return lon, lat, "swiss"

    except:
        return None


def get_asteroid(name, jd):

    try:

        aid = ASTEROID_IDS[name]

        pos, _ = swe.calc_ut(jd, swe.AST_OFFSET + aid)

        lon = pos[0]
        lat = pos[1]

        return lon, lat, "swiss"

    except:
        return None
