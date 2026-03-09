import json
from datetime import datetime, timedelta
from pathlib import Path

from .bodies.horizons_client import fetch_horizons, fetch_jpl
from .bodies.miriade_client import fetch_miriade as _fetch_miriade_single
from .bodies.miriade_engine import fetch_miriade as _fetch_miriade_week
from .bodies.mpc_client import fetch_mpc
from .bodies.swiss_engine import get_swiss_week

ENGINE_VERSION = "ZodiacOracle.LiveTransit.vHybrid"


# =====================================================
# ZODIAC SIGN HELPER
# =====================================================

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def zodiac(lon):
    """Convert ecliptic longitude to (sign_name, degree_within_sign)."""
    index = int(lon // 30) % 12
    degree = lon % 30
    return (ZODIAC_SIGNS[index], degree)


# =====================================================
# BODY REGISTRY
# =====================================================

# Small-body IDs use a trailing semicolon so that JPL Horizons resolves
# them via the Minor Planet Center (MPC) catalog rather than treating the
# numeric value as a NAIF planet-system barycenter ID (e.g. "1" is Mercury
# barycenter without the semicolon, but "1;" is Ceres via the MPC).
BODIES = {
    "Sun": None,
    "Moon": "301",
    "Mercury": "199",
    "Venus": "299",
    "Mars": "499",
    "Jupiter": "599",
    "Saturn": "699",
    "Uranus": "799",
    "Neptune": "899",
    "Pluto": "999",
    "Ceres": "1;",
    "Pallas": "2;",
    "Juno": "3;",
    "Vesta": "4;",
    "Psyche": "16;",
    "Eros": "433;",
    "Amor": "1221;",
    "Chiron": "2060;",
    "Pholus": "5145;",
    "Chariklo": "10199;",
    "Quaoar": "50000;",
    "Sedna": "90377;",
    "Orcus": "90482;",
    "Eris": "136199;",
    "Haumea": "136108;",
    "Makemake": "136472;",
    "Ixion": "28978;",
}


# =====================================================
# SOURCE FETCHERS (importable names used by resolve_body / fetch_body)
# =====================================================

def fetch_miriade(body_name, start_date=None):
    """Miriade lookup.

    Single-value mode (start_date omitted): returns {"lon": float}.
    Weekly mode (start_date provided as datetime): returns list of (lon, lat)
    tuples, one per day for 7 days starting from start_date.
    """
    if start_date is None:
        return _fetch_miriade_single(body_name)

    start_str = start_date.strftime("%Y-%m-%d")
    stop_str = (start_date + timedelta(days=6)).strftime("%Y-%m-%d")
    rows = _fetch_miriade_week(body_name, start_str, stop_str)
    return [(r["lon"], r["lat"]) for r in rows]


def fetch_swiss(body_name, date):
    """Swiss ephemeris lookup for a single day. Returns (lon, lat) tuple."""
    date_str = date.strftime("%Y-%m-%d") if hasattr(date, "strftime") else str(date)
    results = get_swiss_week(body_name, date_str, date_str, 1)
    if not results:
        raise RuntimeError(f"Swiss: no data for {body_name} on {date_str}")
    return (results[0]["longitude_deg"], 0.0)


# =====================================================
# SINGLE-BODY FETCH (fetch_body fallback chain)
# =====================================================

def fetch_body(body_name):
    """Fetch current-day position for a body, trying multiple sources.

    Fallback order: Horizons → Miriade → MPC.
    Returns {"lon": float}.
    """
    try:
        return fetch_horizons(body_name)
    except Exception:
        pass
    try:
        return fetch_miriade(body_name)
    except Exception:
        pass
    return fetch_mpc(body_name)


# =====================================================
# WEEKLY RESOLVER
# =====================================================

def resolve_body(body_name, start_date):
    """Resolve 7-day ephemeris for a body using JPL → Miriade → Swiss fallback.

    Per-day gap filling: JPL fills known slots; Miriade fills remaining None
    slots; Swiss fills any still-None slots.  Never raises; always returns
    exactly 7 entries with keys lon, lat, source.
    """
    result = [None] * 7
    start_str = start_date.strftime("%Y-%m-%d")
    stop_str = (start_date + timedelta(days=6)).strftime("%Y-%m-%d")

    # Step 1: Try JPL if the body has a mapped ID
    jpl_id = BODIES.get(body_name)
    if jpl_id is not None:
        try:
            jpl_data = fetch_jpl(jpl_id, start_str, stop_str)
            for i, entry in enumerate(jpl_data):
                if i >= 7:
                    break
                lon, lat = entry
                if lon is not None:
                    result[i] = {"lon": lon, "lat": lat, "source": "JPL"}
        except Exception:
            pass

    # Step 2: Fill gaps with Miriade
    if any(r is None for r in result):
        try:
            miriade_data = fetch_miriade(body_name, start_date)
            for i, entry in enumerate(miriade_data):
                if i >= 7:
                    break
                if result[i] is None:
                    lon, lat = entry
                    if lon is not None:
                        result[i] = {"lon": lon, "lat": lat, "source": "Miriade"}
        except Exception:
            pass

    # Step 3: Fill remaining gaps with Swiss (per day)
    for i in range(7):
        if result[i] is None:
            day = start_date + timedelta(days=i)
            try:
                lon, lat = fetch_swiss(body_name, day)
                result[i] = {"lon": lon, "lat": lat, "source": "Swiss"}
            except Exception:
                result[i] = {"lon": None, "lat": None, "source": "none"}

    return result


# =====================================================
# SUNDAY ANCHOR LOGIC
# =====================================================

def get_week_range():
    today = datetime.utcnow().date()
    weekday = today.weekday()  # Monday=0 ... Sunday=6
    days_since_sunday = (weekday + 1) % 7
    week_start = today - timedelta(days=days_since_sunday)
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


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
    "Capella": 80.0,
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
                    "orb": round(sep, 4),
                })
    return hits


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
        "total_targets": len(BODIES),
        "missing": [],
        "bodies": {},
        "arabic_parts": {},
        "fixed_star_conjunctions": {},
    }

    week_start_dt = datetime.strptime(start_str, "%Y-%m-%d")
    resolved = 0

    for name in BODIES:
        daily = resolve_body(name, week_start_dt)

        output["bodies"][name] = {
            "source": daily[0]["source"] if daily else "none",
            "data": {
                (week_start_dt + timedelta(days=i)).strftime("%Y-%m-%d"): entry["lon"]
                for i, entry in enumerate(daily)
                if entry["lon"] is not None
            },
        }

        if any(e["lon"] is not None for e in daily):
            resolved += 1
        else:
            output["missing"].append(name)

    output["resolved"] = resolved
    output["coverage"] = round(resolved / len(BODIES), 3)

    cursor = week_start_dt
    while cursor.date() <= week_end:

        iso = cursor.strftime("%Y-%m-%d")
        daily_positions = {}

        for body in output["bodies"]:
            body_data = output["bodies"][body]["data"]
            if iso in body_data and body_data[iso] is not None:
                daily_positions[body] = body_data[iso]

        if daily_positions:
            output["arabic_parts"][iso] = compute_arabic_parts(daily_positions)

            star_hits = compute_star_hits(daily_positions)
            if star_hits:
                output["fixed_star_conjunctions"][iso] = star_hits

        cursor += timedelta(days=1)

    out_path = Path("docs/current_week.json")
    out_path.parent.mkdir(exist_ok=True)

    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print("Weekly transit file written to docs/current_week.json")


if __name__ == "__main__":
    main()
