from scripts.config import MAX_HARMONIC, STAR_ORB_DEGREES

def compute_arabic_parts_per_date(bodies, ascendant_by_date=None):
    """Arabic parts require a true Ascendant.

    Without ascendant_by_date, returns status unavailable (never ASC=Sun).
    """
    if not ascendant_by_date:
        return {
            "status": "unavailable",
            "reason": "Arabic parts require Ascendant; compute on-device with Placidus ASC.",
            "Part_of_Fortune": {},
        }

    fortune = {}
    for date in bodies.get("Sun", {}):
        if date not in ascendant_by_date:
            continue
        sun = bodies["Sun"][date]
        moon = bodies["Moon"][date]
        asc = ascendant_by_date[date]
        fortune[date] = (asc + moon - sun) % 360

    return {"Part_of_Fortune": fortune}


def compute_harmonics_per_date(bodies):
    matrix = {}
    for body, data in bodies.items():
        for date, lon in data.items():
            if date not in matrix:
                matrix[date] = {}
            for h in range(2, MAX_HARMONIC + 1):
                key = f"H{h}"
                if key not in matrix[date]:
                    matrix[date][key] = {}
                matrix[date][key][body] = (lon * h) % 360
    return matrix


def compute_fixed_star_conjunctions(bodies, star_catalog):
    hits = {}
    for body, data in bodies.items():
        for date, lon in data.items():
            for star_name, star_lon in star_catalog.items():
                diff = abs((lon - star_lon + 360) % 360)
                if diff <= STAR_ORB_DEGREES:
                    hits.setdefault(date, []).append({"body": body, "star": star_name})
    return hits
