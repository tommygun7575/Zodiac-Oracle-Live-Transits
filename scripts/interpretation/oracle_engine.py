import json
import os

# Internal imports
from scripts.utils.zodiac import zodiac_sign
from scripts.utils.harmonics import harmonics


# ------------------------------------------------------------
# LOAD RULE TABLES (planet, sign, house, aspect, myth, shadow)
# ------------------------------------------------------------
BASE_PATH = "oracle_data"

def load_json(name):
    path = os.path.join(BASE_PATH, name)
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


PLANET_RULES = load_json("planets.json")
SIGN_RULES = load_json("signs.json")
HOUSE_RULES = load_json("houses.json")
ASPECT_RULES = load_json("aspects.json")
TNO_RULES = load_json("tnos.json")
STAR_RULES = load_json("stars.json")


# ------------------------------------------------------------
# BLACK ZODIAC ORACLE PARAGRAPH BUILDER (Option D)
# ------------------------------------------------------------
def build_oracle_paragraph(body, pos, dominant_aspects):
    """
    Build a full Black Zodiac Oracle paragraph for one body.
    Uses template-driven sentence construction.
    """

    sign = pos["sign"]
    house = pos["house"]
    lon = pos["lon"]
    retro = pos["retrograde"]
    harm = pos["harmonics"]

    # Select tables
    p_rule = PLANET_RULES.get(body, {})
    s_rule = SIGN_RULES.get(sign, {})
    h_rule = HOUSE_RULES.get(str(house), {})

    # Determine aspect theme
    aspect_lines = []
    for asp in dominant_aspects:
        a_rule = ASPECT_RULES.get(asp["type"], {})
        if a_rule:
            line = a_rule.get("oracle", "").replace("{{other}}", asp["other"])
            aspect_lines.append(line)

    aspect_block = " ".join(aspect_lines[:2])

    # Planet rule
    p_oracle = p_rule.get("oracle", "")
    s_oracle = s_rule.get("oracle", "")
    h_oracle = h_rule.get("oracle", "")

    # Fusion in Canonical Black Zodiac Anchor Voice
    paragraph = (
        p_oracle.replace("{{sign}}", sign)
                .replace("{{house}}", str(house))
                .replace("{{retro}}", "retrograde" if retro else "direct")
                .replace("{{harm}}", str(round(harm, 2)))
        + " "
        + s_oracle.replace("{{planet}}", body)
        + " "
        + h_oracle.replace("{{planet}}", body)
        + " "
        + aspect_block
    )

    return paragraph.strip()


# ------------------------------------------------------------
# SELECT DOMINANT ASPECTS FOR EACH PLANET
# ------------------------------------------------------------
def pick_dominant_aspects(body, aspects):
    dominant = []
    for pair, detail in aspects.items():
        a, b = pair.split("-")
        if a == body:
            dominant.append({"other": b, "type": detail["type"], "orb": detail["orb"]})
        elif b == body:
            dominant.append({"other": a, "type": detail["type"], "orb": detail["orb"]})

    # Sort strongest (smallest orb first)
    dominant.sort(key=lambda x: x["orb"])
    return dominant[:3]


# ------------------------------------------------------------
# MAIN ORACLE ENTRY POINT
# ------------------------------------------------------------
def generate_oracle(transits):
    """
    Input: full transit dictionary (positions + aspects)
    Output: dictionary containing Oracle paragraphs
    """

    positions = transits["positions"]
    aspects = transits["aspects"]

    oracle_output = {}

    for body, pos in positions.items():
        dominant = pick_dominant_aspects(body, aspects)
        paragraph = build_oracle_paragraph(body, pos, dominant)
        oracle_output[body] = paragraph

    return oracle_output
