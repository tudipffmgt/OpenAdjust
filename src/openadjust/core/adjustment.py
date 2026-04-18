"""
Least squares adjustment algorithm (Gauss-Markov model).
"""

from dataclasses import dataclass, field
from typing import Optional
import numpy as np
from scipy import linalg

from openadjust.core.network import Network
from openadjust.core.point import Point


@dataclass
class AdjustmentResult:
    """
    Contains all results from a least squares adjustment.
    
    Attributes:
        converged: True if adjustment converged successfully
        iterations: Number of iterations performed
        sigma_0: A posteriori standard deviation of unit weight
        adjusted_coords: Dictionary of adjusted coordinates
        residuals: Vector of residuals
        Qxx: Cofactor matrix of adjusted parameters
        design_matrix: The final design matrix A
        weight_matrix: The weight matrix P
        redundancy: Degrees of freedom (n - u)
        test_statistic: Chi-square test statistic
        test_passed: True if global model test passed
    """
    
    converged: bool = False
    iterations: int = 0
    sigma_0: float = 0.0
    
    adjusted_coords: dict[str, tuple[float, float, float]] = field(default_factory=dict)
    residuals: Optional[np.ndarray] = None
    
    # Matrices (for inspection/education)
    Qxx: Optional[np.ndarray] = None
    design_matrix: Optional[np.ndarray] = None
    weight_matrix: Optional[np.ndarray] = None
    normal_matrix: Optional[np.ndarray] = None
    
    redundancy: int = 0
    test_statistic: float = 0.0
    test_passed: bool = False
    
    # For step-by-step mode
    iteration_history: list[dict] = field(default_factory=list)


class LeastSquaresAdjustment:
    """
    Performs least squares adjustment using the Gauss-Markov model.
    
    The functional model is: l + v = A * x
    where:
        l = observations (reduced: l - l0)
        v = residuals
        A = design matrix (Jacobian)
        x = parameter corrections
    """
    
    def __init__(self, network: Network, max_iterations: int = 10,
                 convergence_threshold: float = 1e-10):
        """
        Initialize the adjustment.
        
        Args:
            network: The geodetic network to adjust
            max_iterations: Maximum number of iterations
            convergence_threshold: Convergence criterion (max coordinate change)
        """
        self.network = network
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
        self.result = AdjustmentResult()
    
    def run(self) -> AdjustmentResult:
        """
        Executes the least squares adjustment.
        
        Returns:
            AdjustmentResult containing all results
        """
        # TODO: Implement the actual adjustment algorithm
        # This is a placeholder for now
        
        print("Adjustment not yet implemented - placeholder")
        self.result.converged = False
        
        return self.result
    
    def _build_design_matrix(self, param_index: dict[str, int]) -> np.ndarray:
        """Builds the design matrix A."""
        observations = self.network.get_enabled_observations()
        n_obs = len(observations)
        n_params = len(param_index)
        
        A = np.zeros((n_obs, n_params))
        
        for i, obs in enumerate(observations):
            A[i, :] = obs.compute_A_row(self.network, param_index)
        
        return A
    
    def _build_weight_matrix(self) -> np.ndarray:
        """Builds the diagonal weight matrix P."""
        observations = self.network.get_enabled_observations()
        n_obs = len(observations)
        
        P = np.zeros((n_obs, n_obs))
        
        for i, obs in enumerate(observations):
            P[i, i] = obs.weight
        
        return P
    
    def _build_observation_vector(self) -> np.ndarray:
        """Builds the reduced observation vector (l - l0)."""
        observations = self.network.get_enabled_observations()
        
        l = np.zeros(len(observations))
        
        for i, obs in enumerate(observations):
            l0 = obs.compute_l0(self.network)
            l[i] = obs.value - l0
        
        return l
