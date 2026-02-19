
"""
Dual House System Engine:
- Whole Sign Houses
- Placidus Houses

Supports:
- True Ascendant from Local Sidereal Time (LST)
- MC / IC calculation
- 12 house cusps for both systems
"""

import math


# -----------------------------------------------------------
#  BASIC ASTRONOMICAL UTILITIES
# -----------------------------------------------------------

def deg2rad(d): return math.radians(d)
def rad2deg(r): return (math.degrees(r) % 360)


def julian_date_from_iso(iso_ts):
    """
    Convert ISO timestamp → Julian Date.
    """
    from datetime import datetime, timezone
    dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00")).astimezone(timezone.utc)
    year = dt.year
    month = dt.month
    day = dt.day + (dt.hour + dt.minute/60 + dt.second/3600)/24

    if month <= 2:
        year -= 1
        month += 12

    A = math.floor(year / 100)
    B = 2 - A + math.floor(A / 4)
    jd = math.floor(365.25*(year + 4716)) + math.floor(30.6001*(month + 1)) + day + B - 1524.5
    return jd


def gmst(jd):
    """
    Greenwich Mean Sidereal Time (in degrees).
    """
    T = (jd - 2451545.0) / 36525
    GMST = 280.46061837 \
         + 360.98564736629 * (jd - 2451545.0) \
         + 0.000387933 * T*T \
         - (T*T*T) / 38710000
    return GMST % 360


def local_sidereal_time(jd, lon_deg):
    """
    Local sidereal time in degrees.
    lon_deg = observer longitude (east positive, west negative)
    """
    return (gmst(jd) + lon_deg) % 360


# -----------------------------------------------------------
#  ASCENDANT & MC CALCULATION
# -----------------------------------------------------------

def compute_ascendant(jd, lat_deg, lon_deg):
    """
    True Ascendant from LST & latitude.
    """
    eps = deg2rad(23.439291)  # obliquity
    lat = deg2rad(lat_deg)
    lst = deg2rad(local_sidereal_time(jd, lon_deg))

    # ASC formula
    tan_asc = -math.cos(lst) / (math.sin(lst)*math.cos(eps) + math.tan(lat)*math.sin(eps))
    asc = math.atan(tan_asc)

    # Adjust quadrant
    if math.cos(lst) > 0:
        asc = asc + math.pi

    return rad2deg(asc)


def compute_mc(jd, lon_deg):
    """
    Midheaven from sidereal time.
    """
    eps = deg2rad(23.439291)
    lst = deg2rad(local_sidereal_time(jd, lon_deg))
    mc = math.atan2(math.cos(lst), math.sin(lst)*math.cos(eps))
    return rad2deg(mc)


# -----------------------------------------------------------
#  WHOLE SIGN HOUSE SYSTEM
# -----------------------------------------------------------

def whole_sign_cusps(asc_lon):
    """
    House 1 begins at the sign of the Ascendant.
    """
    asc_sign = int(asc_lon // 30)
    return {i+1: ((asc_sign + i) % 12) * 30 for i in range(12)}


def whole_sign_house(lon, asc_lon):
    asc_sign = int(asc_lon // 30)
    body_sign = int(lon // 30)
    return (body_sign - asc_sign) % 12 + 1


# -----------------------------------------------------------
#  PLACIDUS HOUSE SYSTEM
# -----------------------------------------------------------

def placidus_cusps(jd, lat_deg, lon_deg):
    """
    Computes Placidus house cusps.
    Returns dict: {1: cusp1_lon, 2: cusp2_lon, ..., 12: cusp12_lon}
    """

    eps = deg2rad(23.439291)
    lat = deg2rad(lat_deg)

    lst = deg2rad(local_sidereal_time(jd, lon_deg))

    # Compute MC
    mc = compute_mc(jd, lon_deg)
    mc_rad = deg2rad(mc)

    cusps = {10: mc}

    # Houses 11, 12, 1, 2, 3
    for house, angle in zip([11, 12, 1, 2, 3], [mc_rad + math.pi/6, mc_rad + math.pi/3, mc_rad + math.pi/2, mc_rad + 2*math.pi/3, mc_rad + 5*math.pi/6]):
        RA = angle % (2*math.pi)
        tan_ecl = math.atan(math.tan(RA) * math.cos(eps))
        lon = rad2deg(tan_ecl)
        cusps[house] = lon

    # Opposites
    cusps[4] = (cusps[10] + 180) % 360
    cusps[5] = (cusps[11] + 180) % 360
    cusps[6] = (cusps[12] + 180) % 360
    cusps[7] = (cusps[1]  + 180) % 360
    cusps[8] = (cusps[2]  + 180) % 360
    cusps[9] = (cusps[3]  + 180) % 360

    # Order them 1..12
    return {i: cusps[i] for i in range(1, 13)}


def placidus_house(lon, cusps):
    """
    Determine which Placidus house a longitude belongs to.
    """
    for h in range(1, 13):
        start = cusps[h]
        end = cusps[1] if h == 12 else cusps[h+1]
        if start <= end:
            if start <= lon < end:
                return h
        else:
            if lon >= start or lon < end:
                return h
    return None
