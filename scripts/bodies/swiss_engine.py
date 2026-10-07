import swisseph as swe
from datetime import datetime, timedelta
from pathlib import Path

# Prefer bundled ephe/ (symlink or copy); fall back to repo root for sefstars.txt
_REPO = Path(__file__).resolve().parents[2]
_EPHE = _REPO / "ephe"
swe.set_ephe_path(str(_EPHE if _EPHE.is_dir() else _REPO))

SWISS_BODY_MAP = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
    "Mean_Node": swe.MEAN_NODE,
    "True_Node": swe.TRUE_NODE,
    "Chiron": swe.CHIRON,
    "Ceres": swe.CERES,
    "Pallas": swe.PALLAS,
    "Juno": swe.JUNO,
    "Vesta": swe.VESTA,
}


def _to_datetime(value):
    if isinstance(value, datetime):
        return value
    text = str(value)
    if "T" in text:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    return datetime.strptime(text[:10], "%Y-%m-%d")


def _julday(dt: datetime) -> float:
    hour = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    return swe.julday(dt.year, dt.month, dt.day, hour)


def get_swiss_week(body_name, start_date, stop_date, step_days=1, snapshots=None):
    """Return Swiss positions.

    If ``snapshots`` is a list of datetime/ISO values, compute exactly those
    instants (preferred for multi-snapshot feeds). Otherwise step daily from
    start_date through stop_date by step_days.
    """
    if body_name not in SWISS_BODY_MAP:
        raise RuntimeError("Swiss does not support this body")

    body = SWISS_BODY_MAP[body_name]
    results = []

    if snapshots is not None:
        for stamp in snapshots:
            dt = _to_datetime(stamp)
            jd = _julday(dt)
            values = swe.calc_ut(jd, body)[0]
            results.append({
                "date": dt.strftime("%Y-%m-%d"),
                "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "longitude_deg": values[0],
                "latitude_deg": values[1] if len(values) > 1 else 0.0,
            })
        return results

    start = _to_datetime(start_date)
    stop = _to_datetime(stop_date)
    current = start
    while current <= stop:
        jd = _julday(current)
        values = swe.calc_ut(jd, body)[0]
        results.append({
            "date": current.strftime("%Y-%m-%d"),
            "timestamp": current.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "longitude_deg": values[0],
            "latitude_deg": values[1] if len(values) > 1 else 0.0,
        })
        current += timedelta(days=step_days)

    return results
