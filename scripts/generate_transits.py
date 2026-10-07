"""Zodiac Oracle weekly live-transit generator.

Android contract (PRESERVE — additive only):
  docs/current_week.json top-level keys:
    generated_utc, week_start, week_end, engine_version, coverage, resolved,
    total_targets, missing, bodies, arabic_parts, fixed_star_conjunctions
  bodies[name] = { "source": str, "data": { "YYYY-MM-DD": lon, ... } }
  fixed_star_conjunctions[date] = [ {body, star, orb}, ... ]
  arabic_parts may be date→parts OR status unavailable (no ASC on universal feed)

Additive (safe for old parsers):
  bodies[name]["snapshots"] = { "YYYY-MM-DDTHH:MM:SSZ": lon, ... }  # 4×/day UTC
  snapshot_schedule_utc, houses (on-device Placidus policy), aether in bodies
"""
import json
import math
from datetime import datetime, timedelta
from pathlib import Path

from .bodies.horizons_client import fetch_horizons, fetch_jpl
from .bodies.miriade_client import fetch_miriade as _fetch_miriade_single
from .bodies.miriade_engine import fetch_miriade as _fetch_miriade_week
from .bodies.mpc_client import fetch_mpc
from .bodies.swiss_engine import get_swiss_week
from .bodies.fixed_star_engine import get_fixed_star_week
from .bodies.aether_engine import (
    VERIFIED_AETHER,
    compute_aether_from_positions,
)

ENGINE_VERSION = "ZodiacOracle.LiveTransit.vHybrid.multiSnap6h"
OUTPUT_PATH = Path("docs/current_week.json")

# 4 UTC snapshots per day × 7 days (Sunday→Saturday)
SNAPSHOT_HOURS_UTC = (0, 6, 12, 18)
SNAPSHOTS_PER_DAY = len(SNAPSHOT_HOURS_UTC)
SLOTS_PER_WEEK = 7 * SNAPSHOTS_PER_DAY  # 28
STEP_SIZE = "6h"

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
# BODY REGISTRY (expanded; IDs borrowed from Black-Zodiac)
# Small-body IDs use trailing semicolon for Horizons MPC lookup.
# =====================================================

BODIES = {
    # Core planets / luminaries
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
    # Lunar nodes (Swiss primary; no Horizons small-body id)
    "True_Node": None,
    "Mean_Node": None,
    # Dwarfs / major asteroids
    "Ceres": "1;",
    "Pallas": "2;",
    "Juno": "3;",
    "Vesta": "4;",
    "Hygiea": "10;",
    # Expanded asteroids
    "Astraea": "5;",
    "Psyche": "16;",
    "Amphitrite": "29;",
    "Euphrosyne": "31;",
    "Sappho": "80;",
    "Hekate": "100;",
    "Nemesis": "128;",
    "Eros": "433;",
    "Cupido": "763;",
    "Hidalgo": "944;",
    "Amor": "1221;",
    "Aphrodite": "1388;",
    "Aura": "1488;",
    "Bacchus": "2063;",
    "Merlin": "2598;",
    "Panacea": "2878;",
    "Karma": "3811;",
    "Destinn": "6583;",
    # Centaurs
    "Chiron": "2060;",
    "Pholus": "5145;",
    "Nessus": "7066;",
    "Asbolus": "8405;",
    "Chariklo": "10199;",
    "Hylonome": "10370;",
    # TNOs / dwarfs
    "Varuna": "20000;",
    "Ixion": "28978;",
    "Huya": "38628;",
    "Typhon": "42355;",
    "Quaoar": "50000;",
    "2002 AW197": "55565;",
    "2003 VS2": "84922;",
    "Sedna": "90377;",
    "Orcus": "90482;",
    "Salacia": "120347;",
    "Haumea": "136108;",
    "Eris": "136199;",
    "Makemake": "136472;",
    "Gonggong": "225088;",
}

# Fixed stars emitted as body positions (Black-Zodiac major set + Oracle set)
FIXED_STAR_BODIES = [
    "Aldebaran", "Algol", "Altair", "Antares", "Arcturus", "Betelgeuse",
    "Canopus", "Capella", "Deneb", "Fomalhaut", "Pollux", "Procyon",
    "Regulus", "Rigel", "Sirius", "Spica", "Vega", "Zubenelgenubi",
    "Zubeneschamali",
]

# Broader star list for conjunction hits only (existing Oracle set, additive)
FIXED_STARS = sorted(set(FIXED_STAR_BODIES + [
    "Aboras", "Ainalrami", "Al Krikab", "Al Nitham", "Al Sadr al Ketus",
    "Alagemin", "Alathfar", "Aldafirah", "Aldhibain", "Alifa Al Farkadain",
    "Alioth", "Alkalurops", "Alminhar", "Alrischa", "Alsephina", "Alshain",
    "Alsharasif", "Altawk", "Aludra", "Alzirr", "Anunitum", "Arkab Posterior",
    "Ascella", "Asellus Australis", "Asterope", "Atik", "Atirsagne", "Auva",
    "Beemim", "Beid", "Bered", "Botein", "Celaeno", "Cervantes", "Edasich",
    "Electra", "Enif", "Fornacis", "Gorgona Quatra", "Haedi", "Hydrobius",
    "Izar", "Jabbah", "Jih", "Kaht", "Kang", "Kaus Australis", "Libertas",
    "Maaz", "Maia", "Menkar", "Merak", "Mirfak", "Mizar", "Mufrid", "Nanto",
    "Nekkar", "Nodus II", "Nunki", "Ras Elased Australis", "Ruc", "Rukbat",
    "Segin", "Sheratan", "Skat", "Taiyi", "Taygeta", "Tegmen", "Terebellium",
    "Torcularis Septentrionalis", "Tse Tseng", "Tseen Foo", "Unukalhai",
    "Unurgunite", "Urodelus", "Vindemiatrix", "Vishakha",
]))

STAR_ORB = 1.0

HOUSES_POLICY = {
    "status": "on_device",
    "system": "Placidus",
    "reason": (
        "Universal weekly feed is geocentric and location-independent. "
        "House cusps, ASC, and MC require the user's lat/lon and must be "
        "computed on-device (Placidus). No whole-sign house fields are "
        "emitted here; ASC is never approximated as the Sun."
    ),
}

ARABIC_PARTS_UNAVAILABLE = {
    "status": "unavailable",
    "reason": (
        "Arabic parts require a true Ascendant from observer lat/lon. "
        "This universal feed does not invent ASC=Sun. Compute parts "
        "on-device with Placidus ASC/MC."
    ),
}


def fetch_miriade(body_name, start_date=None, nbd=None, step=None):
    """Miriade lookup.

    Single-value mode (start_date omitted): returns {"lon": float}.
    Weekly/multi-slot mode (start_date provided): returns list of (lon, lat).
    """
    if start_date is None:
        return _fetch_miriade_single(body_name)

    if nbd is None:
        nbd = SLOTS_PER_WEEK
    if step is None:
        step = STEP_SIZE

    if hasattr(start_date, "strftime"):
        start_str = start_date.strftime("%Y-%m-%dT%H:%M:%S")
        stop_str = (start_date + timedelta(days=6, hours=18)).strftime("%Y-%m-%dT%H:%M:%S")
    else:
        start_str = str(start_date)
        stop_str = start_str

    rows = _fetch_miriade_week(body_name, start_str, stop_str, nbd=nbd, step=step)
    return [(r["lon"], r["lat"]) for r in rows]


def fetch_swiss(body_name, date):
    """Swiss ephemeris lookup for a single instant. Returns (lon, lat)."""
    if hasattr(date, "strftime"):
        date_str = date.strftime("%Y-%m-%dT%H:%M:%S")
        results = get_swiss_week(body_name, date_str, date_str, snapshots=[date])
    else:
        date_str = str(date)
        results = get_swiss_week(body_name, date_str, date_str, 1)
    if not results:
        raise RuntimeError(f"Swiss: no data for {body_name} on {date_str}")
    lat = results[0].get("latitude_deg", 0.0)
    return (results[0]["longitude_deg"], lat if lat is not None else 0.0)


def _is_valid_number(value):
    return isinstance(value, (int, float)) and math.isfinite(value)


def fetch_body(body_name):
    """Fetch current-day position. Order: Horizons → Miriade → MPC."""
    try:
        return fetch_horizons(body_name)
    except Exception:
        pass
    try:
        return fetch_miriade(body_name)
    except Exception:
        pass
    return fetch_mpc(body_name)


def week_snapshot_datetimes(week_start):
    """Return 28 datetimes: each day of the week at 00/06/12/18 UTC."""
    if isinstance(week_start, datetime):
        base = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        base = datetime.strptime(str(week_start)[:10], "%Y-%m-%d")
    stamps = []
    for day in range(7):
        d = base + timedelta(days=day)
        for hour in SNAPSHOT_HOURS_UTC:
            stamps.append(d.replace(hour=hour, minute=0, second=0, microsecond=0))
    return stamps


def snapshot_iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_body(body_name, start_date, snapshots=None):
    """Resolve ephemeris for a body: JPL → Miriade → Swiss.

    Returns a list aligned to ``snapshots`` (default: 28 week slots).
    Each entry: {lon, lat, source, timestamp}. Never raises.
    """
    if snapshots is None:
        snapshots = week_snapshot_datetimes(start_date)
    n = len(snapshots)
    result = [None] * n
    start_str = snapshot_iso(snapshots[0])
    # Horizons stop is exclusive of final step in some modes; pad +6h
    stop_str = snapshot_iso(snapshots[-1] + timedelta(hours=6))

    jpl_id = BODIES.get(body_name)
    if jpl_id is not None:
        try:
            jpl_data = fetch_jpl(jpl_id, start_str, stop_str, step_size=STEP_SIZE)
            for i, entry in enumerate(jpl_data):
                if i >= n:
                    break
                lon, lat = entry
                if _is_valid_number(lon):
                    result[i] = {
                        "lon": lon,
                        "lat": lat,
                        "source": "JPL",
                        "timestamp": snapshot_iso(snapshots[i]),
                    }
        except Exception:
            pass

    if any(r is None for r in result):
        try:
            miriade_data = fetch_miriade(body_name, snapshots[0], nbd=n, step=STEP_SIZE)
            for i, entry in enumerate(miriade_data):
                if i >= n:
                    break
                if result[i] is None:
                    lon, lat = entry
                    if _is_valid_number(lon):
                        result[i] = {
                            "lon": lon,
                            "lat": lat,
                            "source": "Miriade",
                            "timestamp": snapshot_iso(snapshots[i]),
                        }
        except Exception:
            pass

    for i in range(n):
        if result[i] is None:
            try:
                lon, lat = fetch_swiss(body_name, snapshots[i])
                result[i] = {
                    "lon": lon if _is_valid_number(lon) else None,
                    "lat": lat if _is_valid_number(lat) else None,
                    "source": "Swiss",
                    "timestamp": snapshot_iso(snapshots[i]),
                }
            except Exception:
                result[i] = {
                    "lon": None,
                    "lat": None,
                    "source": "none",
                    "timestamp": snapshot_iso(snapshots[i]),
                }

    return result


def get_week_range():
    today = datetime.utcnow().date()
    weekday = today.weekday()  # Monday=0 ... Sunday=6
    days_since_sunday = (weekday + 1) % 7
    week_start = today - timedelta(days=days_since_sunday)
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def norm(d):
    return d % 360


def compute_arabic_parts(positions):
    """Deprecated for universal feed — requires true ASC.

    Kept as a callable for tests/tools; main() does NOT emit ASC=Sun parts.
    """
    if "Sun" not in positions or "Moon" not in positions:
        return {}
    # Intentionally refuse without an explicit Ascendant key.
    if "Ascendant" not in positions and "ASC" not in positions:
        return dict(ARABIC_PARTS_UNAVAILABLE)
    asc = positions.get("Ascendant", positions.get("ASC"))
    sun = positions["Sun"]
    moon = positions["Moon"]
    parts = {
        "Fortune": norm(asc + moon - sun),
        "Spirit": norm(asc + sun - moon),
        "Eros": norm(asc + positions.get("Venus", sun) - norm(asc + sun - moon)),
        "Victory": norm(asc + positions.get("Jupiter", sun) - sun),
        "Necessity": norm(asc + positions.get("Saturn", sun) - norm(asc + moon - sun)),
        "Courage": norm(asc + positions.get("Mars", sun) - norm(asc + sun - moon)),
        "Nemesis": norm(asc + positions.get("Saturn", sun) - moon),
        "Exaltation": norm(asc + sun - positions.get("Jupiter", sun)),
        "Basis": norm(asc + positions.get("Mercury", sun) - moon),
        "Love": norm(asc + positions.get("Venus", sun) - moon),
        "Marriage": norm(asc + positions.get("Venus", sun) - positions.get("Saturn", sun)),
        "Increase": norm(asc + positions.get("Jupiter", sun) - norm(asc + sun - moon)),
        "Commerce": norm(asc + positions.get("Mercury", sun) - positions.get("Jupiter", sun)),
        "Passion": norm(asc + positions.get("Mars", sun) - positions.get("Venus", sun)),
    }
    return parts


def ang_sep(a, b):
    diff = abs(a - b)
    return min(diff, 360 - diff)


def compute_star_hits(positions, star_positions_for_slot):
    hits = []
    for body, lon in positions.items():
        if body in star_positions_for_slot:
            continue  # skip star-star
        for star, star_lon in star_positions_for_slot.items():
            sep = ang_sep(lon, star_lon)
            if sep <= STAR_ORB:
                hits.append({
                    "body": body,
                    "star": star,
                    "orb": round(sep, 4),
                })
    return hits


def _pack_body_series(daily_entries, snapshots):
    """Build Android-compatible data (date→lon) + additive snapshots (iso→lon)."""
    data = {}
    snap = {}
    for i, entry in enumerate(daily_entries):
        if not _is_valid_number(entry.get("lon")):
            continue
        ts = entry.get("timestamp") or snapshot_iso(snapshots[i])
        snap[ts] = entry["lon"]
        # Daily key = 00:00 UTC slot for that calendar day (legacy Android path)
        if ts.endswith("T00:00:00Z") or (i % SNAPSHOTS_PER_DAY == 0):
            day_key = ts[:10]
            # Prefer exact 00:00; otherwise first available slot that day
            if day_key not in data or ts.endswith("T00:00:00Z"):
                data[day_key] = entry["lon"]
    # Ensure every day with any slot gets a daily key (fallback to first slot)
    for i, entry in enumerate(daily_entries):
        if not _is_valid_number(entry.get("lon")):
            continue
        day_key = snapshots[i].strftime("%Y-%m-%d")
        if day_key not in data:
            data[day_key] = entry["lon"]
    source = "none"
    for entry in daily_entries:
        if _is_valid_number(entry.get("lon")):
            source = entry.get("source", "none")
            break
    return {"source": source, "data": data, "snapshots": snap}


def _new_output_template(start_str, stop_str):
    return {
        "generated_utc": datetime.utcnow().isoformat(),
        "week_start": start_str,
        "week_end": stop_str,
        "engine_version": ENGINE_VERSION,
        "coverage": 0.0,
        "resolved": 0,
        "total_targets": len(BODIES) + len(FIXED_STAR_BODIES) + len(VERIFIED_AETHER),
        "missing": [],
        "bodies": {},
        "arabic_parts": dict(ARABIC_PARTS_UNAVAILABLE),
        "fixed_star_conjunctions": {},
        # Additive metadata (ignored by old Android parsers)
        "snapshot_schedule_utc": {
            "hours": list(SNAPSHOT_HOURS_UTC),
            "interval_hours": 6,
            "slots_per_day": SNAPSHOTS_PER_DAY,
            "slots_per_week": SLOTS_PER_WEEK,
            "note": "App may pick nearest ISO timestamp in bodies[*].snapshots",
        },
        "houses": dict(HOUSES_POLICY),
        "aether_formulas": list(VERIFIED_AETHER),
    }


def _is_valid_output_payload(payload):
    """Android / CI contract: required keys must exist; bodies must be a dict."""
    required = {
        "generated_utc",
        "week_start",
        "week_end",
        "engine_version",
        "coverage",
        "resolved",
        "total_targets",
        "missing",
        "bodies",
        "arabic_parts",
        "fixed_star_conjunctions",
    }
    if not isinstance(payload, dict):
        return False
    if not required.issubset(payload):
        return False
    if not isinstance(payload["bodies"], dict) or not isinstance(payload["missing"], list):
        return False
    # Backward-compat shape: each body has source + data with YYYY-MM-DD keys
    for name, body in payload["bodies"].items():
        if not isinstance(body, dict):
            return False
        if "source" not in body or "data" not in body:
            return False
        if not isinstance(body["data"], dict):
            return False
        for key in body["data"]:
            # Daily keys must remain YYYY-MM-DD for TransitParser
            if len(key) == 10 and key[4] == "-" and key[7] == "-":
                continue
            # Allow only date keys inside data (snapshots live separately)
            return False
    return True


def _android_can_read(payload):
    """Simulate TransitParser date selection: today or max date key."""
    bodies = payload.get("bodies") or {}
    if not bodies:
        return False
    today = datetime.utcnow().strftime("%Y-%m-%d")
    readable = 0
    for name, body in bodies.items():
        data = body.get("data") or {}
        if not data:
            continue
        active = today if today in data else max(data.keys())
        lon = data.get(active)
        if _is_valid_number(lon):
            readable += 1
    return readable > 0


def _write_json_atomic(path, payload):
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(tmp_path, "w") as f:
        json.dump(payload, f, indent=2)
    tmp_path.replace(path)


def main(output_path=OUTPUT_PATH):
    week_start, week_end = get_week_range()
    start_str = week_start.strftime("%Y-%m-%d")
    stop_str = week_end.strftime("%Y-%m-%d")

    output_path = Path(output_path)
    output_path.parent.mkdir(exist_ok=True)
    output = _new_output_template(start_str, stop_str)

    try:
        week_start_dt = datetime.strptime(start_str, "%Y-%m-%d")
        snapshots = week_snapshot_datetimes(week_start_dt)
        resolved = 0

        # Fixed-star longitudes per snapshot (for conjunctions + body emission)
        star_by_ts = {snapshot_iso(s): {} for s in snapshots}
        for star_name in FIXED_STARS:
            try:
                star_rows = get_fixed_star_week(
                    star_name, start_str, stop_str, snapshots=snapshots
                )
            except Exception:
                continue
            for row in star_rows:
                ts = row.get("timestamp") or f"{row['date']}T00:00:00Z"
                star_by_ts.setdefault(ts, {})[star_name] = row["longitude_deg"]

        # Moving bodies
        for name in BODIES:
            daily = resolve_body(name, week_start_dt, snapshots=snapshots)
            packed = _pack_body_series(daily, snapshots)
            output["bodies"][name] = packed
            if packed["data"]:
                resolved += 1
            else:
                output["missing"].append(name)

        # South Node (True Node + 180) — calculated, no fabricated provider coords
        if "True_Node" in output["bodies"] and output["bodies"]["True_Node"]["data"]:
            tn = output["bodies"]["True_Node"]
            south_data = {d: (lon + 180.0) % 360.0 for d, lon in tn["data"].items()}
            south_snap = {t: (lon + 180.0) % 360.0 for t, lon in tn.get("snapshots", {}).items()}
            output["bodies"]["South_Node"] = {
                "source": "calculated",
                "data": south_data,
                "snapshots": south_snap,
            }
            resolved += 1

        # Fixed-star bodies (positions)
        for star_name in FIXED_STAR_BODIES:
            entries = []
            for i, snap in enumerate(snapshots):
                ts = snapshot_iso(snap)
                lon = star_by_ts.get(ts, {}).get(star_name)
                entries.append({
                    "lon": lon,
                    "lat": None,
                    "source": "Swiss" if _is_valid_number(lon) else "none",
                    "timestamp": ts,
                })
            packed = _pack_body_series(entries, snapshots)
            if packed["data"]:
                output["bodies"][star_name] = packed
                resolved += 1
            else:
                output["missing"].append(star_name)

        # Aether (3 verified formulas) per snapshot → daily data + snapshots
        aether_series = {name: [] for name in VERIFIED_AETHER}
        for i, snap in enumerate(snapshots):
            day_key = snap.strftime("%Y-%m-%d")
            ts = snapshot_iso(snap)
            # Prefer this slot's longitude from body snapshots; fall back to daily
            pos = {}
            for bname, bobj in output["bodies"].items():
                lon = (bobj.get("snapshots") or {}).get(ts)
                if lon is None:
                    lon = (bobj.get("data") or {}).get(day_key)
                if _is_valid_number(lon):
                    pos[bname] = lon
            aether_vals = compute_aether_from_positions(pos)
            for aname, alon in aether_vals.items():
                aether_series[aname].append({
                    "lon": alon,
                    "lat": 0.0,
                    "source": "calculated",
                    "timestamp": ts,
                })
        for aname, entries in aether_series.items():
            packed = _pack_body_series(entries, snapshots)
            if packed["data"]:
                output["bodies"][aname] = packed
                resolved += 1
            else:
                output["missing"].append(aname)

        moving_and_calc_targets = (
            len(BODIES) + 1 + len(FIXED_STAR_BODIES) + len(VERIFIED_AETHER)
        )  # +1 South_Node
        output["total_targets"] = moving_and_calc_targets
        output["resolved"] = resolved
        output["coverage"] = round(resolved / max(moving_and_calc_targets, 1), 3)

        # Arabic parts: unavailable on universal feed (no natal ASC)
        output["arabic_parts"] = dict(ARABIC_PARTS_UNAVAILABLE)

        # Fixed-star conjunctions keyed by YYYY-MM-DD (Android contract)
        # Use 00:00 UTC slot positions for the daily hit list.
        for day in range(7):
            day_dt = week_start_dt + timedelta(days=day)
            iso_day = day_dt.strftime("%Y-%m-%d")
            ts0 = f"{iso_day}T00:00:00Z"
            daily_positions = {}
            for body, bobj in output["bodies"].items():
                if body in FIXED_STAR_BODIES or body in VERIFIED_AETHER:
                    continue
                lon = (bobj.get("snapshots") or {}).get(ts0)
                if lon is None:
                    lon = (bobj.get("data") or {}).get(iso_day)
                if _is_valid_number(lon):
                    daily_positions[body] = lon
            star_hits = compute_star_hits(daily_positions, star_by_ts.get(ts0, {}))
            if star_hits:
                output["fixed_star_conjunctions"][iso_day] = star_hits

        if not _is_valid_output_payload(output):
            raise RuntimeError("Generated payload failed validation")
        if not _android_can_read(output):
            raise RuntimeError("Generated payload not readable by Android date parser")

    except Exception as exc:
        output = _new_output_template(start_str, stop_str)
        output["generation_warning"] = str(exc)

    _write_json_atomic(output_path, output)
    print(f"Weekly transit file written to {output_path}")
    return output


if __name__ == "__main__":
    main()
