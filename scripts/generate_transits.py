import json
from datetime import datetime, timedelta

from scripts.targets import TARGETS
from scripts.config import (
    STEP_SIZE_GENERAL,
    STEP_SIZE_MOON,
    COVERAGE_THRESHOLD
)
from scripts.bodies.horizons_client import fetch_ephemeris
from scripts.astrology_layers import (
    compute_arabic_parts_per_date,
    compute_harmonics_per_date,
    compute_fixed_star_conjunctions
)

def generate_week():

    today = datetime.utcnow().date()
    week_start = today
    week_end = today + timedelta(days=7)

    resolved = {}
    missing = []

    for name, body_id in TARGETS.items():

        try:

            step = STEP_SIZE_MOON if name == "Moon" else STEP_SIZE_GENERAL

            data = fetch_ephemeris(
                body_id,
                week_start.strftime("%Y-%m-%d"),
                week_end.strftime("%Y-%m-%d"),
                step
            )

            resolved[name] = {
                row["date"]: row["longitude_deg"]
                for row in data
            }

        except Exception:
            missing.append(name)

    coverage = len(resolved) / len(TARGETS)

    if coverage < COVERAGE_THRESHOLD:
        raise RuntimeError("Coverage below threshold")

    arabic_parts = compute_arabic_parts_per_date(resolved)
    harmonics = compute_harmonics_per_date(resolved)

    star_catalog = {}
    fixed_star_hits = compute_fixed_star_conjunctions(resolved, star_catalog)

    output = {
        "generated_utc": datetime.utcnow().isoformat(),
        "week_start": str(week_start),
        "week_end": str(week_end),
        "engine_version": "ZodiacOracle.LiveTransit.vFinal",
        "coverage": coverage,
        "resolved": len(resolved),
        "total_targets": len(TARGETS),
        "missing": missing,
        "bodies": resolved,
        "arabic_parts": arabic_parts,
        "harmonics": harmonics,
        "fixed_star_conjunctions": fixed_star_hits
    }

    with open("docs/current_week.json", "w") as f:
        json.dump(output, f, indent=2)


if __name__ == "__main__":
    generate_week()
