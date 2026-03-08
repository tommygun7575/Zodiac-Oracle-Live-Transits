import requests
from datetime import datetime

MIRIADE_URL = "https://ssp.imcce.fr/webservices/miriade/api/ephemcc.php"


def fetch_miriade(body, start, stop):

    start_dt = datetime.strptime(start, "%Y-%m-%d")

    params = {
        "name": body,
        "type": "object",
        "epoch": start_dt.strftime("%Y-%m-%dT00:00:00"),
        "nbd": 7,
        "step": "1d",
        "observer": "500",
        "tcoor": "2",
        "mime": "json"
    }

    r = requests.get(MIRIADE_URL, params=params, timeout=30)

    if r.status_code != 200:
        raise RuntimeError(f"Miriade request failed for {body}")

    data = r.json()

    entries = data.get("data", [])

    results = []

    for entry in entries[:7]:

        lon = None
        lat = None

        try:
            lon = float(entry["EclLon"])
            lat = float(entry["EclLat"])
        except Exception:
            pass

        results.append({
            "lon": lon,
            "lat": lat
        })

    # Pad if fewer results than expected to ensure exactly 7 days for downstream consumers
    while len(results) < 7:
        results.append({"lon": None, "lat": None})

    return results
