import json
from datetime import datetime, timedelta

from scripts.bodies.horizons_engine import get_body_week
from scripts.bodies.miriade_engine import get_miriade_week
from scripts.bodies.mpc_engine import get_mpc_week
from scripts.bodies.swiss_engine import get_swiss_week


COVERAGE_THRESHOLD = 0.92  # 92% minimum

ALL_BODIES = {
    # Planets
    "10": "Sun",
    "301": "Moon",
    "199": "Mercury",
    "299": "Venus",
    "499": "Mars",
    "599": "Jupiter",
    "699": "Saturn",
    "799": "Uranus",
    "899": "Neptune",
    "999": "Pluto",

    # Dwarf planets
    "136199": "Eris",
    "136108": "Haumea",
    "136472": "Makemake",

    # TNO examples
    "90377": "Sedna",
    "50000": "Quaoar",
    "90482": "Orcus"
}


def resolve_body(body_id, name, start, stop):

    # 1 — JPL
    try:
        return get_body_week(body_id, name, start, stop), "jpl_horizons"
    except Exception:
        pass

    # 2 — Miriade
    try:
        return get_miriade_week(body_id, name, start, stop), "miriade"
    except Exception:
        pass

    # 3 — MPC
    try:
        return get_mpc_week(body_id, name, start, stop), "mpc"
    except Exception:
        pass

    # 4 — Swiss
    try:
        return get_swiss_week(body_id, name, start, stop), "swiss"
    except Exception:
        pass

    return None, None


def generate_week():
    today = datetime.utcnow().date()
    start = today.strftime("%Y-%m-%d")
    stop = (today + timedelta(days=7)).strftime("%Y-%m-%d")

    bodies = {}
    missing = []

    total_targets = len(ALL_BODIES)

    for body_id, name in ALL_BODIES.items():
        result, source = resolve_body(body_id, name, start, stop)

        if result:
            key, data = result
            bodies[key] = {
                "source": source,
                "data": data
            }
        else:
            missing.append(name)

    coverage = len(bodies) / total_targets

    print(f"Coverage: {coverage * 100:.2f}%")

    if coverage < COVERAGE_THRESHOLD:
        raise RuntimeError(
            f"Coverage below threshold ({coverage*100:.2f}%). Aborting."
        )

    output = {
        "generated_utc": datetime.utcnow().isoformat(),
        "week_start": start,
        "week_end": stop,
        "engine_version": "ZodiacOracle.MultiSource.v3",
        "coverage": coverage,
        "resolved": len(bodies),
        "total_targets": total_targets,
        "missing": missing,
        "bodies": bodies
    }

    filename = f"docs/current_week_{start}.json"

    with open(filename, "w") as f:
        json.dump(output, f, indent=2)

    with open("docs/current_week.json", "w") as f:
        json.dump(output, f, indent=2)

    print("Weekly overlay generated successfully.")


if __name__ == "__main__":
    generate_week()
