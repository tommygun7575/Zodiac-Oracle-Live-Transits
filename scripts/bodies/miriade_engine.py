import requests
from datetime import datetime

MIRIADE_URL = "https://ssp.imcce.fr/webservices/miriade/api/ephemcc.php"


def fetch_miriade(body, start, stop, nbd=7, step="1d"):
    """Fetch Miriade ecliptic longitudes.

    ``nbd`` / ``step`` control sample count (e.g. nbd=28, step='6h' for
    4 UTC slots × 7 days). Pads/truncates to ``nbd`` rows.
    """
    if isinstance(start, datetime):
        epoch = start.strftime("%Y-%m-%dT%H:%M:%S")
    else:
        text = str(start)
        epoch = text if "T" in text else f"{text[:10]}T00:00:00"

    params = {
        "name": body,
        "type": "object",
        "epoch": epoch,
        "nbd": int(nbd),
        "step": step,
        "observer": "500",
        "tcoor": "2",
        "mime": "json",
    }

    r = requests.get(MIRIADE_URL, params=params, timeout=60)

    if r.status_code != 200:
        raise RuntimeError(f"Miriade request failed for {body}")

    data = r.json()
    entries = data.get("data", [])
    results = []

    for entry in entries[: int(nbd)]:
        lon = None
        lat = None
        try:
            lon = float(entry["EclLon"])
            lat = float(entry["EclLat"])
        except Exception:
            pass
        results.append({"lon": lon, "lat": lat})

    while len(results) < int(nbd):
        results.append({"lon": None, "lat": None})

    return results[: int(nbd)]
