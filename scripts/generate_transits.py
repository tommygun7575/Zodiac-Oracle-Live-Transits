import json
import os
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np

from scripts.bodies.horizons_engine import fetch_batch as fetch_jpl
from scripts.bodies.miriade_engine import fetch_miriade
from scripts.bodies.swiss_engine import fetch_swiss

from scripts.bodies.harmonics_engine import compute_harmonics
from scripts.fixed_stars import detect_star_hits


BODY_REGISTRY = [
    "Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn",
    "Uranus","Neptune","Pluto",
    "Ceres","Pallas","Juno","Vesta",
    "Eris","Haumea","Makemake","Sedna",
    "Orcus","Quaoar","Ixion"
]


def is_valid_vector(vec):
    if vec is None:
        return False
    if len(vec) < 7:
        return False

    for day in vec:
        if day is None:
            return False
        lon, lat = day
        if lon is None or lat is None:
            return False
        if np.isnan(lon) or np.isnan(lat):
            return False

    return True


def safe_float(v):
    if isinstance(v, (np.floating, np.integer)):
        return float(v)
    return v


def numpy_to_native(obj):

    if isinstance(obj, np.ndarray):
        return obj.tolist()

    if isinstance(obj, (np.floating, np.integer)):
        return float(obj)

    if isinstance(obj, dict):
        return {k: numpy_to_native(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [numpy_to_native(v) for v in obj]

    return obj


def fetch_body_vector(body, start, stop):

    # --- JPL Horizons (Primary) ---

    try:
        vec = fetch_jpl(body, start, stop)
        if is_valid_vector(vec):
            print(f"[OK] {body} via JPL")
            return body, vec, "jpl_horizons"
    except Exception as e:
        print(f"[WARN] JPL failed for {body}: {e}")

    time.sleep(0.3)

    # --- Miriade (Secondary) ---

    try:
        vec = fetch_miriade(body, start, stop)
        if is_valid_vector(vec):
            print(f"[OK] {body} via Miriade")
            return body, vec, "imcce_miriade"
    except Exception as e:
        print(f"[WARN] Miriade failed for {body}: {e}")

    time.sleep(0.3)

    # --- Swiss Ephemeris (Final fallback) ---

    try:
        vec = fetch_swiss(body, start, stop)
        if is_valid_vector(vec):
            print(f"[OK] {body} via Swiss")
            return body, vec, "swiss_ephemeris"
    except Exception as e:
        print(f"[WARN] Swiss failed for {body}: {e}")

    print(f"[FAIL] no data for {body}")
    return body, None, None


def generate_week():

    now = datetime.utcnow()

    start = now.strftime("%Y-%m-%d")
    stop = (now + timedelta(days=6)).strftime("%Y-%m-%d")

    body_vectors = {}
    body_sources = {}

    with ThreadPoolExecutor(max_workers=4) as executor:

        futures = [
            executor.submit(fetch_body_vector, body, start, stop)
            for body in BODY_REGISTRY
        ]

        for f in as_completed(futures):

            body, vec, source = f.result()

            if vec is not None:
                body_vectors[body] = vec
                body_sources[body] = source

    if "Sun" not in body_vectors or "Moon" not in body_vectors:
        raise RuntimeError("Critical ephemeris missing (Sun or Moon)")

    days = []

    for i in range(7):

        objects = {}
        longitudes = []

        for body, vec in body_vectors.items():

            lon, lat = vec[i]

            lon = safe_float(lon)
            lat = safe_float(lat)

            objects[body] = {
                "ecl_lon_deg": lon,
                "ecl_lat_deg": lat,
                "used_source": body_sources[body]
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

            "harmonics": numpy_to_native({
                "h5": harmonics["h5"],
                "h7": harmonics["h7"],
                "h9": harmonics["h9"]
            }),

            "fixed_star_hits": numpy_to_native(stars)

        })

    return {
        "version": "oracle-current-week",
        "generated_at": datetime.utcnow().isoformat(),
        "week_start": now.isoformat(),
        "days": days
    }


def main():

    print("Generating current week transits...")

    data = generate_week()

    os.makedirs("docs", exist_ok=True)

    output_path = os.path.join("docs", "current_week.json")

    with open(output_path, "w") as f:
        json.dump(numpy_to_native(data), f, indent=2)

    print("Overlay written to:", output_path)


if __name__ == "__main__":
    main()
