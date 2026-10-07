"""Verified Aether formulas for the Zodiac Oracle universal feed.

Exactly three formulas (borrowed from Black-Zodiac celestial_math).
Missing inputs yield None — never fabricated coordinates.
"""
from __future__ import annotations

from typing import Dict, Optional


def normalize(x: float) -> float:
    return ((float(x) % 360.0) + 360.0) % 360.0


VERIFIED_AETHER = (
    "Aetheric_SunMoon_Midpoint",
    "Aetheric_Jovian_Arc",
    "Aetheric_Elemental_Balance",
)


def compute_aether_longitudes(
    sun: Optional[float],
    moon: Optional[float],
    venus: Optional[float],
    mars: Optional[float],
    jupiter: Optional[float],
    saturn: Optional[float],
) -> Dict[str, Optional[float]]:
    """Exactly the three verified Oracle Aether formulas."""
    return {
        "Aetheric_SunMoon_Midpoint": (
            None if sun is None or moon is None else normalize(sun + moon)
        ),
        "Aetheric_Jovian_Arc": (
            None
            if jupiter is None or saturn is None
            else normalize(jupiter - saturn)
        ),
        "Aetheric_Elemental_Balance": (
            None
            if moon is None or venus is None or mars is None
            else normalize((moon + venus + mars) / 3.0)
        ),
    }


def compute_aether_from_positions(positions: Dict[str, float]) -> Dict[str, Optional[float]]:
    """Convenience wrapper taking a name→longitude map."""
    return compute_aether_longitudes(
        positions.get("Sun"),
        positions.get("Moon"),
        positions.get("Venus"),
        positions.get("Mars"),
        positions.get("Jupiter"),
        positions.get("Saturn"),
    )
