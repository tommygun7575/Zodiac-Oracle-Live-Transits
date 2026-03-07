import numpy as np

FIXED_STARS = {
    "Regulus": 150.0,
    "Spica": 204.0,
    "Antares": 250.0,
    "Aldebaran": 69.0
}


def detect_star_hits(longitudes):

    lons = np.array(longitudes)

    hits = {}

    for star, pos in FIXED_STARS.items():
        hits[star] = np.abs(lons - pos) < 1.0

    return hits
