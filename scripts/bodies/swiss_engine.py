import swisseph as swe
from datetime import datetime

# -------------------------------------------------------
# planet id map
# -------------------------------------------------------

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
    "Pluto": swe.PLUTO
}

# -------------------------------------------------------
# convert ISO timestamp to julian day
# -------------------------------------------------------

def iso_to_jd(timestamp):

    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    jd = swe.julday(
        dt.year,
        dt.month,
        dt.day,
        dt.hour + dt.minute / 60 + dt.second / 3600
    )

    return jd


# -------------------------------------------------------
# MAIN FUNCTION
# -------------------------------------------------------

def fetch_swiss_position(body, timestamp):

    if body not in PLANET_MAP:
        raise Exception(f"Swiss does not support body: {body}")

    planet_id = PLANET_MAP[body]

    jd = iso_to_jd(timestamp)

    result, _ = swe.calc_ut(jd, planet_id)

    lon = result[0]
    lat = result[1]

    return {
        "ecl_lon_deg": float(lon),
        "ecl_lat_deg": float(lat)
    }
