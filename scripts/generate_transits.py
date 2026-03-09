import json
import math
from datetime import datetime, timedelta
from pathlib import Path

from .horizons_client import fetch_jpl
from .swiss_client import fetch_swiss
from .miriade_client import fetch_miriade


ENGINE_VERSION = "ZodiacOracle.LiveTransit.vHybrid"


# =========================================================
# WEEK ANCHOR LOGIC — ALWAYS SUNDAY START
# =========================================================

def get_week_range():
    today = datetime.utcnow().date()
    weekday = today.weekday()  # Monday = 0, Sunday = 6

    # Move backward to most recent Sunday
    days_since_sunday = (weekday + 1) % 7
    week_start = today - timedelta(days=days_since_sunday)

    week_end = week_start + timedelta(days=7)

    return week_start, week_end


# =========================================================
# DATE NORMALIZATION
# =========================================================

def normalize_keys_to_iso(ephemeris_dict):
    normalized = {}
    for k, v in ephemeris_dict.items():
        # If already ISO
        if "-" in str(k):
            normalized[k] = v
        else:
            # JD -> ISO
            jd = float(k)
            base = datetime(2000, 1, 1, 12)
            dt = base + timedelta(days=jd - 2451545.0)
            iso = dt.strftime("%Y-%m-%d")
            normalized[iso] = v
    return normalized


# =========================================================
# ARABIC PARTS (12+)
# =========================================================

def normalize_deg(d):
    return d % 360


def compute_arabic_parts(date, bodies):
    parts = {}

    if not all(x in bodies for x in ["Sun", "Moon"]):
        return parts

    sun = bodies["Sun"]
    moon = bodies["Moon"]

    asc = sun  # Transit chart simplification (solar anchor)

    parts["Fortune"] = normalize_deg(asc + moon - sun)
    parts["Spirit"] = normalize_deg(asc + sun - moon)
    parts["Eros"] = normalize_deg(asc + bodies.get("Venus", sun) - parts["Spirit"])
    parts["Victory"] = normalize_deg(asc + bodies.get("Jupiter", sun) - sun)
    parts["Necessity"] = normalize_deg(asc + bodies.get("Saturn", sun) - parts["Fortune"])
    parts["Courage"] = normalize_deg(asc + bodies.get("Mars", sun) - parts["Spirit"])
    parts["Nemesis"] = normalize_deg(asc + bodies.get("Saturn", sun) - moon)
    parts["Exaltation"] = normalize_deg(asc + bodies.get("Sun", sun) - bodies.get("Jupiter", sun))
    parts["Basis"] = normalize_deg(asc + bodies.get("Mercury", sun) - moon)
    parts["Love"] = normalize_deg(asc + bodies.get("Venus", sun) - moon)
    parts["Marriage"] = normalize_deg(asc + bodies.get("Venus", sun) - bodies.get("Saturn", sun))
    parts["Increase"] = normalize_deg(asc + bodies.get("Jupiter", sun) - parts["Spirit"])
    parts["Commerce"] = normalize_deg(asc + bodies.get("Mercury", sun) - bodies.get("Jupiter", sun))
    parts["Passion"] = normalize_deg(asc + bodies.get("Mars", sun) - bodies.get("Venus", sun))

    return parts


# =========================================================
# FIXED STAR PRECISION LAYER
# =========================================================

FIXED_STARS = {
    "Regulus": 150.000,
    "Spica": 204.000,
    "Aldebaran": 69.000,
    "Antares": 249.000,
    "Fomalhaut": 333.000,
    "Algol": 53.000,
    "Sirius": 104.000,
    "Arcturus": 213.000,
    "Vega": 285.000,
    "Capella": 80.000
}

STAR_ORB = 1.0


def angular_sep(a, b):
    diff = abs(a - b)
    return min(diff, 360 - diff)


def compute_fixed_star_hits(date, body_positions):
    hits = []

    for body, lon in body_positions.items():
        for star, star_lon in FIXED_STARS.items():
            sep = angular_sep(lon, star_lon)
            if sep <= STAR_ORB:
                hits.append({
                    "body": body,
                    "star": star,
                    "orb": round(sep, 4)
                })

    return hits


# =========================================================
# TARGET LIST
# =========================================================

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
    "Eris": "200136199",
    "Haumea": "200136108",
    "Makemake": "200136472",
    "Sedna": "90377",
    "Quaoar": "50000",
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


# =========================================================
# MAIN ENGINE
# =========================================================

def main():

    week_start, week_end = get_week_range()

    start_str = week_start.strftime("%Y-%m-%d")
    stop_str = week_end.strftime("%Y-%m-%d")

    output = {
        "generated_utc": datetime.utcnow().isoformat(),
        "week_start": start_str,
        "week_end": stop_str,
        "engine_version": ENGINE_VERSION,
        "coverage": 0.0,
        "resolved": 0,
        "total_targets": len(TARGETS),
        "missing": [],
        "bodies": {},
        "arabic_parts": {},
        "fixed_star_conjunctions": {}
    }

    resolved = 0

    for name, code in TARGETS.items():

        try:
            if name == "Sun":
                data = fetch_swiss(name, start_str, stop_str, "2d")
                source = "swiss"
            else:
                data = fetch_jpl(code, start_str, stop_str, "2d")
                source = "jpl"

        except:
            try:
                data = fetch_miriade(code, start_str, stop_str)
                source = "miriade"
            except:
                data = fetch_swiss(name, start_str, stop_str, "2d")
                source = "swiss"

        data = normalize_keys_to_iso(data)

        output["bodies"][name] = {
            "source": source,
            "data": data
        }

        resolved += 1

    output["resolved"] = resolved
    output["coverage"] = round(resolved / len(TARGETS), 3)

    # ============================================
    # Daily Layer Processing
    # ============================================

    date_cursor = week_start
    while date_cursor <= week_end:

        date_iso = date_cursor.strftime("%Y-%m-%d")

        daily_positions = {}

        for body in output["bodies"]:
            body_data = output["bodies"][body]["data"]
            if date_iso in body_data:
                daily_positions[body] = body_data[date_iso]

        if daily_positions:

            # Arabic Parts
            output["arabic_parts"][date_iso] = compute_arabic_parts(
                date_iso,
                daily_positions
            )

            # Fixed Star Hits
            hits = compute_fixed_star_hits(date_iso, daily_positions)
            if hits:
                output["fixed_star_conjunctions"][date_iso] = hits

        date_cursor += timedelta(days=2)

    # ============================================
    # WRITE FILE
    # ============================================

    out_path = Path("docs/current_week.json")
    out_path.parent.mkdir(exist_ok=True)

    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print("Weekly transit file written to docs/current_week.json")


if __name__ == "__main__":
    main()
