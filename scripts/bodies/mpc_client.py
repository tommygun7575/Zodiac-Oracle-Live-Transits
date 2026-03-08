import requests

MPC_ENDPOINT = "https://minorplanetcenter.net/web_service/search_orbits"


def fetch_mpc(body):

    params = {
        "object_id": body,
        "format": "json"
    }

    r = requests.get(MPC_ENDPOINT, params=params, timeout=30)

    if r.status_code != 200:
        raise RuntimeError("MPC request failed")

    data = r.json()

    if not data:
        raise RuntimeError("Empty MPC response")

    lon = float(data[0]["node"])

    return {"lon": lon}
