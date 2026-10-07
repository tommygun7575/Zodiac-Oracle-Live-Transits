"""IMCCE Miriade week fetcher.

FRAME CONTRACT: geocentric APPARENT ecliptic longitude/latitude, true ecliptic &
equinox OF DATE (-observer=500, -teph=2, -rplane=2, -tcoor=1) — identical to
Horizons q31 and Swiss calc_ut defaults.
"""
import math
import re
from datetime import datetime

import requests

MIRIADE_URL = "https://ssp.imcce.fr/webservices/miriade/api/ephemcc.php"

_PREFIX = {
    "Sun": "p:Sun", "Moon": "s:Moon", "Mercury": "p:Mercury", "Venus": "p:Venus",
    "Mars": "p:Mars", "Jupiter": "p:Jupiter", "Saturn": "p:Saturn",
    "Uranus": "p:Uranus", "Neptune": "p:Neptune", "Pluto": "dp:Pluto",
}

_SEXA = re.compile(r"^\s*([+-]?)(\d+):(\d+):(\d+(?:\.\d*)?)\s*$")


def parse_angle(value):
    """Decimal degrees or sexagesimal 'DDD:MM:SS.s' -> float degrees."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(float(value)) else None
    text = str(value).strip()
    m = _SEXA.match(text)
    if m:
        sign = -1.0 if m.group(1) == "-" else 1.0
        return sign * (float(m.group(2)) + float(m.group(3)) / 60.0 + float(m.group(4)) / 3600.0)
    try:
        v = float(text)
    except ValueError:
        return None
    return v if math.isfinite(v) else None


def miriade_name(body):
    if ":" in str(body):
        return str(body)
    return _PREFIX.get(str(body), f"a:{body}")


def fetch_miriade(body, start, stop, nbd=7, step="1d"):
    """Fetch Miriade ecliptic longitudes (apparent, of date).

    ``nbd`` / ``step`` control sample count (e.g. nbd=28, step='6h' for
    4 UTC slots × 7 days). Pads/truncates to ``nbd`` rows.
    """
    if isinstance(start, datetime):
        epoch = start.strftime("%Y-%m-%dT%H:%M:%S")
    else:
        text = str(start)
        epoch = text if "T" in text else f"{text[:10]}T00:00:00"

    params = {
        "-name": miriade_name(body),
        "-ep": epoch,
        "-nbd": int(nbd),
        "-step": step,
        "-observer": "500",
        "-teph": "2",
        "-tcoor": "1",
        "-rplane": "2",
        "-mime": "json",
    }

    r = requests.get(MIRIADE_URL, params=params, timeout=60)

    if r.status_code != 200:
        raise RuntimeError(f"Miriade request failed for {body}")

    data = r.json()
    if isinstance(data, dict) and "data" not in data and "result" in data:
        data = data["result"]
    entries = data.get("data", []) if isinstance(data, dict) else []
    results = []

    for entry in entries[: int(nbd)]:
        row = {str(k).lower(): v for k, v in entry.items()} if isinstance(entry, dict) else {}
        lon = None
        lat = None
        for key in ("longitude", "ecllon", "elon"):
            if key in row:
                lon = parse_angle(row[key])
                if lon is not None:
                    break
        for key in ("latitude", "ecllat", "elat"):
            if key in row:
                lat = parse_angle(row[key])
                if lat is not None:
                    break
        if lon is not None:
            lon %= 360.0
        results.append({"lon": lon, "lat": lat})

    while len(results) < int(nbd):
        results.append({"lon": None, "lat": None})

    return results[: int(nbd)]
