"""
Base class for all observation types.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional
import numpy as np

if TYPE_CHECKING:
    from openadjust.core.network import Network


@dataclass
class Observation(ABC):
    """
    Abstract base class for geodetic observations.
    
    All observation types (Direction, Zenith, Distance, etc.) inherit from this class
    and implement their specific functional models.
    
    Attributes:
        id: Unique identifier for the observation
        station: ID of the station point (instrument location)
        target: ID of the target point
        value: Measured value (in internal units: radians for angles, meters for distances)
        std_dev: A priori standard deviation of the observation
        enabled: If False, observation is excluded from adjustment
        residual: Residual after adjustment (v = l - l0 - A*x)
        redundancy: Partial redundancy of this observation
    """
    
    id: str
    station: str
    target: str
    value: float
    std_dev: float
    enabled: bool = True
    
    # Results after adjustment
    residual: Optional[float] = None
    redundancy: Optional[float] = None
    normalized_residual: Optional[float] = None
    
    @property
    def weight(self) -> float:
        """Returns the weight p = 1/σ²."""
        return 1.0 / (self.std_dev ** 2)
    
    @property
    def variance(self) -> float:
        """Returns the variance σ²."""
        return self.std_dev ** 2
    
    @abstractmethod
    def compute_l0(self, network: 'Network') -> float:
        """
        Computes the approximate observation value from coordinates.
        
        This is the functional model f(X0) evaluated at the approximate coordinates.
        
        Args:
            network: Network containing all points
            
        Returns:
            Approximate observation value l0
        """
        pass
    
    @abstractmethod
    def compute_A_row(self, network: 'Network', param_index: dict[str, int]) -> np.ndarray:
        """
        Computes one row of the design matrix A.
        
        Contains partial derivatives of the observation equation with respect
        to all unknown parameters.
        
        Args:
            network: Network containing all points
            param_index: Dictionary mapping parameter names to column indices
            
        Returns:
            numpy array representing one row of the design matrix
        """
        pass
    
    @abstractmethod
    def get_observation_type(self) -> str:
        """Returns the observation type as string (for i18n and display)."""
        pass
    
    @abstractmethod
    def get_display_value(self, angle_unit: str = "gon") -> str:
        """Returns the observation value formatted for display."""
        pass
