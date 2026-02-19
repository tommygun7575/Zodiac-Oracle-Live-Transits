import math

# ------------------------------------------------------------
# ASPECT DEFINITIONS (degrees ± orb)
# ------------------------------------------------------------
ASPECTS = {
    "conjunction": 0,
    "sextile": 60,
    "square": 90,
    "trine": 120,
    "opposition": 180,
}

ORB_MAX = 10


# ------------------------------------------------------------
# BLACK ZODIAC BASE POWER
# ------------------------------------------------------------
BASE_POWER = {
    "conjunction": 1.40,
    "opposition": 1.60,
    "square": 1.50,
    "trine": 1.10,
    "sextile": 0.70,
}


# ------------------------------------------------------------
# FIXED STAR MULTIPLIER
# ------------------------------------------------------------
STAR_MULTIPLIER = {
    "Regulus": 1.8,
    "Spica": 1.5,
    "Aldebaran": 1.7,
    "Antares": 1.7,
    "Algol": 2.0,
    "Sirius": 1.6,
    "Canopus": 1.6,
    "Fomalhaut": 1.6,
}


# ------------------------------------------------------------
# TNO MULTIPLIERS
# ------------------------------------------------------------
TNO_MULTIPLIER = {
    "Sedna": 2.2,
    "Eris": 1.6,
    "Haumea": 1.6,
    "Makemake": 1.6,
    "Quaoar": 1.6,
    "Orcus": 1.4,
    "Varuna": 1.4,
    "Ixion": 1.4,
    "Salacia": 1.4,
    "Typhon": 1.8,
}


# ------------------------------------------------------------
# NORMALIZE ANGLE TO 0–360
# ------------------------------------------------------------
def norm(deg):
    while deg < 0:
        deg += 360
    while deg >= 360:
        deg -= 360
    return deg


# ------------------------------------------------------------
# ANGLE DIFFERENCE
# ------------------------------------------------------------
def angle_diff(a, b):
    diff = abs(a - b)
    if diff > 180:
        diff = 360 - diff
    return diff


# ------------------------------------------------------------
# ORB MULTIPLIER — precision weighting
# ------------------------------------------------------------
def orb_multiplier(orb):
    if orb > ORB_MAX:
        return 0
    return max(0, 1 - (orb / ORB_MAX))


# ------------------------------------------------------------
# HARMONIC MULTIPLIER
# ------------------------------------------------------------
def harmonic_multiplier(h):
    return 1 + (abs(h) % 10) / 20


# ------------------------------------------------------------
# Get star multiplier
# ------------------------------------------------------------
def star_mult(name_a, name_b):
    m = 1.0
    if name_a in STAR_MULTIPLIER:
        m *= STAR_MULTIPLIER[name_a]
    if name_b in STAR_MULTIPLIER:
        m *= STAR_MULTIPLIER[name_b]
    return m


# ------------------------------------------------------------
# Get TNO multiplier
# ------------------------------------------------------------
def tno_mult(name_a, name_b):
    m = 1.0
    if name_a in TNO_MULTIPLIER:
        m *= TNO_MULTIPLIER[name_a]
    if name_b in TNO_MULTIPLIER:
        m *= TNO_MULTIPLIER[name_b]
    return m


# ------------------------------------------------------------
# COMPUTE ASPECT BETWEEN TWO BODIES
# Returns dict or None
# ------------------------------------------------------------
def compute_aspect(name_a, a_lon, a_harm, name_b, b_lon, b_harm):
    diff = angle_diff(a_lon, b_lon)

    for asp_name, asp_angle in ASPECTS.items():
        orb = abs(diff - asp_angle)

        if orb <= ORB_MAX:
            base = BASE_POWER[asp_name]
            orb_m = orb_multiplier(orb)
            harm_m = (harmonic_multiplier(a_harm) + harmonic_multiplier(b_harm)) / 2
            star_m = star_mult(name_a, name_b)
            tno_m = tno_mult(name_a, name_b)

            score = base * orb_m * harm_m * star_m * tno_m

            return {
                "type": asp_name,
                "angle": round(diff, 2),
                "orb": round(orb, 2),
                "exact": asp_angle,
                "score": round(score, 4),
                "intensity": round(score * 100, 1),
            }

    return None


# ------------------------------------------------------------
# FULL ASPECT GRID
# bodies = {name: {"lon":..., "harmonics":...}}
# ------------------------------------------------------------
def compute_all_aspects(bodies):
    names = list(bodies.keys())
    aspects = {}

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a = names[i]
            b = names[j]

            a_lon = bodies[a]["lon"]
            b_lon = bodies[b]["lon"]
            a_harm = bodies[a]["harmonics"]
            b_harm = bodies[b]["harmonics"]

            asp = compute_aspect(a, a_lon, a_harm, b, b_lon, b_harm)

            if asp is not None:
                key = f"{a}-{b}"
                aspects[key] = asp

    return aspects
