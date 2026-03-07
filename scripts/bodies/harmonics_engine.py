
import numpy as np


def compute_harmonics(longitudes):

    lons = np.array(longitudes)

    return {
        "h5": (lons * 5) % 360,
        "h7": (lons * 7) % 360,
        "h9": (lons * 9) % 360
    }
