import requests
from datetime import datetime

MIRIADE_URL = "https://ssp.imcce.fr/webservices/miriade/api/ephemcc.php"


def fetch_miriade_position(body, timestamp):

    # convert ISO timestamp to required format
    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    date_str = dt.strftime("%Y-%m-%dT%H:%M:%S")

    params = {
        "name": body,
        "type": "majorbody",
        "epoch": date_str,
        "coord": "ECLIPTIC",
        "refsystem": "ICRF",
        "mime": "json"
    }

    response = requests.get(MIRIADE_URL, params=params, timeout=20)

    if response.status_code != 200:
        raise Exception("Miriade request failed")

    data = response.json()

    if "data" not in data:
        raise Exception("Invalid Miriade response")

    entry = data["data"][0]

    lon = float(entry["longitude"])
    lat = float(entry["latitude"])

    return {
        "ecl_lon_deg": lon,
        "ecl_lat_deg": lat
    }
