# Minor Planet Center Ephemeris Client
#import requests

MPC_ENDPOINT = "https://minorplanetcenter.net/web_service/search_orbits"


def fetch_mpc(body_name: str):
    """
    Fetch orbital elements for an asteroid/TNO from the Minor Planet Center.
    Returns a dict with orbital parameters used for propagation.
    """

    params = {
        "object_id": body_name,
        "format": "json"
    }

    response = requests.get(MPC_ENDPOINT, params=params, timeout=30)

    if response.status_code != 200:
        raise RuntimeError(f"MPC request failed for {body_name}")

    data = response.json()

    if not data:
        raise RuntimeError(f"MPC returned empty result for {body_name}")

    return data TODO: Implement MPC object fetching and ecliptic computation.
