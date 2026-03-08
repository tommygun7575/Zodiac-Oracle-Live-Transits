import requests

MIRIADE_URL = "https://ssp.imcce.fr/webservices/miriade/api/ephemcc.php"


def fetch_miriade(body):

    params = {
        "name": body,
        "type": "asteroid",
        "output": "json"
    }

    r = requests.get(MIRIADE_URL, params=params, timeout=30)

    if r.status_code != 200:
        raise RuntimeError(f"Miriade request failed for {body} with status {r.status_code}")

    data = r.json()

    lon = float(data["data"][0]["RA"])

    return {"lon": lon}
