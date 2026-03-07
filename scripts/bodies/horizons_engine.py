import math
import numpy as np
from astroquery.jplhorizons import Horizons


HORIZONS_IDS = {
    "Sun": "10",
    "Moon": "301",
    "Mercury": "199",
    "Venus": "299",
    "Mars": "499",
    "Jupiter": "599",
    "Saturn": "699",
    "Uranus": "799",
    "Neptune": "899",
    "Pluto": "999",
    "Ceres": "1",
    "Pallas": "2",
    "Juno": "3",
    "Vesta": "4",
    "Eris": "136199",
    "Haumea": "136108",
    "Makemake": "136472",
    "Sedna": "90377",
    "Orcus": "90482",
    "Quaoar": "50000",
    "Ixion": "28978"
}


def fetch_batch(body, start, stop):

    try:

        body_id = HORIZONS_IDS.get(body)

        if body_id is None:
            raise RuntimeError(f"No Horizons ID for {body}")

        obj = Horizons(
            id=body_id,
            location="500@399",
            epochs={
                "start": start,
                "stop": stop,
                "step": "1d"
            }
        )

        eph = obj.ephemerides()

        if eph is None or len(eph) == 0:
            raise RuntimeError(f"Horizons returned empty ephemeris for {body}")

        vectors = []

        for row in eph:

            lon = row["EclLon"]
            lat = row["EclLat"]

            if lon is None or lat is None:
                continue

            if isinstance(lon, np.ma.core.MaskedConstant):
                continue

            if isinstance(lat, np.ma.core.MaskedConstant):
                continue

            lon = float(lon)
            lat = float(lat)

            if math.isnan(lon) or math.isnan(lat):
                continue

            lon = lon % 360

            vectors.append((lon, lat))

        if len(vectors) == 0:
            raise RuntimeError(f"Horizons returned no usable coordinates for {body}")

        return vectors

    except Exception as e:

        raise RuntimeError(str(e))
