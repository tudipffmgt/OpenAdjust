"""
Slope distance observation model.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING
import numpy as np

from openadjust.core.observation import Observation

if TYPE_CHECKING:
    from openadjust.core.network import Network


@dataclass
class DistanceObservation(Observation):
    """
    Slope distance observation (3D distance).
    
    The functional model is:
        s_ij = sqrt((Xj-Xi)² + (Yj-Yi)² + (Zj-Zi)²) * (1 + m)

    where m is the optional scale parameter.

    For the design matrix:
        ∂s/∂Xi = -ΔX / s
        ∂s/∂Yi = -ΔY / s
        ∂s/∂Zi = -ΔZ / s
        ∂s/∂Xj = ΔX / s
        ∂s/∂Yj = ΔY / s
        ∂s/∂Zj = ΔZ / s
        ∂s/∂m = s (scale parameter, if included)

    Note: For total station measurements, instrument and target heights
    should be considered if not reduced to ground marks.

    Attributes:
        instrument_height: Height of instrument above station point
        target_height: Height of target/prism above target point
    """

    instrument_height: float = 0.0
    target_height: float = 0.0

    def compute_l0(self, network: 'Network') -> float:
        """Computes approximate slope distance from coordinates."""
        sta = network.get_point(self.station)
        tgt = network.get_point(self.target)

        dx = tgt.x - sta.x
        dy = tgt.y - sta.y
        dz = (tgt.z + self.target_height) - (sta.z + self.instrument_height)

        return np.sqrt(dx**2 + dy**2 + dz**2)

    def compute_A_row(self, network: 'Network', param_index: dict[str, int]) -> np.ndarray:
        """
        Computes partial derivatives of slope distance observation.

        ∂s/∂Xi = -ΔX / s
        ∂s/∂Yi = -ΔY / s
        ∂s/∂Zi = -ΔZ / s
        ∂s/∂Xj = ΔX / s
        ∂s/∂Yj = ΔY / s
        ∂s/∂Zj = ΔZ / s
        ∂s/∂m = s (scale parameter)
        """
        sta = network.get_point(self.station)
        tgt = network.get_point(self.target)

        dx = tgt.x - sta.x
        dy = tgt.y - sta.y
        dz = (tgt.z + self.target_height) - (sta.z + self.instrument_height)

        s = np.sqrt(dx**2 + dy**2 + dz**2)

        if s < 1e-10:
            return np.zeros(len(param_index))

        n_params = len(param_index)
        A_row = np.zeros(n_params)

        # Partial derivatives w.r.t. station coordinates
        if f"{self.station}_x" in param_index:
            A_row[param_index[f"{self.station}_x"]] = -dx / s
        if f"{self.station}_y" in param_index:
            A_row[param_index[f"{self.station}_y"]] = -dy / s
        if f"{self.station}_z" in param_index:
            A_row[param_index[f"{self.station}_z"]] = -dz / s

        # Partial derivatives w.r.t. target coordinates
        if f"{self.target}_x" in param_index:
            A_row[param_index[f"{self.target}_x"]] = dx / s
        if f"{self.target}_y" in param_index:
            A_row[param_index[f"{self.target}_y"]] = dy / s
        if f"{self.target}_z" in param_index:
            A_row[param_index[f"{self.target}_z"]] = dz / s

        # Partial derivative w.r.t. scale parameter (if included)
        # ∂s/∂m = s, but we express m in ppm, so ∂s/∂m = s/1000 [m/ppm]
        if "scale" in param_index:
            A_row[param_index["scale"]] = s / 1000.0  # Scale in ppm
        
        return A_row
    
    def get_observation_type(self) -> str:
        return "distance"
    
    def get_display_value(self, angle_unit: str = "gon") -> str:
        # angle_unit is ignored for distances
        return f"{self.value:.4f} m"
