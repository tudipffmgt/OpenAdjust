"""
Least squares adjustment algorithm (Gauss-Markov model).

Implements the parametric adjustment (Gauss-Markov model):
    l + v = A * x̂

where:
    l = reduced observations (l - l0)
    v = residuals
    A = design matrix (Jacobian)
    x̂ = estimated parameter corrections

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
        Returns standard deviations for a point (sx, sy, sz) in meters.

        Args:
            point_id: ID of the point

        Returns:
            Tuple (std_x, std_y, std_z) or None if not available
        """
        if self.Qxx is None or not self.param_index:
            return None

        std_x = std_y = std_z = None

        if f"{point_id}_x" in self.param_index:
            idx = self.param_index[f"{point_id}_x"]
            std_x = self.sigma_0 * np.sqrt(self.Qxx[idx, idx])

        if f"{point_id}_y" in self.param_index:
            idx = self.param_index[f"{point_id}_y"]
            std_y = self.sigma_0 * np.sqrt(self.Qxx[idx, idx])

        if f"{point_id}_z" in self.param_index:
            idx = self.param_index[f"{point_id}_z"]
            std_z = self.sigma_0 * np.sqrt(self.Qxx[idx, idx])

        if std_x is None and std_y is None and std_z is None:
            return None

        return (std_x or 0.0, std_y or 0.0, std_z or 0.0)

    def get_helmert_point_error(self, point_id: str) -> Optional[float]:
        """
        Returns Helmert's point position error (sH) for a point.

        sH = sqrt(sx² + sy²) for 2D
        sH = sqrt(sx² + sy² + sz²) for 3D

        Args:
            point_id: ID of the point

        Returns:
            Helmert point error in meters, or None if not available
        """
        stds = self.get_point_std(point_id)
        if stds is None:
            return None

        sx, sy, sz = stds
        return np.sqrt(sx ** 2 + sy ** 2 + sz ** 2)


class LeastSquaresAdjustment:
    """
    Performs least squares adjustment using the Gauss-Markov model.

    The functional model is: l + v = A * x̂

    where:
        l = observations (reduced: l - l0)
        v = residuals
        A = design matrix (Jacobian)
        x̂ = parameter corrections

    The stochastic model is defined by the weight matrix P = σ₀² * Qll⁻¹

    Solution: x̂ = (A'PA)⁻¹ A'Pl = N⁻¹ * n
    where N = A'PA (normal equation matrix)
          n = A'Pl (right-hand side)
    """

    def __init__(self, network: Network, max_iterations: int = 10,
                 convergence_threshold: float = 1e-10,
                 sigma_0_apriori: float = 1.0,
                 significance_level: float = 0.05):
        """
        Initialize the adjustment.

        Args:
            network: The geodetic network to adjust
            max_iterations: Maximum number of iterations
            convergence_threshold: Convergence criterion (max coordinate change in meters)
            sigma_0_apriori: A priori standard deviation of unit weight
            significance_level: Significance level for statistical tests
        """
        self.network = network
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
        self.sigma_0_apriori = sigma_0_apriori
        self.significance_level = significance_level
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
            print(f"Error: Not enough observations. n={n_obs}, u={n_params}, r={redundancy}")
            self.result.converged = False
            return self.result

        self.result.redundancy = redundancy
        self.result.param_index = param_index

        print(f"\n{'=' * 60}")
        print(f"Starting Least Squares Adjustment")
        print(f"{'=' * 60}")
        print(f"Observations: {n_obs}")
        print(f"Parameters: {n_params}")
        print(f"Redundancy: {redundancy}")
        print(f"{'=' * 60}\n")

        # Build weight matrix (constant)
        P = self._build_weight_matrix()
        self.result.weight_matrix = P

        # Iterative adjustment
        for iteration in range(self.max_iterations):
            print(f"Iteration {iteration + 1}:")

            # Build design matrix A
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
                print("  Warning: Singular matrix, using pseudo-inverse")
                x = np.linalg.lstsq(N, n, rcond=None)[0]

            # Calculate maximum correction
            max_correction = np.max(np.abs(x))
            print(f"  Max correction: {max_correction * 1000:.6f} mm")

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
                print(f"  Converged after {iteration + 1} iterations!")
                self.result.converged = True
                self.result.iterations = iteration + 1
                break
        else:
            print(f"  Warning: Did not converge after {self.max_iterations} iterations")
            self.result.converged = False
            self.result.iterations = self.max_iterations

        # Final calculations with converged coordinates
        A = self._build_design_matrix(param_index)
        l = self._build_observation_vector()

        # Residuals: v = A*x - l (but x≈0 after convergence, so v ≈ -l)
        # More precisely: v = l_observed - l_computed = -(l0 - l_observed) after adjustment
        v = A @ x - l  # This gives small residuals after convergence

        # Actually, residuals should be: v = l_adjusted - l_observed
        # Let's recalculate properly
        v = self._compute_residuals()

        # Weighted sum of squared residuals
        vPv = v.T @ P @ v

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
        self.result.corrections = x
        self.result.test_passed = test_passed
        self.result.test_statistic = test_stat
        self.result.test_critical_lower = lower
        self.result.test_critical_upper = upper

        # Store adjusted coordinates
        for point_id, point in self.network.points.items():
            self.result.adjusted_coords[point_id] = (point.x, point.y, point.z)

        # Print summary
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
        """
        Builds the reduced observation vector (l - l0).

        l = measured value
        l0 = computed value from current coordinates
        """
        observations = self.network.get_enabled_observations()

        l = np.zeros(len(observations))

        for i, obs in enumerate(observations):
            l0 = obs.compute_l0(self.network)
            l[i] = obs.value - l0

        return l

    def _compute_residuals(self) -> np.ndarray:
        """
        Computes residuals v = l_computed - l_observed.

        After adjustment, l_computed should be close to l_observed.
        """
        observations = self.network.get_enabled_observations()

        v = np.zeros(len(observations))

        for i, obs in enumerate(observations):
            l_computed = obs.compute_l0(self.network)  # From adjusted coordinates
            l_observed = obs.value
            v[i] = l_computed - l_observed

        return v

    def _apply_corrections(self, x: np.ndarray, param_index: dict[str, int]) -> None:
        """Applies parameter corrections to the network coordinates."""
        for param_name, idx in param_index.items():
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
        print(f"\n{'=' * 60}")
        print("ADJUSTMENT RESULTS")
        print(f"{'=' * 60}")
        print(f"Converged: {self.result.converged}")
        print(f"Iterations: {self.result.iterations}")
        print(f"Redundancy: {self.result.redundancy}")
        print(f"σ₀ (a posteriori): {self.result.sigma_0:.4f}")
        print(f"vPv: {self.result.vPv:.6f}")
        print(f"\nGlobal Model Test (α={self.significance_level}):")
        print(f"  Test statistic: {self.result.test_statistic:.2f}")
        print(f"  Critical region: [{self.result.test_critical_lower:.2f}, {self.result.test_critical_upper:.2f}]")
        print(f"  Test passed: {self.result.test_passed}")
        print(f"{'=' * 60}\n")


def run_apriori_analysis(network: Network) -> AdjustmentResult:
    """
    Performs a-priori analysis (without actual observations).

    Computes the cofactor matrix Qxx based on the network geometry
    and the stochastic model, without iterative adjustment.

    This is useful for network design and planning.

    Args:
        network: The geodetic network

    Returns:
        AdjustmentResult with Qxx matrix (but no adjusted coordinates)
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
