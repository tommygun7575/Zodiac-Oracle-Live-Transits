"""
Aspect Engine — Phase 3 Step 1
Computes aspects between all bodies based purely on angular geometry.

Supported aspects:
- Conjunction (0°)
- Sextile (60°)
- Square (90°)
- Trine (120°)
- Opposition (180°)

Orb system = Option C (tight precision):
Sun: 6°
Moon: 4°
Mercury/Venus/Mars: 3°
Jupiter/Saturn: 3°
Uranus/Neptune/Pluto: 2°
TNOs: 1°
Asteroids: 1°
"""

import math


# -------------------------------------------------------------
# ASPECT DEFINITIONS
# -------------------------------------------------------------
ASPECTS = {
    "conjunction": 0,
    "sextile": 60,
    "square": 90,
    "trine": 120,
    "opposition": 180,
}


# -------------------------------------------------------------
# ORB RULES (OPTION C)
# -------------------------------------------------------------
def orb_for(body):
    b = body.lower()

    if b in ["sun"]:
        return 6
    if b in ["moon"]:
        return 4
    if b in ["mercury", "venus", "mars"]:
        return 3
    if b in ["jupiter", "saturn"]:
        return 3
    if b in ["uranus", "neptune", "pluto"]:
        return 2

    # TNOs and asteroids
    return 1


# -------------------------------------------------------------
# ANGLE NORMALIZATION
# -------------------------------------------------------------
def angle_diff(a, b):
    """Normalize difference to absolute 0–180°."""
    d = abs(a - b) % 360
    return d if d <= 180 else 360 - d


# -------------------------------------------------------------
# CORE ASPECT DETECTOR
# -------------------------------------------------------------
def detect_aspects(body_positions):
    """
    body_positions = { "Sun": {"lon": X}, "Moon": {...}, ... }
    Returns:
    {
        "Sun-Moon": { "type": "square", "orb": 1.2, "exact": 90 },
        ...
    }
    """

    names = list(body_positions.keys())
    aspects = {}

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            b1 = names[i]
            b2 = names[j]

            lon1 = body_positions[b1]["lon"]
            lon2 = body_positions[b2]["lon"]

            diff = angle_diff(lon1, lon2)

            # compare against all aspects
            for asp_name, asp_angle in ASPECTS.items():
                orb = abs(diff - asp_angle)
                max_orb = min(orb_for(b1), orb_for(b2))

                if orb <= max_orb:
                    key = f"{b1}-{b2}"
                    aspects[key] = {
                        "type": asp_name,
                        "orb": round(orb, 2),
                        "exact": asp_angle,
                        "angle": round(diff, 2)
                    }

    return aspects
