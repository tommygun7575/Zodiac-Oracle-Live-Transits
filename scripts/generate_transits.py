import json
from datetime import datetime, timedelta

from scripts.bodies.horizons_client import fetch_ephemeris
from scripts.bodies.swiss_engine import get_swiss_week


TARGETS = {

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

    "Eris": "136199",
    "Haumea": "136108",
    "Makemake": "136472",
    "Sedna": "90377",
    "Quaoar": "50000",
    "Orcus": "90482",

    "Chiron": "2060",
    "Chariklo": "10199",
    "Pholus": "5145",

    "Ceres": "1;",
    "Pallas": "2;",
    "Juno": "3;",
    "Vesta": "4;",

    "Psyche": "16;",
    "Eros": "433;",
    "Amor": "1221;"
}


def generate_week():

    MAX_HARMONIC = 12

    today = datetime.utcnow().date()
    week_start = today
    week_end = today + timedelta(days=7)

    resolved = {}
    missing = []

    for name, body_id in TARGETS.items():

        step_days = 1 if name in ["Sun", "Moon"] else 2
        data = None
        source = None

        # LAYER 1 — JPL (skip Sun)
        if name != "Sun":
            try:
                jpl_data = fetch_ephemeris(
                    body_id,
                    week_start.strftime("%Y-%m-%d"),
                    week_end.strftime("%Y-%m-%d"),
                    f"{step_days}d"
                )
                if jpl_data:
                    data = jpl_data
                    source = "jpl"
            except:
                pass

        # LAYER 2 — Swiss fallback
        if data is None:
            try:
                swiss_data = get_swiss_week(
                    name,
                    week_start.strftime("%Y-%m-%d"),
                    week_end.strftime("%Y-%m-%d"),
                    step_days
                )
                if swiss_data:
                    data = swiss_data
                    source = "swiss"
            except:
                pass

        if data is not None:
            resolved[name] = {
                "source": source,
                "data": {
                    row["date"]: row["longitude_deg"]
                    for row in data
                }
            }
        else:
            missing.append(name)

    coverage = len(resolved) / len(TARGETS)

    arabic_parts = {"Part_of_Fortune": {}}

    if "Sun" in resolved and "Moon" in resolved:

        sun_data = resolved["Sun"]["data"]
        moon_data = resolved["Moon"]["data"]

        for date in sun_data:
            if date in moon_data:
                sun = sun_data[date]
                moon = moon_data[date]
                asc = (sun + 90) % 360
                arabic_parts["Part_of_Fortune"][date] = (asc + moon - sun) % 360

    harmonics = {}

    for body, payload in resolved.items():
        for date, lon in payload["data"].items():

            if date not in harmonics:
                harmonics[date] = {}

            for h in range(2, MAX_HARMONIC + 1):

                key = f"H{h}"

                if key not in harmonics[date]:
                    harmonics[date][key] = {}

                harmonics[date][key][body] = (lon * h) % 360

    output = {
        "generated_utc": datetime.utcnow().isoformat(),
        "week_start": str(week_start),
        "week_end": str(week_end),
        "engine_version": "ZodiacOracle.LiveTransit.vHybrid",
        "coverage": coverage,
        "resolved": len(resolved),
        "total_targets": len(TARGETS),
        "missing": missing,
        "bodies": resolved,
        "arabic_parts": arabic_parts,
        "harmonics": harmonics,
        "fixed_star_conjunctions": {}
    }

    with open("docs/current_week.json", "w") as f:
        json.dump(output, f, indent=2)


if __name__ == "__main__":
    generate_week()
