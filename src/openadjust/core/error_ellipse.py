"""
Error ellipse calculation from cofactor matrix Qxx.

Based on Navratil, Ausgleichungsrechnung II, Kapitel 4.4
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from openadjust.core.adjustment import AdjustmentResult


@dataclass
class ErrorEllipse:
    """
    Represents an error ellipse for a 2D point.

    Attributes:
        A: Semi-major axis [same unit as coordinates, typically m]
        B: Semi-minor axis [same unit as coordinates]
        phi: Orientation of major axis [radians, from X-axis counter-clockwise]
        sx: Standard deviation in X direction
        sy: Standard deviation in Y direction
        sH: Helmert point position error (sqrt(sx² + sy²))
    """
    A: float  # Semi-major axis
    B: float  # Semi-minor axis
    phi: float  # Orientation in radians (from X-axis, counter-clockwise)
    sx: float  # Standard deviation X
    sy: float  # Standard deviation Y
    sH: float  # Helmert point error

    @property
    def phi_gon(self) -> float:
        """Orientation in gon."""
        return self.phi * 200.0 / np.pi

    @property
    def phi_deg(self) -> float:
        """Orientation in degrees."""
        return self.phi * 180.0 / np.pi

    @property
    def A_mm(self) -> float:
        """Semi-major axis in mm."""
        return self.A * 1000

    @property
    def B_mm(self) -> float:
        """Semi-minor axis in mm."""
        return self.B * 1000


def compute_error_ellipse(qxx: float, qyy: float, qxy: float,
                          sigma_0: float = 1.0) -> ErrorEllipse:
    """
    Computes an error ellipse from cofactor matrix elements.

    The 2x2 cofactor submatrix for a point is:
        Q = [[qxx, qxy],
             [qxy, qyy]]

    Args:
        qxx: Variance cofactor for X coordinate
        qyy: Variance cofactor for Y coordinate
        qxy: Covariance cofactor between X and Y
        sigma_0: A posteriori standard deviation of unit weight

    Returns:
        ErrorEllipse with computed parameters
    """
    # Build 2x2 cofactor matrix
    Q = np.array([[qxx, qxy],
                  [qxy, qyy]])

    # Eigenvalue decomposition
    eigenvalues, eigenvectors = np.linalg.eigh(Q)

    # Sort by eigenvalue (largest first = major axis)
    sort_idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[sort_idx]
    eigenvectors = eigenvectors[:, sort_idx]

    # Semi-axes (scaled by sigma_0)
    A = sigma_0 * np.sqrt(max(eigenvalues[0], 0))
    B = sigma_0 * np.sqrt(max(eigenvalues[1], 0))

    # Orientation: angle of major axis eigenvector from X-axis
    ev = eigenvectors[:, 0]
    phi = np.arctan2(ev[1], ev[0])

    # Normalize to [0, π)
    if phi < 0:
        phi += np.pi
    if phi >= np.pi:
        phi -= np.pi

    # Standard deviations
    sx = sigma_0 * np.sqrt(max(qxx, 0))
    sy = sigma_0 * np.sqrt(max(qyy, 0))
    sH = np.sqrt(sx ** 2 + sy ** 2)

    return ErrorEllipse(A=A, B=B, phi=phi, sx=sx, sy=sy, sH=sH)


def compute_all_error_ellipses(result: 'AdjustmentResult') -> dict[str, ErrorEllipse]:
    """
    Computes error ellipses for all points with unknown coordinates.

    Note: Uses sigma_0 = 1.0 if sigma_0 is 0 or very small (a-priori case
    or perfect observations). This ensures ellipses are always visible.
    """
    if result.Qxx is None or not result.param_index:
        return {}

    # Für Visualisierung: σ₀ = 1 wenn σ₀ ≈ 0 (a-priori oder perfekte Beobachtungen)
    sigma_0 = result.sigma_0 if result.sigma_0 > 0.001 else 1.0

    ellipses = {}

    # Find all unique point IDs
    point_ids = set()
    for param_name in result.param_index.keys():
        if param_name == "scale":
            continue
        parts = param_name.rsplit('_', 1)
        if len(parts) == 2:
            point_ids.add(parts[0])

    # Compute ellipse for each point
    for point_id in point_ids:
        x_key = f"{point_id}_x"
        y_key = f"{point_id}_y"

        # Check if both X and Y are unknown
        if x_key not in result.param_index or y_key not in result.param_index:
            continue

        idx_x = result.param_index[x_key]
        idx_y = result.param_index[y_key]

        qxx = result.Qxx[idx_x, idx_x]
        qyy = result.Qxx[idx_y, idx_y]
        qxy = result.Qxx[idx_x, idx_y]

        ellipse = compute_error_ellipse(qxx, qyy, qxy, sigma_0)
        ellipses[point_id] = ellipse

    return ellipses
