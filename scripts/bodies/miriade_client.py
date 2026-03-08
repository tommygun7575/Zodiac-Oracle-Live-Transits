from datetime import datetime, timedelta

from scripts.bodies.miriade_engine import fetch_miriade as fetch_miriade_batch


def fetch_miriade(body, start=None, stop=None):
    if start is None:
        start_date = datetime.utcnow().date()
        start = start_date.strftime("%Y-%m-%d")
    else:
        start_date = datetime.strptime(start, "%Y-%m-%d").date()

    if stop is None:
        stop = (start_date + timedelta(days=6)).strftime("%Y-%m-%d")

    rows = fetch_miriade_batch(body, start, stop)
    first = rows[0] if rows else {"lon": None, "lat": None}

    if first["lon"] is None:
        raise RuntimeError(f"Miriade returned empty result for {body}")

    return first

