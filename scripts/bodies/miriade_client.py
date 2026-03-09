import requests


MIRIADE_URL = "https://ssp.imcce.fr/webservices/miriade/api/ephemcc.php"


def fetch_miriade(body_name):
    """Fetch the current-epoch Miriade ephemeris entry for a body.

    Returns {"lon": float} where the value is taken from the 'RA' field
    (right ascension in degrees, used here as a proxy longitude for single-day
    transit lookups — callers that need true ecliptic longitude should use the
    miriade_engine week fetcher which returns EclLon).
    Raises RuntimeError("Miriade request failed") for non-200 responses.
    """
    params = {
        "name": body_name,
        "type": "object",
        "ephem": "1",
        "observer": "500",
        "mime": "json",
    }

    r = requests.get(MIRIADE_URL, params=params, timeout=60)

    if r.status_code != 200:
        raise RuntimeError("Miriade request failed")

    data = r.json()

    return {"lon": float(data["data"][0]["RA"])}
