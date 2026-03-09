import json
import os
from datetime import datetime, timedelta
import swisseph as swe

from .bodies.horizons_client import fetch_jpl
from .bodies.miriade_client import fetch_miriade


# Expanded target body map
BODY_MAP = {

    # Luminaries
    "Sun": "10",
    "Moon": "301",

    # Personal
    "Mercury": "199",
    "Venus": "299",
    "Mars": "499",

    # Outer
    "Jupiter": "599",
    "Saturn": "699",
    "Uranus": "799",
    "Neptune": "899",
    "Pluto": "999",

    # Dwarf / TNO
    "Eris": "136199",
    "Haumea": "136108",
    "Makemake": "136472",
    "Sedna": "90377",
    "Orcus": "90482",
    "Gonggong": "225088",
    "Ixion": "28978",
    "Varuna": "20000",

    # Centaurs
    "Chiron": "2060",
    "Chariklo": "10199",
    "Pholus": "5145",
    "Nessus": "7066",
    "Asbolus": "8405",

    # Main Belt
    "Ceres": "1",
    "Pallas": "2",
    "Juno": "3",
    "Vesta": "4",
    "Hygiea": "10",
    "Psyche": "16",

    # NEO / Symbolic
    "Eros": "433",
    "Amor": "1221",
    "Apollo": "1862",
    "Adonis": "2101"
}


def generate_week_dates():
    today = datetime.utcnow().date()
    return today, today + timedelta(days=7)


def swiss_body(body_const, start, end):
    results = {}
    current = start

    while current <= end:
        jd = swe.julday(current.year, current.month, current.day)
        lon = swe.calc_ut(jd, body_const)[0][0] % 360
        results[current.strftime("%Y-%m-%d")] = lon
        current += timedelta(days=1)

    return results


def compute_harmonics(bodies, orders=(5, 7, 9)):
    harmonics = {}

    for order in orders:
        harmonics[str(order)] = {}

        for body, info in bodies.items():
            harmonics[str(order)][body] = {}

            for date, lon in info["data"].items():
                harmonics[str(order)][body][date] = (lon * order) % 360

    return harmonics


def compute_fixed_star_conjunctions(bodies, orb=1.0):
    stars = [
        "Regulus",
        "Spica",
        "Aldebaran",
        "Antares",
        "Fomalhaut",
        "Algol"
    ]

    results = {}

    for body, info in bodies.items():
        for date, lon in info["data"].items():

            jd = swe.julday(
                int(date[:4]),
                int(date[5:7]),
                int(date[8:10])
            )

            for star in stars:
                try:
                    star_data = swe.fixstar_ut(star, jd)
                    star_lon = star_data[0][0] % 360

                    diff = abs(lon - star_lon)
                    if diff > 180:
                        diff = 360 - diff

                    if diff <= orb:
                        if date not in results:
                            results[date] = []

                        results[date].append({
                            "body": body,
                            "star": star,
                            "orb": round(diff, 4)
                        })

                except Exception:
                    continue

    return results


def compute_part_of_fortune(bodies):
    parts = {}

    if "Sun" not in bodies or "Moon" not in bodies:
        return parts

    for date in bodies["Sun"]["data"]:
        try:
            sun_lon = bodies["Sun"]["data"][date]
            moon_lon = bodies["Moon"]["data"][date]

            # Simplified day formula (ASC not included in weekly engine)
            fortune = (moon_lon - sun_lon) % 360
            parts[date] = fortune

        except Exception:
            continue

    return parts


def main():

    week_start, week_end = generate_week_dates()

    output = {
        "generated_utc": datetime.utcnow().isoformat(),
        "week_start": str(week_start),
        "week_end": str(week_end),
        "engine_version": "ZodiacOracle.LiveTransit.vExpanded",
        "bodies": {},
        "harmonics": {},
        "arabic_parts": {},
        "fixed_star_conjunctions": {}
    }

    for body, body_id in BODY_MAP.items():

        try:

            if body == "Sun":
                data = swiss_body(swe.SUN, week_start, week_end)
                source = "swiss"

            elif body == "Moon":
                data = fetch_jpl(body_id, str(week_start), str(week_end), "1d")
                source = "jpl"

            else:
                data = fetch_jpl(body_id, str(week_start), str(week_end), "2d")
                source = "jpl"

            output["bodies"][body] = {
                "source": source,
                "data": data
            }

        except Exception:
            output["bodies"][body] = {
                "source": "missing",
                "data": {}
            }

    output["harmonics"] = compute_harmonics(output["bodies"])
    output["arabic_parts"]["Part_of_Fortune"] = compute_part_of_fortune(output["bodies"])
    output["fixed_star_conjunctions"] = compute_fixed_star_conjunctions(output["bodies"])

    os.makedirs("docs", exist_ok=True)

    with open("docs/current_week.json", "w") as f:
        json.dump(output, f, indent=2)

    print("Expanded weekly transit file written to docs/current_week.json")


if __name__ == "__main__":
    main()
