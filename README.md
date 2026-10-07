# ZODIAC ORACLE — LIVE TRANSITS ENGINE

Version: ephemeris-v1.0 (multi-snapshot 6h UTC)
Updated automatically via GitHub Actions

Generates astronomy-accurate planetary, asteroid, TNO, fixed-star, and Aether
ephemeris for the Zodiac Oracle Android app and compatible clients.

## Android feed contract (do not break)

**Primary URL:**
`https://raw.githubusercontent.com/tommygun7575/Zodiac-Oracle-Live-Transits/main/docs/current_week.json`

Also archived as `docs/current_week_YYYY-MM-DD.json` (week_start date).

### Required shape (legacy + current)

```json
{
  "generated_utc": "...",
  "week_start": "YYYY-MM-DD",
  "week_end": "YYYY-MM-DD",
  "engine_version": "ZodiacOracle.LiveTransit.vHybrid.multiSnap6h",
  "coverage": 1.0,
  "resolved": 0,
  "total_targets": 0,
  "missing": [],
  "bodies": {
    "Sun": {
      "source": "JPL|Miriade|Swiss|calculated",
      "data": { "YYYY-MM-DD": 191.28 },
      "snapshots": { "YYYY-MM-DDTHH:MM:SSZ": 191.28 }
    }
  },
  "arabic_parts": { "status": "unavailable", "reason": "..." },
  "fixed_star_conjunctions": {
    "YYYY-MM-DD": [ { "body": "Sun", "star": "Auva", "orb": 0.5 } ]
  }
}
```

- **`bodies[*].data`**: daily `YYYY-MM-DD` → longitude (00:00 UTC slot).  
  Existing Android `TransitParser` continues to select **today** or **max date**.
- **`bodies[*].snapshots`** *(additive)*: 4 UTC slots/day × 7 days  
  (`00:00`, `06:00`, `12:00`, `18:00` UTC). Clients may pick the nearest ISO key to now.
- **`arabic_parts`**: not fabricated with ASC=Sun on this universal feed; compute on-device with Placidus ASC.
- **Houses**: not emitted per body. System for on-device use is **Placidus** (`houses` metadata).

## Providers (order preserved)

1. NASA JPL Horizons (geocentric)
2. IMCCE Miriade
3. Swiss Ephemeris fallback

No fabricated coordinates. Unresolved bodies appear in `missing`.

## Bodies

Planets, lunar nodes, dwarfs, centaurs, asteroids, TNOs, major fixed stars, and
exactly three verified Aether formulas:

- `Aetheric_SunMoon_Midpoint` = normalize(Sun + Moon)
- `Aetheric_Jovian_Arc` = normalize(Jupiter − Saturn)
- `Aetheric_Elemental_Balance` = normalize((Moon + Venus + Mars) / 3)

Catalog IDs aligned with Black-Zodiac-Live-Transits where helpful.

## Automation

GitHub Actions: Sunday 04:00 UTC + workflow_dispatch → regenerates
`docs/current_week.json` and dated archive, then commits.

## Local run

```bash
python -m venv .venv && .venv/bin/pip install numpy requests pyswisseph python-dateutil
# Provide Swiss ephemeris files under ./ephe (or symlink)
PYTHONPATH=. .venv/bin/python -m scripts.generate_transits
PYTHONPATH=. .venv/bin/python -m pytest tests/ -q
```
