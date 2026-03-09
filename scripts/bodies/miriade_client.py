import requests


MIRADE_URL = "https://ssp.imcce.fr/webservices/miriade/api/ephemcc.php"


def fetch_miriade(body_name, start_date, stop_date, step="2d"):

    params = {
        "name": body_name,
        "type": "object",
        "ephem": "1",
        "observer": "500",
        "epoch": start_date,
        "step": step,
        "nbd": "20",
        "mime": "json"
    }

    r = requests.get(MIRADE_URL, params=params, timeout=60)

    if r.status_code != 200:
        raise RuntimeError("Miriade HTTP error")

    data = r.json()

    if "data" not in data:
        raise RuntimeError("Miriade no data")

    ephemeris = {}

    for row in data["data"]:
        try:
            iso_date = row["date"]
            lon = float(row["lambda"])
            ephemeris[iso_date] = lon
        except:
            continue

    if not ephemeris:
        raise RuntimeError("Miriade parsed zero rows")

    return ephemeris
