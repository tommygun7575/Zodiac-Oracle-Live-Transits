import json
import os
from datetime import datetime, timedelta
import swisseph as swe

from .bodies.horizons_client import fetch_jpl
from .bodies.miriade_client import fetch_miriade


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
                    results.setdefault(date, []).append({
                        "body": body,
                        "star": star_name,
                        "orb": round(diff, 4)
                    })

    return results


def generate_week_dates():
    today = datetime.utcnow().date()
    return today, today + timedelta(days=7)


def swiss_body(body_const, start, end):
    results = {}
    current = start

    while current <= end:
        jd = swe.julday(current.year, current.month, current.day)
        lon = swe.calc_ut(jd, body_const)[0][0]
        results[current.strftime("%Y-%m-%d")] = lon
        current += timedelta(days=1)

    return results


def resolve_body(body, body_id, week_start, week_end):

    if body == "Sun":
        print("Sun → Swiss primary")
        return swiss_body(swe.SUN, week_start, week_end), "swiss"

    if body == "Moon":
        try:
            print("Moon → JPL primary")
            data = fetch_jpl(body_id, str(week_start), str(week_end), "1d")
            return data, "jpl"
        except Exception as e:
            print(f"Moon JPL FAILED: {e}")
            print("Moon → Swiss fallback")
            return swiss_body(swe.MOON, week_start, week_end), "swiss"

    # Standard hybrid routing
    try:
        print(f"{body} → JPL attempt")
        data = fetch_jpl(body_id, str(week_start), str(week_end), "2d")
        return data, "jpl"
    except Exception as e:
        print(f"{body} JPL FAILED: {e}")

    try:
        print(f"{body} → Miriade attempt")
        data = fetch_miriade(body, str(week_start), str(week_end), "2d")
        return data, "miriade"
    except Exception as e:
        print(f"{body} Miriade FAILED: {e}")

    print(f"{body} → Swiss fallback")
    return swiss_body(swe.SUN, week_start, week_end), "swiss"


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
        "fixed_star_conjunctions": {}
    }

    resolved = 0

    for body, body_id in BODY_MAP.items():

        try:
            data, source = resolve_body(body, body_id, week_start, week_end)

            output["bodies"][body] = {
                "source": source,
                "data": data
            }

            resolved += 1

        except Exception as e:
            print(f"TOTAL FAILURE {body}: {e}")
            output["missing"].append(body)

    output["resolved"] = resolved
    output["coverage"] = round(resolved / output["total_targets"], 4)
    output["fixed_star_conjunctions"] = detect_star_conjunctions(output["bodies"])

    os.makedirs("docs", exist_ok=True)

    with open("docs/current_week.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print("Weekly transit file written to docs/current_week.json")


if __name__ == "__main__":
    main()
