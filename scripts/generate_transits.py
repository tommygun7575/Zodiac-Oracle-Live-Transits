import json
import os
from datetime import datetime, timedelta
import swisseph as swe

from scripts.horizons_client import fetch_ephemeris


BODY_MAP = {
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
    "Quaoar": "136108",
    "Orcus": "90482",
    "Chiron": "2060",
    "Chariklo": "10199",
    "Pholus": "5145",
    "Ceres": "1",
    "Pallas": "2",
    "Juno": "3",
    "Vesta": "4",
    "Psyche": "16",
    "Eros": "433",
    "Amor": "1221"
}


def load_fixed_stars():
    with open(os.path.join("data", "fixed_stars.json"), "r") as f:
        return json.load(f)


def detect_star_conjunctions(bodies, orb=1.0):
    stars = load_fixed_stars()
    results = {}

    for body, info in bodies.items():
        for date, lon in info["data"].items():

            for star_name, star_lon in stars.items():

                diff = abs(lon - star_lon)
                if diff > 180:
                    diff = 360 - diff

                if diff <= orb:
                    if date not in results:
                        results[date] = []
                    results[date].append({
                        "body": body,
                        "star": star_name,
                        "orb": round(diff, 4)
                    })

    return results


def generate_week_dates():
    today = datetime.utcnow().date()
    week_start = today
    week_end = today + timedelta(days=7)
    return week_start, week_end


def generate_swiss_sun(start, end):
    swe.set_ephe_path(".")
    results = {}
    current = start

    while current <= end:
        jd = swe.julday(current.year, current.month, current.day)
        lon = swe.calc_ut(jd, swe.SUN)[0][0]
        results[current.strftime("%Y-%m-%d")] = lon
        current += timedelta(days=1)

    return results


def main():

    week_start, week_end = generate_week_dates()

    output = {
        "generated_utc": datetime.utcnow().isoformat(),
        "week_start": str(week_start),
        "week_end": str(week_end),
        "engine_version": "ZodiacOracle.LiveTransit.vHybrid",
        "coverage": 0.0,
        "resolved": 0,
        "total_targets": len(BODY_MAP),
        "missing": [],
        "bodies": {},
        "arabic_parts": {},
        "harmonics": {},
        "fixed_star_conjunctions": {}
    }

    resolved = 0

    for body, body_id in BODY_MAP.items():

        try:

            if body == "Sun":
                data = generate_swiss_sun(week_start, week_end)
                source = "swiss"

            else:
                step = "1d" if body == "Moon" else "2d"
                data = fetch_ephemeris(
                    body_id,
                    str(week_start),
                    str(week_end),
                    step
                )
                source = "jpl"

            output["bodies"][body] = {
                "source": source,
                "data": data
            }

            resolved += 1

        except Exception as e:
            print(f"FAILED {body}: {e}")
            output["missing"].append(body)

    output["resolved"] = resolved
    output["coverage"] = round(resolved / output["total_targets"], 4)

    output["fixed_star_conjunctions"] = detect_star_conjunctions(output["bodies"])

    os.makedirs("output", exist_ok=True)

    with open("output/current_week.json", "w") as f:
        json.dump(output, f, indent=2)


if __name__ == "__main__":
    main()
