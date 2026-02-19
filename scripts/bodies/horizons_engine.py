import warnings
from astroquery.jplhorizons import Horizons
from scripts.utils.coord import equatorial_to_ecliptic

# Extend as needed for asteroids/TNOs (or pass name as-is)
PLANET_IDS = {
    "Sun": 10, "Mercury": 199, "Venus": 299, "Earth": 399, "Moon": 301,
    "Mars": 499, "Jupiter": 599, "Saturn": 699, "Uranus": 799,
    "Neptune": 899, "Pluto": 999, "Ceres": 1, "Pallas": 2, "Juno": 3, "Vesta": 4,
    "Chiron": "2060", "Eris": "136199", "Sedna": "90377", "Haumea": "136108", "Makemake": "136472",
    # Add more as used in your body list
}

def fetch(body_name, iso_utc_timestamp):
    obj_id = PLANET_IDS.get(body_name, body_name)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            obj = Horizons(id=obj_id, location="500@0", epochs=iso_utc_timestamp, id_type='majorbody')
            eph = obj.ephemerides()
        if eph.empty or len(eph) == 0:
            return None

        lon = float(eph["EclLon"][0])
        lat = float(eph["EclLat"][0])
        # Try retrograde from rate in longitude
        try:
            retrograde = float(eph["RA_rate"][0]) < 0
        except Exception:
            retrograde = False
        return {"lon": lon, "lat": lat, "retrograde": retrograde}
    except Exception:
        # Fallback: try vectors/RADEC and convert
        try:
            obj = Horizons(id=obj_id, location="500@0", epochs=iso_utc_timestamp, id_type='majorbody')
            vec = obj.vectors()
            ra = float(vec["RA"][0])
            dec = float(vec["DEC"][0])
            lon, lat = equatorial_to_ecliptic(ra, dec)
            return {"lon": lon, "lat": lat, "retrograde": False}
        except Exception:
            return None# Horizons Ephemeris Client

# TODO: Client implementation for Horizons ephemeris.
