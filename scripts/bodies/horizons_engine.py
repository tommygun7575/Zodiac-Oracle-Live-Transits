"""
Real JPL Horizons Ephemeris Engine
Returns TRUE planetary positions with correct RA/DEC
and converts them into ecliptic coordinates.
"""

from astroquery.jplhorizons import Horizons
from scripts.utils.coord import equatorial_to_ecliptic

# ID numbers for planets for Horizons API
PLANET_IDS = {
    "Sun": 10,
    "Moon": 301,
    "Mercury": 199,
    "Venus": 299,
    "Mars": 499,
    "Jupiter": 599,
    "Saturn": 699,
    "Uranus": 799,
    "Neptune": 899,
    "Pluto": 999,
}

def fetch(body_name, iso_utc_timestamp):
    """
    Fetch REAL planetary positions from JPL Horizons.
    """

    if body_name not in PLANET_IDS:
        return None

    obj_id = PLANET_IDS[body_name]

    # Query JPL Horizons
    try:
        obj = Horizons(
            id=obj_id,
            location="500@0",      # geocentric
            epochs=iso_utc_timestamp
        )

        eph = obj.ephemerides()

        # RA / DEC (true center)
        ra = float(eph["RA"][0])          # degrees
        dec = float(eph["DEC"][0])        # degrees

        # Convert RA/DEC → ecliptic lon/lat
        lon, lat = equatorial_to_ecliptic(ra, dec)

        # Compute retrograde from delta-longitude
        try:
            lon_prev, _ = equatorial_to_ecliptic(
                float(eph["RA_rate"][0] * -1 + ra),
                float(eph["DEC_rate"][0] * -1 + dec)
            )
            retrograde = lon_prev > lon
        except Exception:
            retrograde = False

        return {
            "lon": lon,
            "lat": lat,
            "retrograde": retrograde
        }

    except Exception as e:
        return None
