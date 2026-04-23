"""
Levelling (height difference) observation model.

Reference: Neitzel (2024), "Zur Ausgleichung angeschlossener Höhennetze"
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING
import numpy as np

from openadjust.core.observation import Observation

if TYPE_CHECKING:
    from openadjust.core.network import Network


@dataclass
class LevellingObservation(Observation):
    """
    Height difference observation (Nivellement).

    The functional model is:
        Δh_ij = H_j - H_i

    where:
        Δh_ij = measured height difference from i to j
        H_i = height of station point i
        H_j = height of target point j

    This is a LINEAR observation equation - no iteration required!

    For the design matrix:
        ∂Δh/∂H_i = -1
        ∂Δh/∂H_j = +1

    Note: If station or target is a fixed point (known height),
    the known height acts as a constant in the functional model.
    """

    def compute_l0(self, network: 'Network') -> float:
        """
        Computes the height difference from current coordinates.

        Δh = H_target - H_station
        """
        sta = network.get_point(self.station)
        tgt = network.get_point(self.target)

        return tgt.z - sta.z

    def compute_A_row(self, network: 'Network', param_index: dict[str, int]) -> np.ndarray:
        """
        Computes partial derivatives of height difference observation.

        ∂Δh/∂H_station = -1
        ∂Δh/∂H_target = +1

        Note: Only unfixed Z coordinates appear in param_index.
        Fixed point heights are constants and don't appear in A.
        """
        n_params = len(param_index)
        A_row = np.zeros(n_params)

        # Partial derivative w.r.t. station height (if not fixed)
        station_z_key = f"{self.station}_z"
        if station_z_key in param_index:
            A_row[param_index[station_z_key]] = -1.0

        # Partial derivative w.r.t. target height (if not fixed)
        target_z_key = f"{self.target}_z"
        if target_z_key in param_index:
            A_row[param_index[target_z_key]] = +1.0

        return A_row

    def get_observation_type(self) -> str:
        return "levelling"

    def get_display_value(self, angle_unit: str = "gon") -> str:
        """Returns formatted height difference."""
        return f"{self.value:+.4f} m"
