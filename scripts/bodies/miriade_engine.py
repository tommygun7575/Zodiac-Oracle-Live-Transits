import requests

MIRIADE_URL = "https://ssp.imcce.fr/webservices/miriade/api/ephemcc.php"

def fetch_miriade(body, jd):

    params = {
        "name": body,
        "type": "object",
        "epoch": jd,
        "center": "500@399",
        "output": "json"
    }

    try:

        r = requests.get(MIRIADE_URL, params=params, timeout=20)

        data = r.json()

        lon = float(data["data"][0]["EclLon"])
        lat = float(data["data"][0]["EclLat"])

        return lon, lat, "miriade"

    except:
        return None
