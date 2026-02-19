"""
Coordinate Transformation Utilities
Provides accurate astronomical coordinate conversions needed
for JPL Horizons → Ecliptic longitude/latitude processing.
"""

import math

# -------------------------
# Unit helpers
# -------------------------

def deg_to_rad(deg):
    return math.radians(deg)

def rad_to_deg(rad):
    return math.degrees(rad)

# -------------------------
# Core Transform:
# RA/DEC → Ecliptic Lon/Lat
# -------------------------
def equatorial_to_ecliptic(ra_deg, dec_deg, obliquity_deg=23.439281):
    """
    Convert Right Ascension (RA) and Declination (DEC)
    to Ecliptic Longitude and Latitude using standard
    IAU astronomical formulas.

    Parameters:
        ra_deg (float): Right Ascension in degrees
        dec_deg (float): Declination in degrees
        obliquity_deg (float): Mean obliquity of the ecliptic (Earth's tilt)

    Returns:
        (ecl_lon_deg, ecl_lat_deg): Tuple of ecliptic longitude/latitude in degrees
    """

    # Convert to radians
    ra = deg_to_rad(ra_deg)
    dec = deg_to_rad(dec_deg)
    ob = deg_to_rad(obliquity_deg)

    # Latitude (β)
    sin_beta = math.sin(dec) * math.cos(ob) - math.cos(dec) * math.sin(ob) * math.sin(ra)
    beta = math.asin(sin_beta)

    # Longitude (λ)
    y = math.sin(ra) * math.cos(ob) + math.tan(dec) * math.sin(ob)
    x = math.cos(ra)
    lam = math.atan2(y, x)

    # Convert back to degrees
    ecl_lon = rad_to_deg(lam) % 360
    ecl_lat = rad_to_deg(beta)

    return ecl_lon, ecl_lat

# -------------------------
# Optional reverse transform:
# Ecliptic → RA/DEC
# -------------------------
def ecliptic_to_equatorial(lon_deg, lat_deg, obliquity_deg=23.439281):
    """
    Convert Ecliptic Longitude/Latitude back into
    Right Ascension and Declination.
    """

    lon = deg_to_rad(lon_deg)
    lat = deg_to_rad(lat_deg)
    ob = deg_to_rad(obliquity_deg)

    sin_dec = math.sin(lat) * math.cos(ob) + math.cos(lat) * math.sin(ob) * math.sin(lon)
    dec = math.asin(sin_dec)

    y = math.sin(lon) * math.cos(ob) - math.tan(lat) * math.sin(ob)
    x = math.cos(lon)
    ra = math.atan2(y, x)

    ra_deg = rad_to_deg(ra) % 360
    dec_deg = rad_to_deg(dec)

    return ra_deg, dec_deg
