#!/usr/bin/env python3
"""Derived 6-hour-difference speed layer for the weekly feed + validation.

Engine: ZodiacOracle.LiveTransit.vHybrid.multiSnap6h (short-term persistence
and intraday timing layer). docs/current_week.json is NEVER modified; output
goes to docs/derived/current_week_speed_<week_start>.json (+ a
current_week_speed.json copy).

Rules (2026-10-08 transit-workflow rules):
  * centered difference  speed(t) = wrap180(L[t+6h] - L[t-6h]) / 0.5 day
  * one-sided at the first/last snapshot: wrap180(L[t+6h]-L[t]) / 0.25 day
  * every derived speed carries speed_source = "weekly_6h_difference"
  * fallback only: never overrides a newer valid daily longitude_speed/position
  * no minute-level precision is claimed from 6 h samples
  * fixed stars: motion 'fixed' — never station events; this layer emits NO
    station events at all (true stations come from the six-month series)
Validation over all bodies: every expected snapshot (00/06/12/18 UTC) exists;
no 0/360 wrap discontinuity; derived direction matches daily direct/
retrograde where the daily speed exists (optional --daily); Moon interpolates
cleanly; slow bodies move consistently.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
FEED = ROOT / "docs" / "current_week.json"
OUT_DIR = ROOT / "docs" / "derived"
ENGINE = "ZodiacOracle.LiveTransit.vHybrid.multiSnap6h.derived"
SPEED_SOURCE = "weekly_6h_difference"
HOURS = (0, 6, 12, 18)
STEP_DAYS = 0.25
SLOW_MAX_DEG_PER_DAY = 0.25          # documented: "slow" body for consistency check
SLOW_MAX_SECOND_DIFF_DEG = 0.01      # documented: max |2nd difference| per 6 h for slow bodies (True_Node wobble / Venus near station reach ~0.0025)
MOON_MAX_INTERP_ERR_DEG = 0.05       # documented: midpoint-vs-neighbour interpolation tolerance
FORMULA_POINTS = {"Aetheric_SunMoon_Midpoint", "Aetheric_Jovian_Arc", "Aetheric_Elemental_Balance"}
NODES = {"True_Node", "Mean_Node", "South_Node"}


def wrap180(x: float) -> float:
    return ((x + 180.0) % 360.0 + 360.0) % 360.0 - 180.0


def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def expected_slots(week_start: str, week_end: str) -> List[str]:
    d0 = datetime.strptime(week_start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    d1 = datetime.strptime(week_end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    out = []
    d = d0
    while d <= d1:
        for h in HOURS:
            out.append(iso(d + timedelta(hours=h)))
        d += timedelta(days=1)
    return out


def load_json(src: str) -> Dict[str, Any]:
    if src.startswith("http"):
        with urllib.request.urlopen(src, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))
    return json.loads(Path(src).read_text(encoding="utf-8"))


def body_kind(name: str, fixed_star_names: set) -> str:
    if name in fixed_star_names:
        return "fixed_star"
    if name in FORMULA_POINTS:
        return "aether_point"
    if name in NODES:
        return "lunar_node"
    return "moving_body"


def interpolate(snaps: Dict[str, float], t: datetime) -> Optional[Dict[str, Any]]:
    keys = sorted(snaps)
    times = [parse(k) for k in keys]
    for i in range(len(times) - 1):
        if times[i] <= t <= times[i + 1]:
            fr = (t - times[i]).total_seconds() / (times[i + 1] - times[i]).total_seconds()
            a, b = snaps[keys[i]], snaps[keys[i + 1]]
            return {"value": (a + wrap180(b - a) * fr) % 360.0, "bracket": [keys[i], keys[i + 1]], "fraction": fr}
    return None


def derive(feed: Dict[str, Any], daily: Optional[Dict[str, Any]] = None, source_label: str = "docs/current_week.json") -> Dict[str, Any]:
    slots = expected_slots(feed["week_start"], feed["week_end"])
    bodies = feed["bodies"]
    star_names = set()
    if daily:
        star_names = {n for n, v in daily.get("transit_positions", {}).items() if v.get("category") == "fixed_stars"}
    if not star_names:  # fall back to repo fixed-star list
        fs = json.loads((ROOT / "data" / "fixed_stars.json").read_text(encoding="utf-8"))
        star_names = set(fs.keys()) if isinstance(fs, dict) else {s.get("name") for s in fs if isinstance(s, dict)}
    out_bodies: Dict[str, Any] = {}
    missing_slots, wrap_disc, slow_bad, unexpected_jumps = {}, [], [], []
    slow_stats: List[Any] = []
    for name, b in bodies.items():
        snaps = b.get("snapshots") or {}
        miss = [s for s in slots if s not in snaps or not isinstance(snaps.get(s), (int, float))]
        if miss:
            missing_slots[name] = miss
        L = [snaps.get(s) for s in slots]
        kind = body_kind(name, star_names)
        n = len(L)
        speeds: List[Optional[float]] = [None] * n
        methods: List[str] = ["unresolved"] * n
        for i in range(n):
            if 0 < i < n - 1 and L[i - 1] is not None and L[i + 1] is not None:
                speeds[i] = wrap180(L[i + 1] - L[i - 1]) / (2 * STEP_DAYS); methods[i] = "centered"
            elif i == 0 and L[0] is not None and n > 1 and L[1] is not None:
                speeds[i] = wrap180(L[1] - L[0]) / STEP_DAYS; methods[i] = "forward_one_sided"
            elif i == n - 1 and L[i] is not None and L[i - 1] is not None:
                speeds[i] = wrap180(L[i] - L[i - 1]) / STEP_DAYS; methods[i] = "backward_one_sided"
        steps = [wrap180(L[i + 1] - L[i]) for i in range(n - 1) if L[i] is not None and L[i + 1] is not None]
        raw_steps = [abs(L[i + 1] - L[i]) for i in range(n - 1) if L[i] is not None and L[i + 1] is not None]
        crosses_wrap = any(r > 180 for r in raw_steps)
        # discontinuity = a wrapped 6 h step that is not consistent with neighbours (> 5x median |step| and > 2 deg)
        med = sorted(abs(s) for s in steps)[len(steps) // 2] if steps else 0.0
        jumps = [i for i, s in enumerate(steps) if abs(s) > max(2.0, 5 * med)]
        if jumps:
            (unexpected_jumps if kind == "aether_point" else wrap_disc).append({"body": name, "kind": kind, "step_indices": jumps,
                                                                               "max_step_deg": max(abs(steps[i]) for i in jumps)})
        mean_speed = (sum(steps) / (len(steps) * STEP_DAYS)) if steps else None
        if kind in ("moving_body", "lunar_node") and mean_speed is not None and abs(mean_speed) <= SLOW_MAX_DEG_PER_DAY:
            sd = [abs(wrap180(steps[i + 1] - steps[i])) for i in range(len(steps) - 1)]
            if sd:
                slow_stats.append((max(sd), name))
            if sd and max(sd) > SLOW_MAX_SECOND_DIFF_DEG:
                slow_bad.append({"body": name, "max_second_difference_deg": max(sd)})
        if kind == "fixed_star":
            motion = ["fixed"] * n
        else:
            motion = [None if s is None else ("retrograde" if s < 0 else "direct") for s in speeds]
        out_bodies[name] = {
            "kind": kind,
            "speed_source": SPEED_SOURCE,
            "speed_deg_per_day": speeds,
            "speed_method": methods,
            "motion": motion,
            "station_events": [],
            "crosses_0_360": crosses_wrap,
            "mean_speed_deg_per_day": mean_speed,
        }
    # Daily cross-check (direction + interpolated position) at the daily instant
    daily_check = None
    if daily:
        t = parse(daily["generated_at_utc"])
        rows, mism, unresolved_fallback = {}, [], []
        for name, v in daily.get("transit_positions", {}).items():
            if name not in bodies:
                continue
            ip = interpolate(bodies[name]["snapshots"], t)
            if ip is None:
                continue
            # derived speed at daily instant: centered difference around the bracket
            snaps = bodies[name]["snapshots"]
            k0, k1 = ip["bracket"]
            wspeed = wrap180(snaps[k1] - snaps[k0]) / STEP_DAYS
            dspeed = v.get("longitude_speed")
            kind = out_bodies[name]["kind"]
            row = {"weekly_interpolated_lon": ip["value"], "daily_lon": v.get("longitude"),
                   "lon_diff_deg": abs(wrap180(ip["value"] - v["longitude"])) if v.get("longitude") is not None else None,
                   "weekly_6h_speed": wspeed, "daily_longitude_speed": dspeed, "kind": kind}
            if dspeed is not None and kind in ("moving_body", "lunar_node") and abs(dspeed) > 0.002:
                row["direction_match"] = (wspeed < 0) == (dspeed < 0)
                if not row["direction_match"]:
                    mism.append(name)
            elif dspeed is None and kind == "moving_body":
                row["fallback_speed"] = {"value": wspeed, "speed_source": SPEED_SOURCE,
                                         "authority": "fallback only; daily longitude_speed is null (stays null in daily feed)"}
                unresolved_fallback.append(name)
            rows[name] = row
        daily_check = {"daily_generated_at_utc": daily["generated_at_utc"], "direction_mismatches": mism,
                       "bodies_compared_direction": sum(1 for r in rows.values() if "direction_match" in r),
                       "fallback_speed_available_for_daily_null": unresolved_fallback, "rows": rows}
    # Moon interpolation check: each interior snapshot vs quadratic of neighbours
    moon = [(bodies.get("Moon") or {}).get("snapshots", {}).get(s) for s in slots]
    moon_err = 0.0
    for i in range(1, len(moon) - 1):
        if moon[i - 1] is None or moon[i] is None or moon[i + 1] is None:
            continue
        lin = moon[i - 1] + wrap180(moon[i + 1] - moon[i - 1]) / 2
        moon_err = max(moon_err, abs(wrap180(lin - moon[i])))
    checks = []

    def check(name, ok, detail):
        checks.append({"check": name, "result": "PASS" if ok else "FAIL", "detail": detail})

    check("all_expected_snapshots_present", not missing_slots,
          {"bodies": len(bodies), "expected_per_body": len(slots), "missing": {k: v[:3] for k, v in missing_slots.items()}})
    check("snapshot_hours_00_06_12_18_utc", feed.get("snapshot_schedule_utc", {}).get("hours") == list(HOURS),
          feed.get("snapshot_schedule_utc"))
    check("no_0_360_wrap_discontinuities_physical_bodies", not wrap_disc,
          {"bodies_crossing_0_360": sorted(n for n, b in out_bodies.items() if b["crosses_0_360"]), "violations": wrap_disc})
    if daily_check is not None and daily_check["bodies_compared_direction"] > 0:
        check("derived_direction_matches_daily_where_daily_speed_exists", not daily_check["direction_mismatches"],
              {"compared": daily_check["bodies_compared_direction"], "mismatches": daily_check["direction_mismatches"],
               "daily_generated_at_utc": daily_check["daily_generated_at_utc"]})
    else:
        checks.append({"check": "derived_direction_matches_daily_where_daily_speed_exists", "result": "SKIPPED",
                       "detail": "no daily feed supplied or daily instant outside the weekly snapshot range"})
    check("moon_interpolates_cleanly", moon_err <= MOON_MAX_INTERP_ERR_DEG,
          {"max_midpoint_linear_error_deg": moon_err, "tolerance_deg": MOON_MAX_INTERP_ERR_DEG,
           "note": "6 h linear interpolation error for the Moon; timing claims limited to ~hour precision"})
    check("slow_bodies_consistent_motion", not slow_bad,
          {"slow_threshold_deg_per_day": SLOW_MAX_DEG_PER_DAY, "max_second_difference_deg": SLOW_MAX_SECOND_DIFF_DEG,
           "slow_bodies_checked": len(slow_stats),
           "largest": [{"body": nm, "max_second_difference_deg": v} for v, nm in sorted(slow_stats, reverse=True)[:5]],
           "violations": slow_bad})
    check("no_station_events_emitted", all(not b["station_events"] for b in out_bodies.values()),
          {"fixed_stars": sum(1 for b in out_bodies.values() if b["kind"] == "fixed_star")})
    return {
        "engine_version": ENGINE,
        "layer": "derived (separate from raw snapshots; current_week.json untouched)",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_feed": source_label,
        "source_generated_utc": feed.get("generated_utc"),
        "week_start": feed["week_start"], "week_end": feed["week_end"],
        "snapshot_timestamps_utc": slots,
        "speed_provenance": {
            "speed_source": SPEED_SOURCE,
            "formula": "wrap180(L[t+6h] - L[t-6h]) / 0.5 day (centered); one-sided wrap180(L[t+6h]-L[t]) / 0.25 day at first/last snapshot",
            "precision": "6 h sampling: no minute-level precision; timing statements to about the hour",
            "authority": "fallback for short-term motion when daily longitude_speed is null; never overrides a newer valid daily position or speed",
        },
        "use_for": ["Moon timing", "short-lived triggers", "daily signal building or fading", "nearby turning points (confirm with six-month station series)"],
        "station_rule": "this layer emits no station events; fixed stars are motion 'fixed'",
        "documented_parameters": {"slow_max_deg_per_day": SLOW_MAX_DEG_PER_DAY, "slow_max_second_difference_deg": SLOW_MAX_SECOND_DIFF_DEG,
                                  "moon_max_interp_err_deg": MOON_MAX_INTERP_ERR_DEG,
                                  "discontinuity_rule": "6 h step > max(2 deg, 5x body median step)"},
        "formula_point_discontinuities": unexpected_jumps,
        "formula_point_note": "Aether points are formula outputs (SunMoon = Sun+Moon sum, a known defect; Elemental_Balance = non-circular mean); jumps here are formula artifacts, not wrap-handling errors",
        "daily_crosscheck": daily_check,
        "all_passed": all(c["result"] != "FAIL" for c in checks),
        "checks": checks,
        "bodies": out_bodies,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--feed", default=str(FEED))
    ap.add_argument("--daily", help="daily feed path or URL for direction cross-check")
    a = ap.parse_args()
    feed = load_json(a.feed)
    daily = None
    if a.daily:
        try:
            daily = load_json(a.daily)
        except Exception as exc:
            print(f"[WARN] daily feed unavailable ({exc}); direction cross-check skipped")
    label = a.feed if a.feed.startswith("http") else str(Path(a.feed).resolve().relative_to(ROOT))
    out = derive(feed, daily, label)
    if daily:
        out["daily_source"] = a.daily
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    text = json.dumps(out, indent=1) + "\n"
    (OUT_DIR / f"current_week_speed_{feed['week_start']}.json").write_text(text, encoding="utf-8")
    (OUT_DIR / "current_week_speed.json").write_text(text, encoding="utf-8")
    for c in out["checks"]:
        print(f"[{c['result']}] {c['check']}")
    return 0 if out["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
