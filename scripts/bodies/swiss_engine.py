import swisseph as swe
from datetime import datetime, timedelta

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

def fetch_swiss(body, start, stop):

    if body not in PLANETS:
        raise RuntimeError("unsupported body")

    start_dt = datetime.strptime(start, "%Y-%m-%d")

    vectors = []

    for i in range(7):

        day = start_dt + timedelta(days=i)

        jd = swe.julday(day.year, day.month, day.day)

        pos, flags = swe.calc_ut(jd, PLANETS[body])

        lon = float(pos[0])
        lat = float(pos[1])

        vectors.append((lon, lat))

    return vectors
