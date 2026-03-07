from astroquery.jplhorizons import Horizons
from datetime import datetime
import time

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
    "Pluto": "999"
}

def iso_to_epoch(timestamp):

    dt = datetime.fromisoformat(timestamp.replace("Z","+00:00"))

    return dt.strftime("%Y-%m-%d %H:%M")


def fetch_horizons_position(body, timestamp):

    if body not in HORIZONS_IDS:
        raise Exception(f"Horizons unsupported body {body}")

    target = HORIZONS_IDS[body]

    epoch = iso_to_epoch(timestamp)

    for attempt in range(3):

        try:

            obj = Horizons(
                id=target,
                location="500@0",
                epochs={"start":epoch,"stop":epoch,"step":"1m"}
            )

            eph = obj.ephemerides()

            lon = float(eph["EclLon"][0])
            lat = float(eph["EclLat"][0])

            time.sleep(0.15)

            return {
                "ecl_lon_deg": lon,
                "ecl_lat_deg": lat
            }

        except Exception:

            time.sleep(1)

    raise Exception("Horizons failed after retries")
