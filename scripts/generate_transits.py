import json
from datetime import datetime, timedelta
from scripts.bodies.horizons_engine import get_body_week


BODY_MAP = {
    "10": "Sun",
    "301": "Moon",
    "199": "Mercury",
    "299": "Venus",
    "499": "Mars",
    "599": "Jupiter",
    "699": "Saturn",
    "799": "Uranus",
    "899": "Neptune",
    "999": "Pluto"
}


def generate_week():
    today = datetime.utcnow().date()
    start = today.strftime("%Y-%m-%d")
    stop = (today + timedelta(days=7)).strftime("%Y-%m-%d")

    bodies = {}

    for body_id, name in BODY_MAP.items():
        print(f"Processing {name}")
        key, data = get_body_week(body_id, name, start, stop)
        bodies[key] = data

    if not bodies:
        raise RuntimeError("No bodies collected — aborting write.")

    output = {
        "generated_utc": datetime.utcnow().isoformat(),
        "week_start": start,
        "week_end": stop,
        "bodies": bodies
    }

    filename = f"docs/current_week_{start}.json"

    with open(filename, "w") as f:
        json.dump(output, f, indent=2)

    # also overwrite pointer file
    with open("docs/current_week.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Generated weekly file for {start}")
    print(f"Bodies collected: {len(bodies)}")


if __name__ == "__main__":
    generate_week()
