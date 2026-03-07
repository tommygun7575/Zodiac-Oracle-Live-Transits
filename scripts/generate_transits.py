import json
import os
import sys
import math
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from math import fmod
import swisseph as swe
from dateutil import parser
import pytz

from scripts.sources import horizons_client, swiss_client, miriade_client
from scripts.utils.coords import ra_dec_to_ecl

ROOT = os.path.dirname(os.path.dirname(__file__))
DATA = os.path.join(ROOT, "data")

swe.set_ephe_path(os.path.join(ROOT, "ephe"))

NAME_ALIASES = {
    "Sun": ["Sun", "SUN"],
    "Moon": ["Moon", "MOON", "301"]
}


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize(deg: float) -> float:
    return fmod(deg + 360.0, 360.0)


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def compute_arabic_parts(asc, sun, moon):
    parts = {}

    is_day = (sun - asc) % 360 < 180

    fortune = asc + (moon - sun if is_day else sun - moon)
    spirit = asc + (sun - moon if is_day else moon - sun)
    karma = asc + (sun + moon) / 2.0
    treachery = asc + (moon - karma)
    victory = asc + (sun - karma)
    deliverance = asc + (spirit - fortune)

    for name, lon in {
        "Part_of_Fortune": fortune,
        "Part_of_Spirit": spirit,
        "Part_of_Karma": karma,
        "Part_of_Treachery": treachery,
        "Part_of_Victory": victory,
        "Part_of_Deliverance": deliverance,
    }.items():

        parts[name] = {
            "ecl_lon_deg": normalize(lon),
            "ecl_lat_deg": 0.0,
            "used_source": "calculated"
        }

    return parts


def compute_house_cusps(lat, lon, when_iso, hsys="P"):

    dt = parser.isoparse(when_iso)

    jd = swe.julday(
        dt.year,
        dt.month,
        dt.day,
        dt.hour + dt.minute/60.0 + dt.second/3600.0
    )

    cusps, ascmc = swe.houses(jd, lat, lon, hsys.encode("utf-8"))

    houses = {}

    for i, cusp in enumerate(cusps, start=1):
        houses[f"House_{i}"] = {
            "ecl_lon_deg": cusp,
            "ecl_lat_deg": 0.0,
            "used_source": f"houses-{hsys}"
        }

    houses["ASC"] = {
        "ecl_lon_deg": ascmc[0],
        "ecl_lat_deg": 0.0,
        "used_source": "houses"
    }

    houses["MC"] = {
        "ecl_lon_deg": ascmc[1],
        "ecl_lat_deg": 0.0,
        "used_source": "houses"
    }

    return houses


def compute_harmonics(base_positions: Dict[str, Dict[str, Any]]):

    harmonics = {}

    for body, pos in base_positions.items():

        if pos["ecl_lon_deg"] is None:
            continue

        lon = pos["ecl_lon_deg"]

        harmonics[f"{body}_h8"] = {
            "ecl_lon_deg": normalize(lon * 8 % 360),
            "ecl_lat_deg": 0.0,
            "used_source": "harmonic8"
        }

        harmonics[f"{body}_h9"] = {
            "ecl_lon_deg": normalize(lon * 9 % 360),
            "ecl_lat_deg": 0.0,
            "used_source": "harmonic9"
        }

    return harmonics


def resolve_body(name, sources, when_iso, force_fallback=False):

    got, used = None, None

    aliases = NAME_ALIASES.get(name, [name])

    for alias in aliases:

        for label, func in sources:

            try:
                pos = func(alias, when_iso)
            except Exception as e:
                print(f"[RESOLVER] {name} via {label} → ERROR: {e}")
                pos = None

            if pos:
                lon, lat = pos
                got, used = (lon, lat), label
                print(f"[RESOLVER] {name} → picked {label}")
                break

        if got:
            break

    if not got and force_fallback:

        got, used = (0.0, 0.0), "calculated-fallback"

        print(f"[RESOLVER] {name} → FORCED FALLBACK")

    return {
        "ecl_lon_deg": None if not got else float(got[0]),
        "ecl_lat_deg": None if not got else float(got[1]),
        "used_source": "missing" if not used else used
    }


def compute_positions(when_iso, lat, lon):

    out = {}

    MAJORS = [
        "Sun","Moon","Mercury","Venus","Mars",
        "Jupiter","Saturn","Uranus","Neptune","Pluto","Chiron"
    ]

    ASTEROIDS = [
        "Ceres","Pallas","Juno","Vesta","Psyche","Amor",
        "Eros","Astraea","Sappho","Karma","Bacchus","Hygiea","Nessus"
    ]

    TNOs = [
        "Eris","Sedna","Haumea","Makemake","Varuna",
        "Ixion","Typhon","Salacia","Orcus","Quaoar"
    ]

    AETHERS = [
        "Vulcan","Persephone","Hades","Proserpina","Isis"
    ]

    # SUN FIX (primary issue)
    out["Sun"] = resolve_body(
        "Sun",
        [
            ("jpl", horizons_client.get_ecliptic_lonlat),
            ("swiss", swiss_client.get_ecliptic_lonlat),
            ("miriade", miriade_client.get_ecliptic_lonlat)
        ],
        when_iso,
        force_fallback=True
    )

    for name in MAJORS:

        if name == "Sun":
            continue

        out[name] = resolve_body(
            name,
            [
                ("jpl", horizons_client.get_ecliptic_lonlat),
                ("swiss", swiss_client.get_ecliptic_lonlat),
                ("miriade", miriade_client.get_ecliptic_lonlat)
            ],
            when_iso,
            force_fallback=True
        )

    for name in ASTEROIDS:

        out[name] = resolve_body(
            name,
            [
                ("jpl", horizons_client.get_ecliptic_lonlat),
                ("swiss", swiss_client.get_ecliptic_lonlat),
                ("miriade", miriade_client.get_ecliptic_lonlat)
            ],
            when_iso,
            force_fallback=True
        )

    for name in TNOs:

        out[name] = resolve_body(
            name,
            [
                ("jpl", horizons_client.get_ecliptic_lonlat),
                ("swiss", swiss_client.get_ecliptic_lonlat),
                ("miriade", miriade_client.get_ecliptic_lonlat)
            ],
            when_iso,
            force_fallback=True
        )

    for name in AETHERS:

        out[name] = resolve_body(
            name,
            [("swiss", swiss_client.get_ecliptic_lonlat)],
            when_iso,
            force_fallback=True
        )

    stars = load_json(os.path.join(DATA, "fixed_stars.json"))["stars"]

    for s in stars:

        lam, bet = ra_dec_to_ecl(s["ra_deg"], s["dec_deg"], when_iso)

        out[s["id"]] = {
            "ecl_lon_deg": lam,
            "ecl_lat_deg": bet,
            "used_source": "fixed"
        }

    out.update(compute_house_cusps(lat, lon, when_iso))

    if "ASC" in out and "Sun" in out and "Moon" in out:

        asc = out["ASC"]["ecl_lon_deg"]
        sun = out["Sun"]["ecl_lon_deg"]
        moon = out["Moon"]["ecl_lon_deg"]

        if None not in (asc, sun, moon):
            out.update(compute_arabic_parts(asc, sun, moon))

    out.update(compute_harmonics(out))

    return out


def next_sunday():

    now = datetime.now(timezone.utc)

    days = (6 - now.weekday()) % 7

    if days == 0:
        days = 7

    return now + timedelta(days=days)


def main(argv):

    start = next_sunday()

    lat = 0.0
    lon = 0.0

    week = []

    for i in range(7):

        t = start + timedelta(days=i)

        when_iso = t.replace(microsecond=0).isoformat().replace("+00:00","Z")

        objects = compute_positions(when_iso, lat, lon)

        week.append({
            "timestamp": when_iso,
            "objects": objects
        })

    data = {
        "version": "oracle-weekly-transits",
        "generated_at": iso_now(),
        "week_start": week[0]["timestamp"],
        "days": week
    }

    os.makedirs("docs", exist_ok=True)

    with open("docs/current_week.json","w",encoding="utf-8") as f:
        json.dump(data,f,indent=2,ensure_ascii=False)

    print("[OK] weekly transit file written")


if __name__ == "__main__":
    main(sys.argv[1:])
