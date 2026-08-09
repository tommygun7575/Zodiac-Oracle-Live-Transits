import swisseph as swe
from datetime import datetime, timedelta

swe.set_ephe_path(".")

EXCLUDED_CATALOG_ENTRIES = {"Test"}


def get_fixed_star_week(star_name, start_date, stop_date, step_days=1):
    if star_name in EXCLUDED_CATALOG_ENTRIES:
        raise RuntimeError(f"'{star_name}' is a catalog artifact, not a real star")

    start = datetime.strptime(start_date, "%Y-%m-%d")
    stop = datetime.strptime(stop_date, "%Y-%m-%d")
    current = start
    results = []

    while current <= stop:
        jd = swe.julday(current.year, current.month, current.day)
        try:
            res = swe.fixstar2_ut(star_name, jd)
        except Exception as exc:
            raise RuntimeError(f"Fixed star '{star_name}' not found in catalog: {exc}")

        results.append({
            "date": current.strftime("%Y-%m-%d"),
            "longitude_deg": res[0][0],
            "latitude_deg": res[0][1],
        })
        current += timedelta(days=step_days)

    return results
