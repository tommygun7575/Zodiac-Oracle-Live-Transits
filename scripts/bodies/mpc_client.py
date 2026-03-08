import requests

MPC_ENDPOINT = "https://minorplanetcenter.net/web_service/search_orbits"


def fetch_mpc(body):

    params = {
        "object_id": body,
        "format": "json"
    }

    r = requests.get(MPC_ENDPOINT, params=params, timeout=30)

    if r.status_code != 200:
        raise RuntimeError(f"MPC request failed for {body} with status {r.status_code}")

    data = r.json()

    if not data:
        raise RuntimeError(f"Empty MPC response for {body}")

    lon = float(data[0]["node"])

    return {"lon": lon}
