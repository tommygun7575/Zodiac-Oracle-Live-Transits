from datetime import datetime, timedelta, timezone

from scripts.bodies.miriade_engine import fetch_miriade as fetch_miriade_batch


def fetch_miriade(body, start=None, stop=None):
    if start is None:
        start_date = datetime.now(timezone.utc).date()
        start = start_date.strftime("%Y-%m-%d")
    else:
        start_date = datetime.strptime(start, "%Y-%m-%d").date()

    if stop is None:
        stop = (start_date + timedelta(days=6)).strftime("%Y-%m-%d")

    rows = fetch_miriade_batch(body, start, stop)
    if not rows:
        raise RuntimeError(f"Miriade returned no data for {body}")

    first = rows[0]
    if first["lon"] is None:
        raise RuntimeError(f"Miriade returned incomplete data for {body}")

    return first
