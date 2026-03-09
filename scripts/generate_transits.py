import json
from datetime import datetime, timedelta
from pathlib import Path

from .horizons_client import fetch_jpl
from .swiss_client import fetch_swiss
from .miriade_client import fetch_miriade


ENGINE_VERSION = "ZodiacOracle.LiveTransit.vHybrid"


# =====================================================
# SUNDAY ANCHOR LOGIC
# =====================================================

def get_week_range():
    today = datetime.utcnow().date()
    weekday = today.weekday()  # Monday=0 ... Sunday=6
    days_since_sunday = (weekday + 1) % 7
    week_start = today - timedelta(days=days_since_sunday)
    week_end = week_start + timedelta(days=7)
    return week_start, week_end


# =====================================================
# JD → ISO NORMALIZATION
# =====================================================

def normalize_keys_to_iso(data):
    normalized = {}
    for k, v in data.items():
        if "-" in str(k):
            normalized[k] = v
        else:
            jd = float(k)
            base = datetime(2000, 1, 1, 12)
            dt = base + timedelta(days=jd - 2451545.0)
            iso = dt.strftime("%Y-%m-%d")
            normalized[iso] = v
    return normalized


# =====================================================
# ARABIC PARTS (14)
# =====================================================

def norm(d):
    return d % 360


def compute_arabic_parts(positions):
    if "Sun" not in positions or "Moon" not in positions:
        return {}

    sun = positions["Sun"]
    moon = positions["Moon"]
    asc = sun  # Transit simplification

    parts = {}

    parts["Fortune"] = norm(asc + moon - sun)
    parts["Spirit"] = norm(asc + sun - moon)
    parts["Eros"] = norm(asc + positions.get("Venus", sun) - parts["Spirit"])
    parts["Victory"] = norm(asc + positions.get("Jupiter", sun) - sun)
    parts["Necessity"] = norm(asc + positions.get("Saturn", sun) - parts["Fortune"])
    parts["Courage"] = norm(asc + positions.get("Mars", sun) - parts["Spirit"])
    parts["Nemesis"] = norm(asc + positions.get("Saturn", sun) - moon)
    parts["Exaltation"] = norm(asc + sun - positions.get("Jupiter", sun))
    parts["Basis"] = norm(asc + positions.get("Mercury", sun) - moon)
    parts["Love"] = norm(asc + positions.get("Venus", sun) - moon)
    parts["Marriage"] = norm(asc + positions.get("Venus", sun) - positions.get("Saturn", sun))
    parts["Increase"] = norm(asc + positions.get("Jupiter", sun) - parts["Spirit"])
    parts["Commerce"] = norm(asc + positions.get("Mercury", sun) - positions.get("Jupiter", sun))
    parts["Passion"] = norm(asc + positions.get("Mars", sun) - positions.get("Venus", sun))

    return parts


# =====================================================
# FIXED STAR PRECISION
# =====================================================

FIXED_STARS = {
    "Regulus": 150.0,
    "Spica": 204.0,
    "Aldebaran": 69.0,
    "Antares": 249.0,
    "Fomalhaut": 333.0,
    "Algol": 53.0,
    "Sirius": 104.0,
    "Arcturus": 213.0,
    "Vega": 285.0,
    "Capella": 80.0
}

STAR_ORB = 1.0


def ang_sep(a, b):
    diff = abs(a - b)
    return min(diff, 360 - diff)


def compute_star_hits(positions):
    hits = []
    for body, lon in positions.items():
        for star, star_lon in FIXED_STARS.items():
            sep = ang_sep(lon, star_lon)
            if sep <= STAR_ORB:
                hits.append({
                    "body": body,
                    "star": star,
                    "orb": round(sep, 4)
                })
    return hits


# =====================================================
# TARGETS
# =====================================================

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


# =====================================================
# MAIN ENGINE
# =====================================================

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

    # Daily layer (2-day stepping)
    cursor = week_start
    while cursor <= week_end:

        iso = cursor.strftime("%Y-%m-%d")
        daily_positions = {}

        for body in output["bodies"]:
            body_data = output["bodies"][body]["data"]
            if iso in body_data:
                daily_positions[body] = body_data[iso]

        if daily_positions:
            output["arabic_parts"][iso] = compute_arabic_parts(daily_positions)

            star_hits = compute_star_hits(daily_positions)
            if star_hits:
                output["fixed_star_conjunctions"][iso] = star_hits

        cursor += timedelta(days=2)

    out_path = Path("docs/current_week.json")
    out_path.parent.mkdir(exist_ok=True)

    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print("Weekly transit file written to docs/current_week.json")


if __name__ == "__main__":
    main()
