from datetime import datetime, timedelta
import numpy as np
from astroquery.jplhorizons import Horizons

BODY_IDS = {
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


def _fetch_one(body, when):

    body_id = BODY_IDS[body]

    obj = Horizons(
        id=body_id,
        location="500@399",
        epochs=when
    )

    eph = obj.ephemerides(quantities="1,3")

    if len(eph) == 0:
        return None

    lon = float(eph["EclLon"][0])
    lat = float(eph["EclLat"][0])

    return lon % 360, lat


def fetch_batch(body, start, end):

    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)

    days = (end_dt - start_dt).days + 1

    results = []

    for i in range(days):

        t = start_dt + timedelta(days=i)

        jd = t.timestamp() / 86400.0 + 2440587.5

        lonlat = _fetch_one(body, jd)

        if lonlat is None:
            raise RuntimeError(f"Horizons returned no coordinates for {body}")

        results.append(lonlat)

    return np.array(results)
