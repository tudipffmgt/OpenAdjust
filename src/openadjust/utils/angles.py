"""
Angle conversion utilities.
"""

import numpy as np


def gon_to_rad(gon: float) -> float:
    """Converts Gon to Radians."""
    return gon * np.pi / 200.0


def rad_to_gon(rad: float) -> float:
    """Converts Radians to Gon."""
    return rad * 200.0 / np.pi


def deg_to_rad(deg: float) -> float:
    """Converts Degrees to Radians."""
    return deg * np.pi / 180.0


def rad_to_deg(rad: float) -> float:
    """Converts Radians to Degrees."""
    return rad * 180.0 / np.pi


def normalize_angle(angle_rad: float) -> float:
    """Normalizes an angle to [0, 2π)."""
    return angle_rad % (2 * np.pi)


def dms_to_decimal(degrees: int, minutes: int, seconds: float) -> float:
    """Converts Degrees-Minutes-Seconds to Decimal Degrees."""
    sign = -1 if degrees < 0 else 1
    return sign * (abs(degrees) + minutes / 60.0 + seconds / 3600.0)
