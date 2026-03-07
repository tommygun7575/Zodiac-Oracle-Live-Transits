import json
import os
from datetime import datetime, timedelta

from scripts.bodies.horizons_engine import fetch_batch as fetch_jpl
from scripts.bodies.miriade_engine import fetch_miriade
from scripts.bodies.swiss_engine import fetch_swiss


BODIES = [
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
    "Ceres",
    "Pallas",
    "Juno",
    "Vesta",
    "Eris",
    "Sedna",
    "Orcus",
    "Makemake",
    "Haumea",
    "Quaoar",
    "Ixion"
]


def merge_vectors(primary, fallback):

    merged = []

    for i in range(len(primary)):

        p = primary[i] if primary else {}
        f = fallback[i] if fallback else {}

        lon = p.get("lon") if p.get("lon") is not None else f.get("lon")
        lat = p.get("lat") if p.get("lat") is not None else f.get("lat")

        merged.append({
            "lon": lon,
            "lat": lat
        })

    return merged


def normalize_jpl(vec):

    normalized = []

    for day in vec:

        try:
            lon, lat = day
            normalized.append({"lon": float(lon), "lat": float(lat)})
        except Exception:
            normalized.append({"lon": None, "lat": None})

    return normalized


def generate_week():

    today = datetime.utcnow()

    start = today.strftime("%Y-%m-%d")
    stop = (today + timedelta(days=6)).strftime("%Y-%m-%d")

    print("Generating current week transits...")

    body_vectors = {}

    for body in BODIES:

        jpl_data = None
        miriade_data = None
        swiss_data = None

        try:

            vec = fetch_jpl(body, start, stop)
            jpl_data = normalize_jpl(vec)

            print(f"[OK] {body} via JPL")

        except Exception as e:

            print(f"[WARN] JPL failed for {body}: {e}")

        try:

            miriade_data = fetch_miriade(body, start, stop)

            print(f"[OK] {body} via Miriade")

        except Exception as e:

            print(f"[WARN] Miriade failed for {body}: {e}")

        try:

            swiss_data = fetch_swiss(body, start, stop)

            print(f"[OK] {body} via Swiss")

        except Exception as e:

            print(f"[WARN] Swiss failed for {body}: {e}")

        data = jpl_data

        if data is None and miriade_data:

            data = miriade_data

        elif data and miriade_data:

            data = merge_vectors(data, miriade_data)

        if data and swiss_data:

            data = merge_vectors(data, swiss_data)

        if data is None:

            print(f"[FAIL] no data for {body}")
            continue

        body_vectors[body] = data

    if "Sun" not in body_vectors:

        raise RuntimeError("Sun ephemeris missing after all providers")

    if "Moon" not in body_vectors:

        raise RuntimeError("Moon ephemeris missing after all providers")

    return body_vectors


def write_json(data):

    os.makedirs("docs", exist_ok=True)

    output = {
        "generated": datetime.utcnow().isoformat(),
        "bodies": data
    }

    with open("docs/current_week.json", "w") as f:

        json.dump(output, f, indent=2)

    print("current_week.json generated")


def main():

    data = generate_week()

    write_json(data)


if __name__ == "__main__":

    main()
