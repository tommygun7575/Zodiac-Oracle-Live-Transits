import os
import sys
import json
import numpy as np
from datetime import datetime, timedelta

# ensure repo root is importable
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


def generate_week():

    now = datetime.utcnow()
    start = now.strftime("%Y-%m-%d")
    end = (now + timedelta(days=6)).strftime("%Y-%m-%d")

    body_vectors = {}

    # batch ephemeris queries
    for name, body_id in BODY_REGISTRY.items():

        vec = fetch_batch(body_id, start, end)

        body_vectors[name] = vec

    days = []

    for i in range(7):

        objects = {}
        longitudes = []

        for body, vec in body_vectors.items():

            lon, lat = vec[i]

            objects[body] = {
                "ecl_lon_deg": float(lon),
                "ecl_lat_deg": float(lat),
                "used_source": "jpl_horizons"
            }

            longitudes.append(lon)

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

    data = generate_week()

    os.makedirs("docs", exist_ok=True)

    with open("docs/weekly_overlay.json", "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    main()
