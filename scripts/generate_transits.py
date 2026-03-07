import os
import sys
import json
import time
import numpy as np
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from scripts.bodies.horizons_engine import fetch_batch
from scripts.bodies.harmonics_engine import compute_harmonics
from scripts.fixed_stars import detect_star_hits


BODY_REGISTRY = {
    "Sun": "10",
    "Moon": "301",
    "Mercury": "199",
    "Venus": "299",
    "Mars": "499",
    "Jupiter": "599",
    "Saturn": "699",
    "Uranus": "799",
    "Neptune": "899",
    "Pluto": "999",
    "Ceres": "1",
    "Pallas": "2",
    "Juno": "3",
    "Vesta": "4",
    "Eris": "136199",
    "Haumea": "136108",
    "Makemake": "136472",
    "Sedna": "90377",
    "Orcus": "90482",
    "Quaoar": "50000",
    "Ixion": "28978"
}


CACHE_DIR = "cache"

SLOW_OBJECTS = {
    "Sedna",
    "Eris",
    "Haumea",
    "Makemake",
    "Orcus"
}


def load_cache(name):

    path = os.path.join(CACHE_DIR, f"{name}.json")

    if not os.path.exists(path):
        return None

    try:
        with open(path) as f:
            data = json.load(f)

        arr = np.array(data)

        if arr.shape[0] < 7:
            return None

        return arr

    except Exception:
        return None


def save_cache(name, data):

    os.makedirs(CACHE_DIR, exist_ok=True)

    path = os.path.join(CACHE_DIR, f"{name}.json")

    with open(path, "w") as f:
        json.dump(data.tolist(), f)


def fetch_body_safe(name, body_id, start, end):

    try:

        if name in SLOW_OBJECTS:

            cached = load_cache(name)

            if cached is not None:
                return name, cached

        vec = fetch_batch(body_id, start, end)

        if vec is None or len(vec) < 7:
            raise RuntimeError("Vector incomplete")

        if name in SLOW_OBJECTS:
            save_cache(name, vec)

        return name, vec

    except Exception as e:

        print(f"[WARN] skipping {name}: {e}")

        return name, None


def generate_week():

    now = datetime.utcnow()

    start = now.strftime("%Y-%m-%d")

    end = (now + timedelta(days=6)).strftime("%Y-%m-%d")

    body_vectors = {}

    futures = []

    with ThreadPoolExecutor(max_workers=6) as executor:

        for name, body_id in BODY_REGISTRY.items():

            futures.append(
                executor.submit(fetch_body_safe, name, body_id, start, end)
            )

        for future in as_completed(futures):

            name, vec = future.result()

            if vec is not None:
                body_vectors[name] = vec

    if "Sun" not in body_vectors or "Moon" not in body_vectors:
        raise RuntimeError("Critical bodies missing from ephemeris")

    days = []

    for i in range(7):

        objects = {}

        longitudes = []

        for body, vec in body_vectors.items():

            if i >= len(vec):
                continue

            lon, lat = vec[i]

            objects[body] = {
                "ecl_lon_deg": float(lon),
                "ecl_lat_deg": float(lat),
                "used_source": "jpl_horizons"
            }

            longitudes.append(float(lon))

        harmonics = compute_harmonics(longitudes)

        stars = detect_star_hits(longitudes)

        sun = objects["Sun"]["ecl_lon_deg"]

        moon = objects["Moon"]["ecl_lon_deg"]

        part_of_fortune = (moon - sun) % 360

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

    output_path = os.path.join("docs", "weekly_overlay.json")

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print("Weekly overlay written:", output_path)


if __name__ == "__main__":
    main()
