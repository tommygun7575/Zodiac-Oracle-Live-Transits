import requests
from datetime import datetime, timedelta

MIRIADE_URL = "https://ssp.imcce.fr/webservices/miriade/api/ephemcc.php"


def fetch_miriade(body, start, stop):

    start_dt = datetime.strptime(start, "%Y-%m-%d")

    results = []

    for i in range(7):

        day = start_dt + timedelta(days=i)

        params = {
            "name": body,
            "type": "object",
            "epoch": day.strftime("%Y-%m-%d"),
            "observer": "500",
            "mime": "json"
        }

        r = requests.get(MIRIADE_URL, params=params, timeout=30)

        if r.status_code != 200:
            raise RuntimeError(f"Miriade request failed for {body}")

        data = r.json()

        lon = None
        lat = None

        try:
            lon = float(data["data"][0]["EclLon"])
            lat = float(data["data"][0]["EclLat"])
        except Exception:
            pass

        results.append({
            "lon": lon,
            "lat": lat
        })

    return results
