import requests
import math


def fetch(body, jd):

    try:

        url = "https://ssp.imcce.fr/webservices/miriade/api/ephemcc.php"

        params = {
            "name": body,
            "type": "planet",
            "ep": jd
        }

        r = requests.get(url, params=params, timeout=10)

        data = r.json()

        lon = float(data["longitude"])
        lat = float(data["latitude"])

        return lon, lat, "miriade"

    except Exception:

        return None
