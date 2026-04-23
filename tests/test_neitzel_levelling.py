"""
Tests based on Neitzel's levelling network example.

Reference: Neitzel, F. (2024): "Zur Ausgleichung angeschlossener Höhennetze"
           zfv - Zeitschrift für Geodäsie, Geoinformation und Landmanagement, 6/2024

Original data from: Baumann (1993), S. 29 ff.

This is a LINEAR adjustment problem - no iteration required!
"""

import pytest
import numpy as np
from openadjust.core.point import Point
from openadjust.core.network import Network
from openadjust.core.adjustment import LeastSquaresAdjustment
from openadjust.models.levelling import LevellingObservation


class TestNeitzelLevellingNetwork:
    """
    Test cases based on Neitzel's levelling network example.

    Network structure:
    - 3 fixed points: A, B, C (known heights)
    - 3 new points: 1, 2, 3 (heights to be determined)
    - 8 height difference observations

    Reference solution (Neitzel Eq. 40):
    - H1 = 333.6605 m
    - H2 = 331.8988 m
    - H3 = 335.8149 m
    """

    @pytest.fixture
    def network(self) -> Network:
        """
        Creates the Neitzel levelling network.

        Fixed points (Table 2):
        - A: H = 332.851 m
        - B: H = 330.437 m
        - C: H = 334.595 m

        New points (heights to be determined):
        - 1, 2, 3
        """
        net = Network(name="Neitzel Höhennetz")

        # Fixed points (benchmarks) - only Z is relevant, X/Y arbitrary
        # Z coordinate = height, fixed_z = True
        net.add_point(Point(id="A", x=0.0, y=0.0, z=332.851,
                            fixed_x=True, fixed_y=True, fixed_z=True))
        net.add_point(Point(id="B", x=100.0, y=0.0, z=330.437,
                            fixed_x=True, fixed_y=True, fixed_z=True))
        net.add_point(Point(id="C", x=50.0, y=100.0, z=334.595,
                            fixed_x=True, fixed_y=True, fixed_z=True))

        # New points - approximate heights (will be adjusted)
        # Start with arbitrary values - should converge to correct solution
        net.add_point(Point(id="1", x=30.0, y=30.0, z=333.0,
                            fixed_x=True, fixed_y=True, fixed_z=False))
        net.add_point(Point(id="2", x=60.0, y=30.0, z=332.0,
                            fixed_x=True, fixed_y=True, fixed_z=False))
        net.add_point(Point(id="3", x=45.0, y=60.0, z=336.0,
                            fixed_x=True, fixed_y=True, fixed_z=False))

        return net

    @pytest.fixture
    def observations(self, network: Network) -> list[LevellingObservation]:
        """
        Creates the 8 height difference observations.

        Table 1 from Neitzel (original from Baumann 1993):
        | Nr | von | nach | Δh [m]  | Gewicht p |
        |----|-----|------|---------|-----------|
        | 1  | A   | 3    | 2.964   | 0.87      |
        | 2  | A   | 1    | 0.811   | 0.82      |
        | 3  | 2   | 1    | 1.765   | 0.72      |
        | 4  | B   | 1    | 3.220   | 1.04      |
        | 5  | B   | 2    | 1.463   | 0.90      |
        | 6  | 2   | C    | 2.693   | 0.71      |
        | 7  | 2   | 3    | 3.917   | 1.12      |
        | 8  | C   | 3    | 1.218   | 0.55      |

        Note: Weight p = 1/σ², so σ = 1/sqrt(p)
        """
        obs_data = [
            # (id, station, target, delta_h, weight)
            ("L1", "A", "3", 2.964, 0.87),
            ("L2", "A", "1", 0.811, 0.82),
            ("L3", "2", "1", 1.765, 0.72),
            ("L4", "B", "1", 3.220, 1.04),
            ("L5", "B", "2", 1.463, 0.90),
            ("L6", "2", "C", 2.693, 0.71),
            ("L7", "2", "3", 3.917, 1.12),
            ("L8", "C", "3", 1.218, 0.55),
        ]

        obs_list = []
        for obs_id, station, target, delta_h, weight in obs_data:
            # σ = 1/sqrt(p), but we need σ for the observation
            # Actually, we can use weight directly since P = diag(weights)
            # So std_dev = 1/sqrt(weight) to get P[i,i] = weight
            std_dev = 1.0 / np.sqrt(weight)

            obs = LevellingObservation(
                id=obs_id,
                station=station,
                target=target,
                value=delta_h,
                std_dev=std_dev
            )
            obs_list.append(obs)

        return obs_list

    def test_network_creation(self, network: Network):
        """Test that network is created correctly."""
        assert len(network.points) == 6  # 3 fixed + 3 new

        # Check fixed point heights
        assert network.get_point("A").z == pytest.approx(332.851)
        assert network.get_point("B").z == pytest.approx(330.437)
        assert network.get_point("C").z == pytest.approx(334.595)

        # Check that fixed points have fixed_z = True
        assert network.get_point("A").fixed_z == True
        assert network.get_point("B").fixed_z == True
        assert network.get_point("C").fixed_z == True

        # Check that new points have fixed_z = False
        assert network.get_point("1").fixed_z == False
        assert network.get_point("2").fixed_z == False
        assert network.get_point("3").fixed_z == False

    def test_observation_count(self, network: Network, observations: list):
        """Test that we have 8 observations."""
        assert len(observations) == 8

    def test_parameter_count(self, network: Network, observations: list):
        """
        Test that only 3 parameters (heights of new points) are unknown.
        """
        for obs in observations:
            network.add_observation(obs)

        param_index = network.get_unknown_parameters()

        # Should have exactly 3 parameters: H1, H2, H3 (only Z coordinates)
        assert len(param_index) == 3

        # Verify the parameters are the Z coordinates of new points
        assert "1_z" in param_index
        assert "2_z" in param_index
        assert "3_z" in param_index

        # Fixed points should NOT be in param_index
        assert "A_z" not in param_index
        assert "B_z" not in param_index
        assert "C_z" not in param_index

    def test_redundancy(self, network: Network, observations: list):
        """Test redundancy: r = n - u = 8 - 3 = 5."""
        for obs in observations:
            network.add_observation(obs)

        redundancy = network.get_redundancy()
        assert redundancy == 5

    def test_levelling_observation_derivatives(self, network: Network):
        """Test that levelling observation computes correct derivatives."""
        # Simple test: height difference from A to 1
        obs = LevellingObservation(
            id="test",
            station="A",
            target="1",
            value=0.811,
            std_dev=1.0
        )

        # A is fixed, 1 is free, so only 1_z should appear
        param_index = {"1_z": 0, "2_z": 1, "3_z": 2}
        A_row = obs.compute_A_row(network, param_index)

        # ∂Δh/∂H_A = -1, but A is fixed so not in param_index
        # ∂Δh/∂H_1 = +1
        assert A_row[0] == pytest.approx(1.0)  # 1_z
        assert A_row[1] == pytest.approx(0.0)  # 2_z
        assert A_row[2] == pytest.approx(0.0)  # 3_z

    def test_levelling_between_new_points(self, network: Network):
        """Test derivatives for observation between two new points."""
        # Height difference from 2 to 1
        obs = LevellingObservation(
            id="test",
            station="2",
            target="1",
            value=1.765,
            std_dev=1.0
        )

        param_index = {"1_z": 0, "2_z": 1, "3_z": 2}
        A_row = obs.compute_A_row(network, param_index)

        # ∂Δh/∂H_2 = -1, ∂Δh/∂H_1 = +1
        assert A_row[0] == pytest.approx(1.0)  # 1_z (target)
        assert A_row[1] == pytest.approx(-1.0)  # 2_z (station)
        assert A_row[2] == pytest.approx(0.0)  # 3_z

    def test_adjustment_solution(self, network: Network, observations: list):
        """
        Test that adjustment gives correct solution.

        Reference solution from Neitzel (2024), Equation 40:
        - H1 = 333.6605 m
        - H2 = 331.8988 m
        - H3 = 335.8149 m
        """
        for obs in observations:
            network.add_observation(obs)

        adj = LeastSquaresAdjustment(
            network,
            max_iterations=10,
            convergence_threshold=1e-12,
            verbose=True
        )
        result = adj.run()

        assert result.converged, "Levelling network should converge"

        # Get adjusted heights
        H1 = network.get_point("1").z
        H2 = network.get_point("2").z
        H3 = network.get_point("3").z

        print(f"\n{'=' * 60}")
        print("NEITZEL HÖHENNETZ - ERGEBNISSE")
        print(f"{'=' * 60}")
        print(f"Adjusted heights:")
        print(f"  H1 = {H1:.4f} m (expected: 333.6605 m)")
        print(f"  H2 = {H2:.4f} m (expected: 331.8988 m)")
        print(f"  H3 = {H3:.4f} m (expected: 335.8149 m)")
        print(f"{'=' * 60}")

        # Check against reference values (tolerance 0.1 mm)
        assert H1 == pytest.approx(333.6605, abs=0.0001), f"H1 = {H1}, expected 333.6605"
        assert H2 == pytest.approx(331.8988, abs=0.0001), f"H2 = {H2}, expected 331.8988"
        assert H3 == pytest.approx(335.8149, abs=0.0001), f"H3 = {H3}, expected 335.8149"

    def test_residuals(self, network: Network, observations: list):
        """
        Test that residuals match reference values.

        Reference residuals from Neitzel (2024), Table 3 [mm]:
        v1 = -0.08, v2 = -1.52, v3 = -3.31, v4 = 3.48
        v5 = -1.21, v6 = 3.21, v7 = -0.88, v8 = 1.92
        """
        for obs in observations:
            network.add_observation(obs)

        adj = LeastSquaresAdjustment(network, verbose=False)
        result = adj.run()

        expected_residuals_mm = [-0.08, -1.52, -3.31, 3.48, -1.21, 3.21, -0.88, 1.92]

        print(f"\n{'=' * 60}")
        print("VERBESSERUNGEN (Residuals)")
        print(f"{'=' * 60}")
        print(f"{'Nr':>3} {'v_calc [mm]':>12} {'v_exp [mm]':>12} {'Diff [mm]':>12}")

        max_diff = 0
        for i, (v_calc, v_exp) in enumerate(zip(result.residuals, expected_residuals_mm)):
            v_calc_mm = v_calc * 1000  # Convert to mm
            diff = abs(v_calc_mm - v_exp)
            max_diff = max(max_diff, diff)
            print(f"{i + 1:>3} {v_calc_mm:>12.2f} {v_exp:>12.2f} {diff:>12.3f}")

        print(f"\nMax difference: {max_diff:.3f} mm")

        # Check residuals (tolerance 0.1 mm)
        for i, (v_calc, v_exp) in enumerate(zip(result.residuals, expected_residuals_mm)):
            v_calc_mm = v_calc * 1000
            assert v_calc_mm == pytest.approx(v_exp, abs=0.1), \
                f"Residual {i + 1}: {v_calc_mm:.2f} mm, expected {v_exp} mm"

    def test_linear_problem_single_iteration(self, network: Network, observations: list):
        """
        Verify this is a linear problem - should converge in 1-2 iterations.

        Neitzel emphasizes that levelling is LINEAR and requires no iteration
        when solved directly. With approximate coordinates, it may need 1-2
        iterations due to the way our adjustment is structured.
        """
        for obs in observations:
            network.add_observation(obs)

        adj = LeastSquaresAdjustment(network, verbose=True)
        result = adj.run()

        print(f"\nIterations needed: {result.iterations}")

        # Should converge very quickly (1-2 iterations max for linear problem)
        assert result.iterations <= 3, \
            f"Linear problem should converge quickly, but took {result.iterations} iterations"


class TestLevellingObservationWeight:
    """Test weight handling for levelling observations."""

    def test_weight_from_std_dev(self):
        """Test that weight is correctly computed from std_dev."""
        # If we want weight p = 0.87, then σ = 1/sqrt(0.87) ≈ 1.072
        weight = 0.87
        std_dev = 1.0 / np.sqrt(weight)

        obs = LevellingObservation(
            id="test",
            station="A",
            target="B",
            value=1.0,
            std_dev=std_dev
        )

        # obs.weight should give us back p = 1/σ²
        assert obs.weight == pytest.approx(weight, rel=1e-10)
