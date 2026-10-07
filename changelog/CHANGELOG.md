# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-02-19
- Project scaffold: initial directory structure, JSON schema, and feed stubs.

## [0.2.0] - 2026-10-06
- Expand body catalog (asteroids, centaurs, TNOs, nodes, fixed stars, 3 Aether formulas).
- Add 4× daily UTC snapshots (00/06/12/18) in `bodies[*].snapshots` while keeping
  Android-compatible `bodies[*].data` date keys.
- Switch house policy to Placidus on-device; omit personal houses from universal feed.
- Stop emitting Arabic Parts with ASC=Sun; mark unavailable without natal ASC.
- Aether engine: three verified formulas only (no stubs).
- JPL Horizons center set to geocentric Earth (`500@399`).
