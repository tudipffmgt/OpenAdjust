"""
Horizontal direction observation model.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING
import numpy as np

from openadjust.core.observation import Observation

if TYPE_CHECKING:
    from openadjust.core.network import Network


@dataclass
class DirectionObservation(Observation):
    """
    Horizontal direction observation (Hz).
    
    The functional model is:
        r_ij = arctan2(Xj - Xi, Yj - Yi) - o_i
    
    where:
        r_ij = direction from i to j
        Xi, Yi = coordinates of station i
        Xj, Yj = coordinates of target j
        o_i = orientation unknown for station i
    
    Attributes:
        orientation_group: ID for grouping directions with same orientation unknown
    """
    
    orientation_group: str = ""
    
    def __post_init__(self):
        if not self.orientation_group:
            self.orientation_group = self.station
    
    def compute_l0(self, network: 'Network') -> float:
        """Computes approximate direction from coordinates."""
        sta = network.get_point(self.station)
        tgt = network.get_point(self.target)
        
        dx = tgt.x - sta.x
        dy = tgt.y - sta.y
        
        # Bearing angle (arctan2 returns -π to +π)
        bearing = np.arctan2(dx, dy)  # Geodetic convention: arctan(ΔX/ΔY)
        
        if bearing < 0:
            bearing += 2 * np.pi
        
        return bearing
    
    def compute_A_row(self, network: 'Network', param_index: dict[str, int]) -> np.ndarray:
        """
        Computes partial derivatives of direction observation.
        
        ∂r/∂Xi = ΔY / s²
        ∂r/∂Yi = -ΔX / s²
        ∂r/∂Xj = -ΔY / s²
        ∂r/∂Yj = ΔX / s²
        ∂r/∂o = -1
        """
        sta = network.get_point(self.station)
        tgt = network.get_point(self.target)
        
        dx = tgt.x - sta.x
        dy = tgt.y - sta.y
        s_horiz_sq = dx**2 + dy**2
        
        n_params = len(param_index)
        A_row = np.zeros(n_params)
        
        # Partial derivatives w.r.t. station coordinates
        if f"{self.station}_x" in param_index:
            A_row[param_index[f"{self.station}_x"]] = dy / s_horiz_sq
        if f"{self.station}_y" in param_index:
            A_row[param_index[f"{self.station}_y"]] = -dx / s_horiz_sq
        
        # Partial derivatives w.r.t. target coordinates
        if f"{self.target}_x" in param_index:
            A_row[param_index[f"{self.target}_x"]] = -dy / s_horiz_sq
        if f"{self.target}_y" in param_index:
            A_row[param_index[f"{self.target}_y"]] = dx / s_horiz_sq
        
        # Partial derivative w.r.t. orientation unknown
        orient_key = f"orientation_{self.orientation_group}"
        if orient_key in param_index:
            A_row[param_index[orient_key]] = -1.0
        
        return A_row
    
    def get_observation_type(self) -> str:
        return "direction"
    
    def get_display_value(self, angle_unit: str = "gon") -> str:
        if angle_unit == "gon":
            value_gon = self.value * 200.0 / np.pi
            return f"{value_gon:.5f} gon"
        else:
            value_deg = self.value * 180.0 / np.pi
            return f"{value_deg:.5f}°"
