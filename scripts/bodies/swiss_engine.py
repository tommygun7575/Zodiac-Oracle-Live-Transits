import swisseph as swe
from datetime import datetime, timedelta


BODY_CODES = {
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


def fetch_swiss(body, start, stop):

    if body not in BODY_CODES:
        raise RuntimeError(f"Swiss ephemeris unsupported body {body}")

    start_dt = datetime.strptime(start, "%Y-%m-%d")

    results = []

    for i in range(7):

        day = start_dt + timedelta(days=i)

        jd = swe.julday(day.year, day.month, day.day)

        lon, lat, dist = swe.calc_ut(jd, BODY_CODES[body])[0]

        results.append((lon, lat))

    return results
