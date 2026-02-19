import math

def equatorial_to_ecliptic(ra_deg, dec_deg, obliquity_deg=23.439281):
    ra = math.radians(ra_deg)
    dec = math.radians(dec_deg)
    ob = math.radians(obliquity_deg)

    sin_ecl_lat = math.sin(dec)*math.cos(ob) - math.cos(dec)*math.sin(ob)*math.sin(ra)
    ecl_lat = math.asin(sin_ecl_lat)

    y = math.sin(ra)*math.cos(ob) + math.tan(dec)*math.sin(ob)
    x = math.cos(ra)
    ecl_lon = math.atan2(y, x)

    return math.degrees(ecl_lon) % 360, math.degrees(ecl_lat)
"""
Coordinate Transformation Utilities

TODO:
    - Implement ecliptic <-> RA/DEC conversions using math utils.
    - Provide accurate astronomical coordinate conversions for all ephemeris engines.
"""
