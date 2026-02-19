ZODIAC ORACLE — LIVE TRANSITS ENGINE

Version: ephemeris-v1.0
Updated automatically via GitHub Actions

The Zodiac Oracle Live Transits Engine generates astronomy-accurate planetary, asteroid, TNO, and fixed-star ephemeris feeds for consumption by the Zodiac Oracle mobile app and any external services requiring precise daily and weekly transit data.

This repository produces four public JSON feeds:

feed_now.json — real-time snapshot

feed_daily.json — next 7 days

current_week.json — structured week block (Sunday → Saturday)

_meta.json — metadata, versioning, and generation timestamp

All feeds are automatically regenerated weekly and made accessible via GitHub’s raw CDN endpoints.

Ephemeris Sources

Data is resolved through a cascading multi-engine pipeline:

NASA JPL Horizons — primary

IMCCE Miriade — secondary (covers objects Horizons cannot resolve, including many TNOs)

Swiss-style fallback — sparse emergency resolver

This ensures maximal coverage across:

Planets

Moon

Dwarf planets

Centaurs

Asteroids

TNOs

Deep objects

Major fixed stars

Each body includes:

Ecliptic longitude

Latitude

Retrograde flag

Velocity estimate

Zodiac sign

Degree within sign

Whole-sign house

Harmonic signature

Fixed Stars

The feed also includes the dominant stars used by the Zodiac Oracle system:

Regulus

Spica

Aldebaran

Antares

Algol

Arcturus

Betelgeuse

Canopus

Capella

Deneb

Fomalhaut

Pollux

Procyon

Rigel

Sirius

Vega

Zubenelgenubi

Zubeneschamali

These are resolved as static longitudes with house assignment applied at generation time.

Houses & Location

House system: Whole Sign
Observer reference: Greenwich Observatory

Latitude: 51.4769°
Longitude: 0.0000°


This provides a globally neutral baseline for apps using universal, location-independent broadcasts.

Aspect Engine

The system automatically computes aspects between all bodies and fixed stars:

0° conjunction

60° sextile

90° square

120° trine

180° opposition

Each entry includes:

type

orb

exact angle

actual angle

These are consumed by downstream applications for interpretive overlays.

JSON Feed Structure

Example structure:

{
  "version": "ephemeris-v1.0",
  "week_start": "2026-02-22T00:00:00Z",
  "days": [
    {
      "timestamp": "2026-02-22T00:00:00Z",
      "transits": {
        "positions": {
          "Sun": {
            "lon": 5.0,
            "lat": 0.0,
            "retrograde": false,
            "speed": 0.0,
            "sign": "Aries",
            "deg": 5.0,
            "house": 5,
            "harmonics": 5.0
          }
        },
        "aspects": {
          "Sun-Saturn": {
            "type": "trine",
            "orb": 3.0,
            "exact": 120,
            "angle": 117.0
          }
        }
      }
    }
  ]
}

Feed Locations

All feeds are written to:

/docs/feed_now.json
/docs/feed_daily.json
/docs/current_week.json
/docs/_meta.json


These files are intended for direct pull via the GitHub CDN, for example:

https://raw.githubusercontent.com/<USERNAME>/<REPO>/main/docs/current_week.json


Replace <USERNAME> and <REPO> with your repository details.

Automation (GitHub Actions)

The workflow executes automatically:

Every Sunday @ 00:00 UTC

On manual dispatch

On push to main

This guarantees the app always receives:

Fresh weekly transits

Up-to-date aspect grids

Accurate planetary + fixed star positions

Intended Use

This repository exists to supply deterministic, astronomy-accurate transit data for the Zodiac Oracle ecosystem and any compatible downstream engines.

Not licensed for redistribution or repackaging.
