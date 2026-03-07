import datetime

# -------------------------------------------------------
# Make astroquery optional so GitHub workflow never fails
# -------------------------------------------------------
try:
    from astroquery.jplhorizons import Horizons
    ASTROQUERY_AVAILABLE = True
except Exception:
    ASTROQUERY_AVAILABLE = False


def fetch_horizons_position(body_name: str, timestamp: str):
    """
    Fetch ecliptic coordinates from JPL Horizons.

    If astroquery is not installed (GitHub runner case),
    the function safely returns None so the pipeline
    falls back to Swiss Ephemeris.
    """

    if not ASTROQUERY_AVAILABLE:
        return None

    try:

        dt = datetime.datetime.fromisoformat(timestamp.replace("Z", ""))

        obj = Horizons(
            id=body_name,
            location="500@10",
            epochs=dt.timestamp()
        )

        eph = obj.ephemerides()

        lon = float(eph["EclLon"][0])
        lat = float(eph["EclLat"][0])

        return {
            "ecl_lon_deg": lon,
            "ecl_lat_deg": lat
        }

    except Exception:
        return None
