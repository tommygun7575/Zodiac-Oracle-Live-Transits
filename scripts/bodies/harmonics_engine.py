# Harmonics Calculation Engine
"""
Harmonic chart utilities.
Provides basic harmonic longitude calculations for astrological processing.
"""

def harmonics(ecl_lon_deg, harmonic_number=1):
    """
    Compute harmonic longitude for any harmonic N.
    Harmonic longitude = (ecl_lon * N) % 360

    Parameters:
        ecl_lon_deg (float): Ecliptic longitude (0–360)
        harmonic_number (int): Harmonic multiplier (default=1)

    Returns:
        float: Harmonic longitude in degrees (0–360)
    """

    if ecl_lon_deg is None:
        return None

    try:
        return float((ecl_lon_deg * harmonic_number) % 360)
    except Exception:
        return None

# TODO: Implement calculation of harmonics (1-24).
