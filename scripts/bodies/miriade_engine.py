import requests
from scripts.utils.coord import equatorial_to_ecliptic

MIRIADE_BASE = "https://api.imcce.fr/webservices/miriade/ephemcc"

def fetch(body_name, iso_utc_timestamp):
    # First try ecliptic
    params = {
        "obj": body_name,
        "type": "helioc",
        "coord": "eclh",
        "ep": iso_utc_timestamp,
        "output": "json",
    }
    try:
        r = requests.get(MIRIADE_BASE, params=params, timeout=20)
        if r.status_code != 200:
            return None
        data = r.json()
        if "data" in data and len(data["data"]) and len(data["data"][0]) >= 5:
            lon = float(data["data"][0][2])
            lat = float(data["data"][0][3])
            return {"lon": lon, "lat": lat, "retrograde": False}
        # Fallback: Try equatorial, convert
        params_equ = dict(params)
        params_equ["type"] = "equ"
        params_equ["coord"] = "eq"
        r2 = requests.get(MIRIADE_BASE, params=params_equ, timeout=20)
        if r2.status_code == 200:
            data2 = r2.json()
            if "data" in data2 and len(data2["data"]) and len(data2["data"][0]) >= 5:
                ra = float(data2["data"][0][2])
                dec = float(data2["data"][0][3])
                lon, lat = equatorial_to_ecliptic(ra, dec)
                return {"lon": lon, "lat": lat, "retrograde": False}
        return None
    except Exception:
        return None
