from datetime import datetime, timedelta
import numpy as np
from astroquery.jplhorizons import Horizons
import math
import time

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

OBLIQUITY = math.radians(23.439291)


def radec_to_ecliptic(ra_deg, dec_deg):
    ra = math.radians(ra_deg)
    dec = math.radians(dec_deg)

    lon = math.atan2(
        math.sin(ra) * math.cos(OBLIQUITY) + math.tan(dec) * math.sin(OBLIQUITY),
        math.cos(ra)
    )

    lat = math.asin(
        math.sin(dec) * math.cos(OBLIQUITY) -
        math.cos(dec) * math.sin(OBLIQUITY) * math.sin(ra)
    )

    return math.degrees(lon) % 360, math.degrees(lat)


def fetch_single(body, jd):

    for attempt in range(5):

        try:

            obj = Horizons(
                id=BODY_IDS[body],
                location="500@399",
                epochs=jd
            )

            eph = obj.ephemerides()

            if len(eph) == 0:
                raise RuntimeError("empty ephemeris")

            if "EclLon" in eph.colnames and "EclLat" in eph.colnames:
                return float(eph["EclLon"][0]) % 360, float(eph["EclLat"][0])

            if "RA" in eph.colnames and "DEC" in eph.colnames:
                return radec_to_ecliptic(
                    float(eph["RA"][0]),
                    float(eph["DEC"][0])
                )

            raise RuntimeError("no coordinate columns")

        except Exception:
            time.sleep(2)

    return None


def fetch_batch(body, start, end):

    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)

    days = (end_dt - start_dt).days + 1
    results = []

    for i in range(days):

        t = start_dt + timedelta(days=i)
        jd = t.timestamp() / 86400.0 + 2440587.5

        coords = fetch_single(body, jd)

        if coords is None:
            raise RuntimeError(f"Horizons returned no coordinates for {body}")

        results.append(coords)

    return np.array(results)
