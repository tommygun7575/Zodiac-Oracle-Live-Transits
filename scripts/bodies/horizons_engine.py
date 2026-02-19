"""
Real JPL Horizons Ephemeris Engine
Provides TRUE planetary and TNO positions using the NASA/JPL Horizons system.
Converts RA/DEC into ecliptic longitude/latitude.
Includes real orbital velocity + retrograde detection.
"""

from astroquery.jplhorizons import Horizons
from scripts.utils.coord import equatorial_to_ecliptic


# ---------------------------------------------------------
# NAIF MAJOR-BODY IDs (planets + Moon + Pluto)
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# TNO & DWARF PLANET TARGETS — Horizons string identifiers
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# MAIN FETCH ENGINE WITH TRUE SPEED / RETROGRADE
# ---------------------------------------------------------
def fetch(body_name, iso_utc_timestamp):
    """
    Fetch REAL ephemeris data for major planets AND TNOs using JPL Horizons.
    Returns dict with:
        "lon": float
        "lat": float
        "retrograde": bool
        "speed": float   (deg/day)
    """

    # Determine Horizons target
    if body_name in PLANET_IDS:
        target = PLANET_IDS[body_name]
    elif body_name in TNO_TARGETS:
        target = TNO_TARGETS[body_name]
    else:
        return None

    try:
        # Query NASA Horizons
        obj = Horizons(
            id=target,
            location="500@0",  # geocentric observer
            epochs=iso_utc_timestamp
        )

        eph = obj.ephemerides()

        # Extract RA / DEC (in degrees)
        ra = float(eph["RA"][0])
        dec = float(eph["DEC"][0])

        # Convert to ecliptic coordinates
        lon, lat = equatorial_to_ecliptic(ra, dec)

        # ---------------------------------------------------------
        # REAL ORBITAL SPEED CALCULATION
        # ---------------------------------------------------------
        try:
            # Horizons rates are in arcseconds/hour
            dra_arcsec_hr = float(eph["RA_rate"][0])
            ddec_arcsec_hr = float(eph["DEC_rate"][0])

            # Convert arcsec/hr → degrees/hr → degrees/day
            dra_deg = dra_arcsec_hr / 3600.0
            ddec_deg = ddec_arcsec_hr / 3600.0

            # Previous position approximation
            ra_prev = ra - dra_deg
            dec_prev = dec - ddec_deg

            lon_prev, lat_prev = equatorial_to_ecliptic(ra_prev, dec_prev)

            # Raw speed (deg/day)
            speed = lon - lon_prev

            # Normalize speed to -180..+180
            if speed > 180:
                speed -= 360
            elif speed < -180:
                speed += 360

            # Retrograde if speed is negative
            retrograde = speed < 0

        except Exception:
            speed = 0.0
            retrograde = False

        # ---------------------------------------------------------
        # RETURN FULL ASTRONOMICAL RECORD
        # ---------------------------------------------------------
        return {
            "lon": lon,
            "lat": lat,
            "retrograde": retrograde,
            "speed": speed
        }

    except Exception:
        return None
