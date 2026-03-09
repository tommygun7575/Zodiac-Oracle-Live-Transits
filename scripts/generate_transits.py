import json
import os
from datetime import datetime, timedelta
import swisseph as swe

from .bodies.horizons_client import fetch_jpl

# ─────────────────────────────
# Expanded Body Map
# ─────────────────────────────

BODY_MAP = {

    # Luminaries
    "Sun": "10",
    "Moon": "301",

    # Personal
    "Mercury": "199",
    "Venus": "299",
    "Mars": "499",

    # Social / Outer
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

    # NEO
    "Eros": "433",
    "Amor": "1221",
    "Apollo": "1862",
    "Adonis": "2101"
}

# Classification tags
CLASS_TAGS = {
    "Chiron": "centaur",
    "Chariklo": "centaur",
    "Pholus": "centaur",
    "Nessus": "centaur",
    "Asbolus": "centaur",

    "Eris": "dwarf",
    "Haumea": "dwarf",
    "Makemake": "dwarf",
    "Sedna": "detached",
    "Orcus": "plutino",
    "Gonggong": "scattered",
    "Ixion": "plutino",
    "Varuna": "classical",

    "Ceres": "main_belt",
    "Pallas": "main_belt",
    "Juno": "main_belt",
    "Vesta": "main_belt",
    "Hygiea": "main_belt",
    "Psyche": "metallic"
}


# ─────────────────────────────
# Core Utilities
# ─────────────────────────────

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


# ─────────────────────────────
# Harmonics 1–12
# ─────────────────────────────

def compute_harmonics(bodies):
    harmonics = {}

    for order in range(1, 13):
        harmonics[str(order)] = {}

        for body, info in bodies.items():
            harmonics[str(order)][body] = {}

            for date, lon in info["data"].items():
                harmonics[str(order)][body][date] = (lon * order) % 360

    return harmonics


# ─────────────────────────────
# Precision Fixed Stars (Swiss precessed)
# ─────────────────────────────

FIXED_STARS = [
    "Regulus",
    "Spica",
    "Aldebaran",
    "Antares",
    "Fomalhaut",
    "Algol",
    "Sirius",
    "Arcturus",
    "Capella",
    "Vega"
]


def compute_fixed_star_conjunctions(bodies, orb=1.0):
    results = {}

    for body, info in bodies.items():
        for date, lon in info["data"].items():

            jd = swe.julday(
                int(date[:4]),
                int(date[5:7]),
                int(date[8:10])
            )

            for star in FIXED_STARS:
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


# ─────────────────────────────
# Arabic Parts (12+)
# ─────────────────────────────

def compute_arabic_parts(bodies):
    parts = {}

    required = ["Sun", "Moon", "Mars", "Venus", "Jupiter", "Saturn"]

    if not all(p in bodies for p in required):
        return parts

    for date in bodies["Sun"]["data"]:

        try:
            sun = bodies["Sun"]["data"][date]
            moon = bodies["Moon"]["data"][date]
            mars = bodies["Mars"]["data"][date]
            venus = bodies["Venus"]["data"][date]
            jupiter = bodies["Jupiter"]["data"][date]
            saturn = bodies["Saturn"]["data"][date]

            parts[date] = {
                "Part_of_Fortune": (moon - sun) % 360,
                "Part_of_Spirit": (sun - moon) % 360,
                "Part_of_Eros": (venus - sun) % 360,
                "Part_of_Courage": (mars - saturn) % 360,
                "Part_of_Victory": (jupiter - mars) % 360,
                "Part_of_Nemesis": (saturn - sun) % 360,
                "Part_of_Father": (saturn - sun) % 360,
                "Part_of_Mother": (moon - venus) % 360,
                "Part_of_Children": (jupiter - saturn) % 360,
                "Part_of_Basis": (mars - sun) % 360,
                "Part_of_Commerce": (mercury := bodies["Mercury"]["data"][date]) - venus % 360,
                "Part_of_Marriage": (venus - saturn) % 360
            }

        except Exception:
            continue

    return parts


# ─────────────────────────────
# Main
# ─────────────────────────────

def main():

    week_start, week_end = generate_week_dates()

    output = {
        "generated_utc": datetime.utcnow().isoformat(),
        "week_start": str(week_start),
        "week_end": str(week_end),
        "engine_version": "ZodiacOracle.LiveTransit.vUltimate",
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
            else:
                data = fetch_jpl(body_id, str(week_start), str(week_end), "2d")
                source = "jpl"

            output["bodies"][body] = {
                "source": source,
                "class": CLASS_TAGS.get(body, "planetary"),
                "data": data
            }

        except Exception:
            output["bodies"][body] = {
                "source": "missing",
                "class": CLASS_TAGS.get(body, "unknown"),
                "data": {}
            }

    output["harmonics"] = compute_harmonics(output["bodies"])
    output["arabic_parts"] = compute_arabic_parts(output["bodies"])
    output["fixed_star_conjunctions"] = compute_fixed_star_conjunctions(output["bodies"])

    os.makedirs("docs", exist_ok=True)

    with open("docs/current_week.json", "w") as f:
        json.dump(output, f, indent=2)

    print("Ultimate weekly transit file written to docs/current_week.json")


if __name__ == "__main__":
    main()
