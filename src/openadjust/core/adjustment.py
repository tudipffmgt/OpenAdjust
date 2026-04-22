"""
Least squares adjustment algorithm (Gauss-Markov model).

Implements the parametric adjustment:
    l + v = A * x̂

The solution minimizes v'Pv (weighted sum of squared residuals).
"""

from dataclasses import dataclass, field
from typing import Optional
import numpy as np
from scipy import linalg

from openadjust.core.network import Network
from openadjust.core.point import Point
from openadjust.core.statistics import global_model_test, compute_sigma_0


@dataclass
class AdjustmentResult:
    """
    Contains all results from a least squares adjustment.
    """

    converged: bool = False
    iterations: int = 0
    sigma_0: float = 0.0

    # Adjusted coordinates: {point_id: (x, y, z)}
    adjusted_coords: dict[str, tuple[float, float, float]] = field(default_factory=dict)

    # Parameter corrections from last iteration
    corrections: Optional[np.ndarray] = None

    # Residuals
    residuals: Optional[np.ndarray] = None

    # Matrices (for inspection/education)
    Qxx: Optional[np.ndarray] = None
    design_matrix: Optional[np.ndarray] = None
    weight_matrix: Optional[np.ndarray] = None
    normal_matrix: Optional[np.ndarray] = None

    # Cofactor matrix of residuals
    Qvv: Optional[np.ndarray] = None

    # Statistics
    redundancy: int = 0
    vPv: float = 0.0
    test_statistic: float = 0.0
    test_critical_lower: float = 0.0
    test_critical_upper: float = 0.0
    test_passed: bool = False

    # Parameter index mapping
    param_index: dict[str, int] = field(default_factory=dict)

    # For step-by-step mode
    iteration_history: list[dict] = field(default_factory=list)

    def get_point_std(self, point_id: str) -> Optional[tuple[float, float, float]]:
        """
        Returns standard deviations for a point (sx, sy, sz).
        """
        if self.Qxx is None or not self.param_index:
            return None

        std_x = std_y = std_z = 0.0

        if f"{point_id}_x" in self.param_index:
            idx = self.param_index[f"{point_id}_x"]
            std_x = self.sigma_0 * np.sqrt(abs(self.Qxx[idx, idx]))

        if f"{point_id}_y" in self.param_index:
            idx = self.param_index[f"{point_id}_y"]
            std_y = self.sigma_0 * np.sqrt(abs(self.Qxx[idx, idx]))

        if f"{point_id}_z" in self.param_index:
            idx = self.param_index[f"{point_id}_z"]
            std_z = self.sigma_0 * np.sqrt(abs(self.Qxx[idx, idx]))

        if std_x == 0 and std_y == 0 and std_z == 0:
            return None

        return (std_x, std_y, std_z)

    def get_helmert_point_error(self, point_id: str) -> Optional[float]:
        """
        Returns Helmert's point position error (sH) for a point.
        """
        stds = self.get_point_std(point_id)
        if stds is None:
            return None

        sx, sy, sz = stds
        # For 2D: only sx and sy
        if sz == 0:
            return np.sqrt(sx**2 + sy**2)
        return np.sqrt(sx**2 + sy**2 + sz**2)

    def get_residual_for_observation(self, obs_index: int) -> Optional[float]:
        """Returns the residual for a specific observation."""
        if self.residuals is None or obs_index >= len(self.residuals):
            return None
        return self.residuals[obs_index]

    def get_normalized_residual(self, obs_index: int) -> Optional[float]:
        """
        Returns the normalized residual for outlier detection.
        w = v / (σ₀ * sqrt(qvv))
        """
        if self.residuals is None or self.Qvv is None:
            return None
        if obs_index >= len(self.residuals):
            return None

        v = self.residuals[obs_index]
        qvv = self.Qvv[obs_index, obs_index]

        if qvv <= 0 or self.sigma_0 <= 0:
            return None

        return v / (self.sigma_0 * np.sqrt(qvv))


class LeastSquaresAdjustment:
    """
    Performs least squares adjustment using the Gauss-Markov model.

    The functional model is: l + v = A * x̂

    where:
        l = observations (reduced: l - l0)
        v = residuals
        A = design matrix (Jacobian)
        x̂ = parameter corrections

    Solution: x̂ = (A'PA)⁻¹ A'Pl = N⁻¹ * n
    """

    def __init__(self, network: Network, max_iterations: int = 10,
                 convergence_threshold: float = 1e-10,
                 sigma_0_apriori: float = 1.0,
                 significance_level: float = 0.05,
                 verbose: bool = True):
        """
        Initialize the adjustment.

        Args:
            network: The geodetic network to adjust
            max_iterations: Maximum number of iterations
            convergence_threshold: Convergence criterion (max coordinate change)
            sigma_0_apriori: A priori standard deviation of unit weight
            significance_level: Significance level for statistical tests
            verbose: If True, print progress information
        """
        self.network = network
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
        self.sigma_0_apriori = sigma_0_apriori
        self.significance_level = significance_level
        self.verbose = verbose
        self.result = AdjustmentResult()

    def run(self) -> AdjustmentResult:
        """
        Executes the least squares adjustment.

        Returns:
            AdjustmentResult containing all results
        """
        # Get enabled observations and parameter index
        observations = self.network.get_enabled_observations()
        param_index = self.network.get_unknown_parameters()

        n_obs = len(observations)
        n_params = len(param_index)

        # Check for sufficient observations
        redundancy = n_obs - n_params
        if redundancy < 0:
            if self.verbose:
                print(f"Error: Not enough observations. n={n_obs}, u={n_params}")
            self.result.converged = False
            return self.result

        self.result.redundancy = redundancy
        self.result.param_index = param_index

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Starting Least Squares Adjustment")
            print(f"{'='*60}")
            print(f"Observations: {n_obs}")
            print(f"Parameters: {n_params}")
            print(f"Redundancy: {redundancy}")
            print(f"{'='*60}\n")

        # Build weight matrix (constant throughout iterations)
        P = self._build_weight_matrix()
        self.result.weight_matrix = P

        # Iterative adjustment
        for iteration in range(self.max_iterations):
            if self.verbose:
                print(f"Iteration {iteration + 1}:")

            # Build design matrix A at current coordinates
            A = self._build_design_matrix(param_index)

            # Build reduced observation vector (l - l0)
            l = self._build_observation_vector()

            # Form normal equations: N = A'PA, n = A'Pl
            N = A.T @ P @ A
            n = A.T @ P @ l

            # Solve: x = N⁻¹ * n
            try:
                x = np.linalg.solve(N, n)
            except np.linalg.LinAlgError:
                if self.verbose:
                    print("  Warning: Singular matrix, using pseudo-inverse")
                x = np.linalg.lstsq(N, n, rcond=None)[0]

            # Calculate maximum correction
            max_correction = np.max(np.abs(x))
            if self.verbose:
                print(f"  Max correction: {max_correction*1000:.6f} mm")

            # Update coordinates
            self._apply_corrections(x, param_index)

            # Store iteration data
            self.result.iteration_history.append({
                'iteration': iteration + 1,
                'max_correction': max_correction,
                'corrections': x.copy()
            })

            # Check convergence
            if max_correction < self.convergence_threshold:
                if self.verbose:
                    print(f"  ✓ Converged after {iteration + 1} iterations!")
                self.result.converged = True
                self.result.iterations = iteration + 1
                break
        else:
            if self.verbose:
                print(f"  ⚠ Did not converge after {self.max_iterations} iterations")
            self.result.converged = False
            self.result.iterations = self.max_iterations

        # Final calculations with converged coordinates
        A = self._build_design_matrix(param_index)
        l = self._build_observation_vector()

        # Normal equation matrix (final)
        N = A.T @ P @ A

        # Residuals: v = A*x - l (x≈0 after convergence)
        # More accurate: recalculate from adjusted coordinates
        v = self._compute_residuals()

        # Weighted sum of squared residuals
        vPv = float(v.T @ P @ v)

        # A posteriori standard deviation of unit weight
        if redundancy > 0:
            sigma_0 = np.sqrt(vPv / redundancy)
        else:
            sigma_0 = 0.0

        # Cofactor matrix of parameters
        try:
            Qxx = np.linalg.inv(N)
        except np.linalg.LinAlgError:
            Qxx = np.linalg.pinv(N)

        # Cofactor matrix of residuals: Qvv = Qll - A*Qxx*A'
        # where Qll = P⁻¹
        Qll = np.diag(1.0 / np.diag(P))
        Qvv = Qll - A @ Qxx @ A.T

        # Global model test
        test_passed, test_stat, lower, upper = global_model_test(
            vPv, redundancy, self.sigma_0_apriori, self.significance_level
        )

        # Store results
        self.result.sigma_0 = sigma_0
        self.result.residuals = v
        self.result.vPv = vPv
        self.result.design_matrix = A
        self.result.normal_matrix = N
        self.result.Qxx = Qxx
        self.result.Qvv = Qvv
        self.result.corrections = x
        self.result.test_passed = bool(test_passed)
        self.result.test_statistic = float(test_stat)
        self.result.test_critical_lower = float(lower)
        self.result.test_critical_upper = float(upper)

        # Store adjusted coordinates
        for point_id, point in self.network.points.items():
            self.result.adjusted_coords[point_id] = (point.x, point.y, point.z)

        # Print summary
        if self.verbose:
            self._print_summary()

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

    def _compute_residuals(self) -> np.ndarray:
        """Computes residuals v = l_computed - l_observed."""
        observations = self.network.get_enabled_observations()

        v = np.zeros(len(observations))

        for i, obs in enumerate(observations):
            l_computed = obs.compute_l0(self.network)
            l_observed = obs.value
            v[i] = l_computed - l_observed

        return v

    def _apply_corrections(self, x: np.ndarray, param_index: dict[str, int]) -> None:
        """Applies parameter corrections to the network coordinates."""
        for param_name, idx in param_index.items():
            # Handle scale parameter
            if param_name == "scale":
                continue  # Scale is not applied to coordinates

            parts = param_name.rsplit('_', 1)
            point_id = parts[0]
            coord = parts[1]

            point = self.network.points[point_id]
            correction = x[idx]

            if coord == 'x':
                point.x += correction
            elif coord == 'y':
                point.y += correction
            elif coord == 'z':
                point.z += correction

    def _print_summary(self) -> None:
        """Prints adjustment summary."""
        print(f"\n{'='*60}")
        print("ADJUSTMENT RESULTS")
        print(f"{'='*60}")
        print(f"Converged: {self.result.converged}")
        print(f"Iterations: {self.result.iterations}")
        print(f"Redundancy: {self.result.redundancy}")
        print(f"σ₀ (a posteriori): {self.result.sigma_0:.6f}")
        print(f"vPv: {self.result.vPv:.6f}")
        print(f"\nGlobal Model Test (α={self.significance_level}):")
        print(f"  Test statistic: {self.result.test_statistic:.2f}")
        print(f"  Critical region: [{self.result.test_critical_lower:.2f}, "
              f"{self.result.test_critical_upper:.2f}]")
        print(f"  Test passed: {'✓' if self.result.test_passed else '✗'}")
        print(f"{'='*60}\n")


def run_apriori_analysis(network: Network) -> AdjustmentResult:
    """
    Performs a-priori analysis (without actual observations).

    Computes the cofactor matrix Qxx based on the network geometry
    and the stochastic model, without iterative adjustment.
    """
    result = AdjustmentResult()

    observations = network.get_enabled_observations()
    param_index = network.get_unknown_parameters()

    n_obs = len(observations)
    n_params = len(param_index)

    result.redundancy = n_obs - n_params
    result.param_index = param_index

    # Build matrices
    A = np.zeros((n_obs, n_params))
    P = np.zeros((n_obs, n_obs))

    for i, obs in enumerate(observations):
        A[i, :] = obs.compute_A_row(network, param_index)
        P[i, i] = obs.weight

    # Normal equation matrix
    N = A.T @ P @ A

    # Cofactor matrix
    try:
        Qxx = np.linalg.inv(N)
    except np.linalg.LinAlgError:
        Qxx = np.linalg.pinv(N)

    result.design_matrix = A
    result.weight_matrix = P
    result.normal_matrix = N
    result.Qxx = Qxx
    result.sigma_0 = 1.0  # A-priori: σ₀ = 1
    result.converged = True

    return result
