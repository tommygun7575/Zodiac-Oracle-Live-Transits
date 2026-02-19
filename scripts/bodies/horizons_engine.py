"""
Real JPL Horizons Ephemeris Engine
Provides TRUE planetary and TNO positions using the NASA/JPL Horizons system.
Converts RA/DEC into ecliptic longitude/latitude for full astrological use.
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
# These resolve correctly in Horizons for full ephemerides.
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
# MAIN FETCH ENGINE
# ---------------------------------------------------------
def fetch(body_name, iso_utc_timestamp):
    """
    Fetch REAL ephemeris data for major planets AND TNOs using JPL Horizons.
    Returns:
        {"lon": float, "lat": float, "retrograde": bool}
    """

    # Determine target for Horizons
    if body_name in PLANET_IDS:
        target = PLANET_IDS[body_name]
    elif body_name in TNO_TARGETS:
        target = TNO_TARGETS[body_name]
    else:
        return None

    try:
        # Query real NASA ephemeris
        obj = Horizons(
            id=target,
            location="500@0",  # geocentric observer
            epochs=iso_utc_timestamp
        )

        eph = obj.ephemerides()

        # Extract positions
        ra = float(eph["RA"][0])      # Right Ascension (deg)
        dec = float(eph["DEC"][0])    # Declination (deg)

        # Convert to ecliptic
        lon, lat = equatorial_to_ecliptic(ra, dec)

        # Retrograde determination
        try:
            dra = float(eph["RA_rate"][0])
            ddec = float(eph["DEC_rate"][0])
            lon_prev, _ = equatorial_to_ecliptic(ra - dra, dec - ddec)
            retrograde = lon_prev > lon
        except Exception:
            retrograde = False

        return {
            "lon": lon,
            "lat": lat,
            "retrograde": retrograde
        }

    except Exception:
        return None
