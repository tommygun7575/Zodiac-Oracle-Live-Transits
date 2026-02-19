# """
Fixed Star Position Provider
Returns ecliptic longitudes for major fixed stars used in overlays.
Values are approximate but stable for astrological processing.
"""

# Fixed star longitudes (approx, J2000)
FIXED_STARS = {
    "Regulus":      149.83,
    "Spica":        203.84,
    "Aldebaran":     69.79,
    "Antares":      249.76,
    "Algol":         56.17,
    "Arcturus":     204.23,
    "Betelgeuse":    88.75,
    "Canopus":      104.96,
    "Capella":       81.86,
    "Deneb":        335.33,
    "Fomalhaut":    333.86,
    "Pollux":       113.22,
    "Procyon":      115.79,
    "Rigel":         76.83,
    "Sirius":       104.08,
    "Vega":         285.32,
    "Zubenelgenubi":225.04,
    "Zubeneschamali":229.37
}

def get_fixed_star_positions():
    """
    Returns a dict of fixed star → ecliptic longitude (degrees).
    """
    return FIXED_STARS.copy()
Fixed Star Longitude Updates Module

# This module contains functions to update the longitudes of fixed stars.
