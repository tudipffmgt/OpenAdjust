"""
Zenith angle observation model.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING
import numpy as np

from openadjust.core.observation import Observation

if TYPE_CHECKING:
    from openadjust.core.network import Network


@dataclass
class ZenithObservation(Observation):
    """
    Zenith angle observation (V).
    
    The functional model is:
        z_ij = arctan2(s_horiz, ΔH) = arccos(ΔH / s_3D)
    
    where:
        z_ij = zenith angle from i to j
        s_horiz = horizontal distance
        ΔH = Zj - Zi - ih + th (height difference considering instrument/target heights)
        ih = instrument height
        th = target height
    
    Attributes:
        instrument_height: Height of instrument above station point
        target_height: Height of target/prism above target point
    """
    
    instrument_height: float = 0.0
    target_height: float = 0.0
    
    def compute_l0(self, network: 'Network') -> float:
        """Computes approximate zenith angle from coordinates."""
        sta = network.get_point(self.station)
        tgt = network.get_point(self.target)
        
        dx = tgt.x - sta.x
        dy = tgt.y - sta.y
        dz = (tgt.z + self.target_height) - (sta.z + self.instrument_height)
        
        s_horiz = np.sqrt(dx**2 + dy**2)
        
        # Zenith angle
        zenith = np.arctan2(s_horiz, dz)
        
        return zenith
    
    def compute_A_row(self, network: 'Network', param_index: dict[str, int]) -> np.ndarray:
        """
        Computes partial derivatives of zenith angle observation.
        """
        sta = network.get_point(self.station)
        tgt = network.get_point(self.target)
        
        dx = tgt.x - sta.x
        dy = tgt.y - sta.y
        dz = (tgt.z + self.target_height) - (sta.z + self.instrument_height)
        
        s_horiz_sq = dx**2 + dy**2
        s_horiz = np.sqrt(s_horiz_sq)
        s_3d_sq = s_horiz_sq + dz**2
        
        n_params = len(param_index)
        A_row = np.zeros(n_params)
        
        # Common factor
        factor_xy = dz / (s_3d_sq * s_horiz) if s_horiz > 1e-10 else 0.0
        factor_z = -s_horiz / s_3d_sq
        
        # Partial derivatives w.r.t. station coordinates
        if f"{self.station}_x" in param_index:
            A_row[param_index[f"{self.station}_x"]] = -factor_xy * dx
        if f"{self.station}_y" in param_index:
            A_row[param_index[f"{self.station}_y"]] = -factor_xy * dy
        if f"{self.station}_z" in param_index:
            A_row[param_index[f"{self.station}_z"]] = -factor_z
        
        # Partial derivatives w.r.t. target coordinates
        if f"{self.target}_x" in param_index:
            A_row[param_index[f"{self.target}_x"]] = factor_xy * dx
        if f"{self.target}_y" in param_index:
            A_row[param_index[f"{self.target}_y"]] = factor_xy * dy
        if f"{self.target}_z" in param_index:
            A_row[param_index[f"{self.target}_z"]] = factor_z
        
        return A_row
    
    def get_observation_type(self) -> str:
        return "zenith"
    
    def get_display_value(self, angle_unit: str = "gon") -> str:
        if angle_unit == "gon":
            value_gon = self.value * 200.0 / np.pi
            return f"{value_gon:.5f} gon"
        else:
            value_deg = self.value * 180.0 / np.pi
            return f"{value_deg:.5f}°"
