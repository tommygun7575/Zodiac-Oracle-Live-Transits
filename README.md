# Zodiac Oracle Live Transits

Live ephemeris and real-time planetary feeds for symbolic and astronomical planetary layers.

## Features
- Multiple engines: Swiss, MPC, Miriade, Aether
- Real-time UTC and weekly ephemeris feeds
- JSON-schema validation (see `transit-schema.json`)
- Modular, engine-agnostic architecture

## Getting Started

1. See `/schema/transit-schema.json` for the feed structure.
2. Dummy feeds:
    - Current: `docs/feed_now.json`
    - Weekly: `docs/feed_weekly.json`
3. Utilities under `scripts/utils/`. Engines under `scripts/bodies/`.

MIT License
