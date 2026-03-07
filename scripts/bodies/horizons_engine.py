from datetime import datetime, timedelta
from typing import Optional, Tuple

import numpy as np
from astroquery.jplhorizons import Horizons
import swisseph as swe


MAJOR_BODIES = {
    "Sun": "10",
    "Moon": "301",
    "Mercury": "199",
    "Venus": "299",
    "Mars": "499",
    "Jupiter": "599",
    "Saturn": "699",
    "Uranus": "799",
    "Neptune": "899",
    "Pluto": "999"
}


SMALL_BODIES = {
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


BODY_IDS = {**MAJOR_BODIES, **SMALL_BODIES}


def _fetch_one(body: str, when: datetime) -> Optional[Tuple[float, float]]:

    try:

        body_id = BODY_IDS[body]

        jd = swe.julday(
            when.year,
            when.month,
            when.day,
            when.hour + when.minute/60 + when.second/3600
        )

        if body in MAJOR_BODIES:

            obj = Horizons(
                id=body_id,
                location="500@399",
                epochs=[jd],
                id_type="majorbody"
            )

        else:

            obj = Horizons(
                id=body_id,
                location="500@399",
                epochs=[jd],
                id_type="smallbody"
            )

        eph = obj.ephemerides()

        lon = None
        lat = None

        for key in ("EclLon", "EclipticLon", "ELON"):
            if key in eph.colnames:
                lon = float(eph[key][0])
                break

        for key in ("EclLat", "EclipticLat", "ELAT"):
            if key in eph.colnames:
                lat = float(eph[key][0])
                break

        if lon is None or lat is None:
            return None

        return lon % 360, lat

    except Exception:
        return None


def fetch_batch(body: str, start: str, end: str):

    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)

    days = (end_dt - start_dt).days + 1

    results = []

    for i in range(days):

        t = start_dt + timedelta(days=i)

        lonlat = _fetch_one(body, t)

        if lonlat is None:
            raise RuntimeError(f"Horizons returned no coordinates for {body}")

        results.append(lonlat)

    return np.array(results)
