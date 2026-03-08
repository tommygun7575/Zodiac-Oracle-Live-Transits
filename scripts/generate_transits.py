import json
from datetime import datetime, timedelta

from scripts.bodies.horizons_engine import get_body_week
from scripts.bodies.miriade_engine import get_miriade_week
from scripts.bodies.mpc_engine import get_mpc_week
from scripts.bodies.swiss_engine import get_swiss_week


COVERAGE_THRESHOLD = 0.92
HARMONIC_MIN = 2
HARMONIC_MAX = 12  # dynamic range (change freely)

# Curated master registry (expand carefully)
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

    # Dwarf / TNO
    "136199": "Eris",
    "136108": "Haumea",
    "136472": "Makemake",
    "90377": "Sedna",
    "50000": "Quaoar",
    "90482": "Orcus",

    # Centaurs
    "2060": "Chiron",
    "10199": "Chariklo",
    "5145": "Pholus",

    # Key Asteroids
    "1": "Ceres",
    "2": "Pallas",
    "3": "Juno",
    "4": "Vesta",
    "16": "Psyche",
    "433": "Eros",
    "1221": "Amor"
}

# Fixed star catalog (curated)
FIXED_STARS = {
    "Regulus": 150.0,
    "Spica": 204.0,
    "Aldebaran": 69.0,
    "Antares": 249.0
}

ORB = 1.0  # degree orb


def resolve_body(body_id, name, start, stop):

    try:
        return get_body_week(body_id, name, start, stop), "jpl"
    except:
        pass

    try:
        return get_miriade_week(body_id, name, start, stop), "miriade"
    except:
        pass

    try:
        return get_mpc_week(body_id, name, start, stop), "mpc"
    except:
        pass

    try:
        return get_swiss_week(body_id, name, start, stop), "swiss"
    except:
        pass

    return None, None


def compute_arabic_parts(bodies):
    parts = {}

    try:
        sun = float(bodies["Sun"]["data"][0]["longitude_deg"])
        moon = float(bodies["Moon"]["data"][0]["longitude_deg"])

        # Placeholder ASC (real ASC requires location + time calc)
        asc = (sun + 90) % 360

        fortune = (asc + moon - sun) % 360
        parts["Part_of_Fortune"] = fortune

    except:
        pass

    return parts


def compute_harmonics(bodies, h_min, h_max):
    harmonic_output = {}

    for h in range(h_min, h_max + 1):
        harmonic_output[f"H{h}"] = {}
        for name, obj in bodies.items():
            try:
                lon = float(obj["data"][0]["longitude_deg"])
                harmonic_output[f"H{h}"][name] = (lon * h) % 360
            except:
                pass

    return harmonic_output


def compute_fixed_star_conjunctions(bodies):
    results = {}

    for body_name, obj in bodies.items():
        try:
            lon = float(obj["data"][0]["longitude_deg"])
            for star, star_lon in FIXED_STARS.items():
                diff = abs(lon - star_lon)
                if diff <= ORB or abs(diff - 360) <= ORB:
                    results.setdefault(body_name, []).append(star)
        except:
            pass

    return results


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

    arabic_parts = compute_arabic_parts(bodies)
    harmonics = compute_harmonics(bodies, HARMONIC_MIN, HARMONIC_MAX)
    fixed_star_hits = compute_fixed_star_conjunctions(bodies)

    output = {
        "generated_utc": datetime.utcnow().isoformat(),
        "week_start": start,
        "week_end": stop,
        "engine_version": "ZodiacOracle.Curated.vFinal",
        "coverage": coverage,
        "resolved": len(bodies),
        "total_targets": total_targets,
        "missing": missing,
        "bodies": bodies,
        "arabic_parts": arabic_parts,
        "harmonics": harmonics,
        "fixed_star_conjunctions": fixed_star_hits
    }

    filename = f"docs/current_week_{start}.json"

    with open(filename, "w") as f:
        json.dump(output, f, indent=2)

    with open("docs/current_week.json", "w") as f:
        json.dump(output, f, indent=2)

    print("Weekly overlay generated successfully.")


if __name__ == "__main__":
    generate_week()
