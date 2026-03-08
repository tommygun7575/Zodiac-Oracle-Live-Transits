from datetime import datetime, timedelta

from scripts.bodies.horizons_engine import fetch_batch


def fetch_horizons(body, start=None, stop=None):
    if start is None:
        start_date = datetime.utcnow().date()
        start = start_date.strftime("%Y-%m-%d")
    else:
        start_date = datetime.strptime(start, "%Y-%m-%d").date()

    if stop is None:
        stop = (start_date + timedelta(days=6)).strftime("%Y-%m-%d")

    rows = fetch_batch(body, start, stop)
    lon, lat = rows[0]

    if lon is None:
        raise RuntimeError(f"Horizons returned empty result for {body}")

    return {"lon": lon, "lat": lat}

