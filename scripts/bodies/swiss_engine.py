import swisseph as swe
from datetime import datetime, timedelta

swe.set_ephe_path(".")

SWISS_BODY_MAP = {
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

def get_swiss_week(body_name, start_date, stop_date, step_days):

    if body_name not in SWISS_BODY_MAP:
        raise RuntimeError("Swiss does not support this body")

    body = SWISS_BODY_MAP[body_name]

    start = datetime.strptime(start_date, "%Y-%m-%d")
    stop = datetime.strptime(stop_date, "%Y-%m-%d")

    current = start
    results = []

    while current <= stop:
        jd = swe.julday(current.year, current.month, current.day)
        lon = swe.calc_ut(jd, body)[0][0]

        results.append({
            "date": current.strftime("%Y-%m-%d"),
            "longitude_deg": lon
        })

        current += timedelta(days=step_days)

    return results
