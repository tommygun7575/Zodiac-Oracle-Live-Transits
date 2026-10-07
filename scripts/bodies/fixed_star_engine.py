import swisseph as swe
from datetime import datetime, timedelta
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_EPHE = _REPO / "ephe"
# sefstars.txt lives at repo root; planet files under ephe/
swe.set_ephe_path(str(_REPO))
if _EPHE.is_dir():
    swe.set_ephe_path(str(_EPHE))
    # Swiss looks for sefstars relative to ephe path; also try repo root copy
    if not (_EPHE / "sefstars.txt").exists() and (_REPO / "sefstars.txt").exists():
        try:
            (_EPHE / "sefstars.txt").symlink_to(_REPO / "sefstars.txt")
        except OSError:
            pass

EXCLUDED_CATALOG_ENTRIES = {"Test"}


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


def get_fixed_star_week(star_name, start_date, stop_date, step_days=1, snapshots=None):
    if star_name in EXCLUDED_CATALOG_ENTRIES:
        raise RuntimeError(f"'{star_name}' is a catalog artifact, not a real star")

    results = []

    if snapshots is not None:
        for stamp in snapshots:
            dt = _to_datetime(stamp)
            jd = _julday(dt)
            try:
                res = swe.fixstar2_ut(star_name, jd)
            except Exception as exc:
                raise RuntimeError(f"Fixed star '{star_name}' not found in catalog: {exc}")
            results.append({
                "date": dt.strftime("%Y-%m-%d"),
                "timestamp": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "longitude_deg": res[0][0],
                "latitude_deg": res[0][1],
            })
        return results

    start = _to_datetime(start_date)
    stop = _to_datetime(stop_date)
    current = start
    while current <= stop:
        jd = _julday(current)
        try:
            res = swe.fixstar2_ut(star_name, jd)
        except Exception as exc:
            raise RuntimeError(f"Fixed star '{star_name}' not found in catalog: {exc}")

        results.append({
            "date": current.strftime("%Y-%m-%d"),
            "timestamp": current.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "longitude_deg": res[0][0],
            "latitude_deg": res[0][1],
        })
        current += timedelta(days=step_days)

    return results
