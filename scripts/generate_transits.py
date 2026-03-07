import os
import sys
import json
import numpy as np
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# ------------------------------------------------
# FIX PYTHON IMPORT PATH FOR GITHUB ACTIONS
# ------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# now internal modules resolve correctly
from scripts.bodies.horizons_engine import fetch_batch
from scripts.bodies.harmonics_engine import compute_harmonics
from scripts.fixed_stars import detect_star_hits


BODY_REGISTRY = [
    "Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn",
    "Uranus","Neptune","Pluto",
    "Ceres","Pallas","Juno","Vesta",
    "Eris","Haumea","Makemake","Sedna",
    "Orcus","Quaoar","Ixion"
]


def fetch_body(body, start, stop):

    try:

        vec = fetch_batch(body, start, stop)

        if vec is None or len(vec) < 7:
            raise RuntimeError("vector incomplete")

        return body, vec

    except Exception as e:

        print(f"[WARN] skipping {body}: {e}")

        return body, None


def generate_week():

    now = datetime.utcnow()

    start = now.strftime("%Y-%m-%d")
    stop = (now + timedelta(days=6)).strftime("%Y-%m-%d")

    body_vectors = {}

    with ThreadPoolExecutor(max_workers=4) as executor:

        futures = [
            executor.submit(fetch_body, body, start, stop)
            for body in BODY_REGISTRY
        ]

        for f in as_completed(futures):

            body, vec = f.result()

            if vec is not None:
                body_vectors[body] = vec


    if "Sun" not in body_vectors or "Moon" not in body_vectors:
        raise RuntimeError("Critical bodies missing from ephemeris")


    days = []

    for i in range(7):

        objects = {}
        longitudes = []

        for body, vec in body_vectors.items():

            lon, lat = vec[i]

            lon = float(lon)
            lat = float(lat)

            objects[body] = {
                "ecl_lon_deg": lon,
                "ecl_lat_deg": lat,
                "used_source": "jpl_horizons"
            }

            longitudes.append(lon)


        longitudes_np = np.array(longitudes)

        harmonics = compute_harmonics(longitudes_np)
        stars = detect_star_hits(longitudes_np)

        sun = objects["Sun"]["ecl_lon_deg"]
        moon = objects["Moon"]["ecl_lon_deg"]

        part_of_fortune = float((moon - sun) % 360)

        days.append({

            "timestamp": (now + timedelta(days=i)).isoformat(),

            "objects": objects,

            "arabic_parts": {
                "Part_of_Fortune": part_of_fortune
            },

            "harmonics": {
                "h5": harmonics["h5"].tolist(),
                "h7": harmonics["h7"].tolist(),
                "h9": harmonics["h9"].tolist()
            },

            "fixed_star_hits": stars

        })


    return {
        "version": "oracle-weekly-transits",
        "generated_at": datetime.utcnow().isoformat(),
        "week_start": now.isoformat(),
        "days": days
    }


def main():

    print("Generating weekly transits...")

    data = generate_week()

    os.makedirs("docs", exist_ok=True)

    output = os.path.join("docs", "weekly_overlay.json")

    with open(output, "w") as f:
        json.dump(data, f, indent=2)

    print("Weekly overlay written:", output)


if __name__ == "__main__":
    main()
