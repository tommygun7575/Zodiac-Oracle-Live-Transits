"""
Zodiac helper functions for converting ecliptic longitude
into sign name and degree position within the sign.
"""

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

def zodiac_sign(ecl_lon):
    """
    Returns the zodiac sign name based on ecliptic longitude (0–360 degrees).
    """
    if ecl_lon is None:
        return None
    index = int(ecl_lon // 30) % 12
    return ZODIAC_SIGNS[index]

def degree_in_sign(ecl_lon):
    """
    Returns the degree inside the sign (0–30 degrees).
    """
    if ecl_lon is None:
        return None
    return float(ecl_lon % 30)
