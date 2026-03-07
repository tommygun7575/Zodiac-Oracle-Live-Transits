from astroquery.jplhorizons import Horizons
import math

def get_body(body, jd):
    try:
        obj = Horizons(id=body, location="500@10", epochs=jd)
        vec = obj.vectors()

        x = float(vec["x"][0])
        y = float(vec["y"][0])
        z = float(vec["z"][0])

        lon = math.degrees(math.atan2(y, x)) % 360
        lat = math.degrees(math.atan2(z, (x*x+y*y)**0.5))

        return lon, lat, "horizons"
    except Exception:
        return None

def get_numbered_object(number, jd):
    try:
        obj = Horizons(id=f"{number};", location="500@10", epochs=jd)
        vec = obj.vectors()

        x = float(vec["x"][0])
        y = float(vec["y"][0])
        z = float(vec["z"][0])

        lon = math.degrees(math.atan2(y, x)) % 360
        lat = math.degrees(math.atan2(z, (x*x+y*y)**0.5))

        return lon, lat, "horizons"
    except Exception:
        return None
