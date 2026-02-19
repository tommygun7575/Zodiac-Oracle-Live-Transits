"""
Real JPL Horizons Ephemeris Engine
Provides TRUE planetary and TNO positions using the NASA/JPL Horizons system.
Includes real orbital velocity + retrograde detection.
"""

from astroquery.jplhorizons import Horizons
from scripts.utils.coord import equatorial_to_ecliptic


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

TNO_TARGETS = {
    "Eris": "Eris",
    "Haumea": "Haumea",
    "Makemake": "Makemake",
    "Sedna": "Sedna",
    "Quaoar": "Quaoar",
    "Orcus": "Orcus",
    "Salacia": "Salacia",
    "Ixion": "Ixion",
    "Varuna": "Varuna",
    "Typhon": "Typhon",
    "2002 AW197": "2002 AW197",
    "2003 VS2": "2003 VS2",
}


def fetch(body_name, iso_utc_timestamp):
    """
    Returns:
        {
            "lon": float,
            "lat": float,
            "retrograde": bool,
            "speed": float
        }
    """

    if body_name in PLANET_IDS:
        target = PLANET_IDS[body_name]
    elif body_name in TNO_TARGETS:
        target = TNO_TARGETS[body_name]
    else:
        return None

    try:
        obj = Horizons(
            id=target,
            location="500@0",
            epochs=iso_utc_timestamp,
            quantities="1,2"     # <-- REQUIRED to get RA_rate and DEC_rate
        )

        eph = obj.ephemerides()

        ra = float(eph["RA"][0])
        dec = float(eph["DEC"][0])

        lon, lat = equatorial_to_ecliptic(ra, dec)

        # -----------------------------------------------------
        # TRUE SPEED CALCULATION
        # -----------------------------------------------------
        try:
            # arcsec/hour → degrees/day
            dra = float(eph["RA_rate"][0]) / 3600.0
            ddec = float(eph["DEC_rate"][0]) / 3600.0

            ra_prev = ra - dra
            dec_prev = dec - ddec

            lon_prev, lat_prev = equatorial_to_ecliptic(ra_prev, dec_prev)

            speed = lon - lon_prev

            if speed > 180:
                speed -= 360
            elif speed < -180:
                speed += 360

            retrograde = speed < 0

        except Exception:
            speed = 0.0
            retrograde = False

        return {
            "lon": lon,
            "lat": lat,
            "retrograde": retrograde,
            "speed": speed
        }

    except Exception:
        return None
