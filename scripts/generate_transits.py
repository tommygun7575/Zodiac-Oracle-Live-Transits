import json
import os
from datetime import datetime, timedelta

from scripts.bodies.horizons_engine import fetch_batch as fetch_jpl
from scripts.bodies.miriade_engine import fetch_miriade
from scripts.bodies.swiss_engine import fetch_swiss


BODIES = [
    "Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn",
    "Uranus","Neptune","Pluto",
    "Ceres","Pallas","Juno","Vesta",
    "Eris","Sedna","Orcus","Makemake",
    "Haumea","Quaoar","Ixion"
]


def normalize(vec):

    result = []

    for item in vec:

        try:
            lon, lat = item
            result.append({"lon": lon, "lat": lat})
        except Exception:
            result.append({"lon": None, "lat": None})

    return result


def merge(primary, fallback):

    merged = []

    for i in range(len(primary)):

        p = primary[i] if primary else {}
        f = fallback[i] if fallback else {}

        lon = p.get("lon") if p.get("lon") is not None else f.get("lon")
        lat = p.get("lat") if p.get("lat") is not None else f.get("lat")

        merged.append({"lon": lon, "lat": lat})

    return merged


def generate_week():

    now = datetime.utcnow()

    start = now.strftime("%Y-%m-%d")
    stop = (now + timedelta(days=6)).strftime("%Y-%m-%d")

    body_vectors = {}

    print("Generating weekly overlay")

    for body in BODIES:

        jpl = None
        miriade = None
        swiss = None

        try:
            jpl = normalize(fetch_jpl(body, start, stop))
            print(f"[OK] {body} via JPL")
        except Exception as e:
            print(f"[WARN] JPL failed for {body}: {e}")

        try:
            miriade = fetch_miriade(body, start, stop)
            print(f"[OK] {body} via Miriade")
        except Exception as e:
            print(f"[WARN] Miriade failed for {body}: {e}")

        try:
            swiss = fetch_swiss(body, start, stop)
            print(f"[OK] {body} via Swiss")
        except Exception as e:
            print(f"[WARN] Swiss failed for {body}: {e}")

        data = jpl

        if data is None and miriade:
            data = miriade
        elif data and miriade:
            data = merge(data, miriade)

        if data and swiss:
            data = merge(data, swiss)

        if data is None:
            print(f"[FAIL] no data for {body}")
            continue

        body_vectors[body] = data

    if "Sun" not in body_vectors:
        raise RuntimeError("Sun missing after all providers")

    if "Moon" not in body_vectors:
        raise RuntimeError("Moon missing after all providers")

    return body_vectors


def write_output(data):

    os.makedirs("docs", exist_ok=True)

    payload = {
        "generated": datetime.utcnow().isoformat(),
        "bodies": data
    }

    with open("docs/current_week.json","w") as f:
        json.dump(payload,f,indent=2)

    print("current_week.json written")


def main():

    data = generate_week()

    write_output(data)


if __name__ == "__main__":
    main()
