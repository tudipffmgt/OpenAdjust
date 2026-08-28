"""
Tests for 3D tacheometry (total station) observations.

This test uses a synthetic example with known "true" coordinates:
- 3 fixed points forming an equilateral triangle at ground level
- 1 new point elevated (simulating a tower/building)

Observations:
- Slope distances from each fixed point to the new point
- Zenith angles from each fixed point to the new point

This tests:
- ZenithObservation model
- DistanceObservation in 3D
- Combined 3D adjustment
"""

import pytest
import numpy as np
from openadjust.core.point import Point
from openadjust.core.network import Network
from openadjust.core.adjustment import LeastSquaresAdjustment, run_apriori_analysis
from openadjust.models.distance import DistanceObservation
from openadjust.models.zenith import ZenithObservation


class TestZenithObservation:
    """Tests for zenith angle observation model."""

    def test_zenith_computation(self):
        """Test zenith angle computation from coordinates."""
        network = Network()

        # Station at ground level
        network.add_point(Point("P1", x=0.0, y=0.0, z=100.0,
                                fixed_x=True, fixed_y=True, fixed_z=True))
        # Target elevated by 50m, horizontal distance 50m
        network.add_point(Point("P2", x=50.0, y=0.0, z=150.0,
                                fixed_x=True, fixed_y=True, fixed_z=True))

        obs = ZenithObservation(
            id="Z1",
            station="P1",
            target="P2",
            value=np.pi / 4,  # 45° = looking up at 45°
            std_dev=0.0003  # ~0.02 gon
        )

        # Compute zenith from coordinates
        # s_horiz = 50, dz = 50 → zenith = arctan(50/50) = 45° = π/4
        l0 = obs.compute_l0(network)
        expected_zenith = np.arctan2(50.0, 50.0)  # arctan2(s_horiz, dz)

        print(f"\nComputed zenith: {np.degrees(l0):.4f}°")
        print(f"Expected zenith: {np.degrees(expected_zenith):.4f}°")

        assert l0 == pytest.approx(expected_zenith, rel=1e-10)

    def test_zenith_looking_down(self):
        """Test zenith angle when looking down."""
        network = Network()

        # Station elevated
        network.add_point(Point("P1", x=0.0, y=0.0, z=150.0,
                                fixed_x=True, fixed_y=True, fixed_z=True))
        # Target at ground level
        network.add_point(Point("P2", x=50.0, y=0.0, z=100.0,
                                fixed_x=True, fixed_y=True, fixed_z=True))

        obs = ZenithObservation(
            id="Z1",
            station="P1",
            target="P2",
            value=0.0,
            std_dev=0.0003
        )

        l0 = obs.compute_l0(network)
        # dz = -50 (looking down), s_horiz = 50
        # zenith = arctan2(50, -50) ≈ 135° (looking below horizontal)

        print(f"\nZenith looking down: {np.degrees(l0):.4f}°")
        print(f"Expected: ~135° (below horizontal)")

        # Zenith > 90° means looking down
        assert l0 > np.pi / 2

    def test_zenith_derivatives(self):
        """Test partial derivatives of zenith observation."""
        network = Network()

        network.add_point(Point("P1", x=0.0, y=0.0, z=100.0,
                                fixed_x=True, fixed_y=True, fixed_z=True))
        network.add_point(Point("P2", x=30.0, y=40.0, z=150.0,
                                fixed_z=False))  # Only Z is unknown

        obs = ZenithObservation(
            id="Z1",
            station="P1",
            target="P2",
            value=np.pi / 4,
            std_dev=0.0003
        )

        # Only P2_z should be in param_index (X, Y fixed)
        param_index = {"P2_z": 0}
        A_row = obs.compute_A_row(network, param_index)

        # ∂z/∂Z_target should be negative (increasing Z decreases zenith)
        print(f"\n∂zenith/∂Z_target = {A_row[0]:.6f}")

        # Derivative should be: -s_horiz / s_3d²
        dx, dy, dz = 30.0, 40.0, 50.0
        s_horiz = np.sqrt(dx ** 2 + dy ** 2)  # 50
        s_3d_sq = dx ** 2 + dy ** 2 + dz ** 2  # 5000
        expected_deriv = -s_horiz / s_3d_sq  # -50/5000 = -0.01

        print(f"Expected derivative: {expected_deriv:.6f}")

        assert A_row[0] == pytest.approx(expected_deriv, rel=1e-6)


class Test3DTacheometry:
    """Tests for combined 3D tacheometry (distances + zenith angles)."""

    @pytest.fixture
    def tower_network(self) -> Network:
        """
        Creates a 3D network for tower surveying.

        True coordinates:
        - P1: (1000, 1000, 100) - Fixed, station 1
        - P2: (1100, 1000, 100) - Fixed, station 2
        - P3: (1050, 1086.603, 100) - Fixed, station 3
        - P4: (1050, 1028.868, 125) - New point (tower)

        The fixed points form an equilateral triangle.
        P4 is at the centroid of the triangle, 25m elevated.
        """
        net = Network(name="Tower Survey 3D")

        # Equilateral triangle vertices at ground level
        net.add_point(Point("P1", x=1000.0, y=1000.0, z=100.0,
                            fixed_x=True, fixed_y=True, fixed_z=True))
        net.add_point(Point("P2", x=1100.0, y=1000.0, z=100.0,
                            fixed_x=True, fixed_y=True, fixed_z=True))
        net.add_point(Point("P3", x=1050.0, y=1086.603, z=100.0,
                            fixed_x=True, fixed_y=True, fixed_z=True))

        # New point at centroid, elevated (approximate coordinates)
        # True: (1050, 1028.868, 125)
        # Start with perturbed values
        net.add_point(Point("P4", x=1050.5, y=1028.5, z=124.5,
                            fixed_x=False, fixed_y=False, fixed_z=False))

        return net

    @pytest.fixture
    def true_coords(self) -> dict:
        """True coordinates for verification."""
        return {
            "P1": (1000.0, 1000.0, 100.0),
            "P2": (1100.0, 1000.0, 100.0),
            "P3": (1050.0, 1086.603, 100.0),
            "P4": (1050.0, 1028.868, 125.0)  # Centroid at Z=125
        }

    def _calc_true_distance(self, true_coords: dict, sta: str, tgt: str) -> float:
        """Calculate true 3D distance between two points."""
        x1, y1, z1 = true_coords[sta]
        x2, y2, z2 = true_coords[tgt]
        return np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)

    def _calc_true_zenith(self, true_coords: dict, sta: str, tgt: str) -> float:
        """Calculate true zenith angle from station to target."""
        x1, y1, z1 = true_coords[sta]
        x2, y2, z2 = true_coords[tgt]

        dx = x2 - x1
        dy = y2 - y1
        dz = z2 - z1

        s_horiz = np.sqrt(dx ** 2 + dy ** 2)
        return np.arctan2(s_horiz, dz)

    def test_network_geometry(self, tower_network: Network, true_coords: dict):
        """Verify network geometry."""
        # Check that fixed points form equilateral triangle
        d12 = self._calc_true_distance(true_coords, "P1", "P2")
        d23 = self._calc_true_distance(true_coords, "P2", "P3")
        d13 = self._calc_true_distance(true_coords, "P1", "P3")

        print(f"\nTriangle side lengths:")
        print(f"  P1-P2: {d12:.3f} m")
        print(f"  P2-P3: {d23:.3f} m")
        print(f"  P1-P3: {d13:.3f} m")

        # All sides should be ~100m
        assert d12 == pytest.approx(100.0, rel=0.01)
        assert d23 == pytest.approx(100.0, rel=0.01)
        assert d13 == pytest.approx(100.0, rel=0.01)

    def test_distances_only(self, tower_network: Network, true_coords: dict):
        """Test adjustment with only distance observations."""
        # Add distance observations from each station to P4
        for sta in ["P1", "P2", "P3"]:
            true_dist = self._calc_true_distance(true_coords, sta, "P4")

            tower_network.add_observation(DistanceObservation(
                id=f"D_{sta}_P4",
                station=sta,
                target="P4",
                value=true_dist,
                std_dev=0.002  # 2mm
            ))

        # With only 3 distances, we can determine X, Y but not uniquely Z
        # (distance sphere intersection)
        # This should still converge but with higher Z uncertainty

        adj = LeastSquaresAdjustment(tower_network, verbose=True)
        result = adj.run()

        assert result.converged
        assert result.redundancy == 0  # 3 obs - 3 unknowns = 0

        p4 = tower_network.get_point("P4")
        true_x, true_y, true_z = true_coords["P4"]

        print(f"\nAdjusted P4: ({p4.x:.4f}, {p4.y:.4f}, {p4.z:.4f})")
        print(f"True P4:     ({true_x:.4f}, {true_y:.4f}, {true_z:.4f})")

    def test_distances_and_zenith(self, tower_network: Network, true_coords: dict):
        """
        Test adjustment with distances AND zenith angles.

        This is the complete 3D tacheometry case.
        6 observations (3 distances + 3 zenith), 3 unknowns → redundancy 3
        """
        # Add observations from each station to P4
        for sta in ["P1", "P2", "P3"]:
            true_dist = self._calc_true_distance(true_coords, sta, "P4")
            true_zenith = self._calc_true_zenith(true_coords, sta, "P4")

            # Distance observation
            tower_network.add_observation(DistanceObservation(
                id=f"D_{sta}_P4",
                station=sta,
                target="P4",
                value=true_dist,
                std_dev=0.002  # 2mm
            ))

            # Zenith angle observation
            tower_network.add_observation(ZenithObservation(
                id=f"Z_{sta}_P4",
                station=sta,
                target="P4",
                value=true_zenith,
                std_dev=0.0003  # ~0.02 gon
            ))

        print(f"\n{'=' * 60}")
        print("3D TACHEOMETRY TEST")
        print(f"{'=' * 60}")
        print(f"Observations: 3 distances + 3 zenith angles = 6")
        print(f"Unknowns: X, Y, Z of P4 = 3")
        print(f"Expected redundancy: 3")

        # Run adjustment
        adj = LeastSquaresAdjustment(
            tower_network,
            max_iterations=10,
            convergence_threshold=1e-12,
            verbose=True
        )
        result = adj.run()

        # Verify convergence
        assert result.converged, "3D adjustment should converge"
        assert result.redundancy == 3, f"Expected redundancy 3, got {result.redundancy}"

        # Check adjusted coordinates
        p4 = tower_network.get_point("P4")
        true_x, true_y, true_z = true_coords["P4"]

        print(f"\n{'=' * 60}")
        print("RESULTS")
        print(f"{'=' * 60}")
        print(f"Adjusted P4: X={p4.x:.4f}, Y={p4.y:.4f}, Z={p4.z:.4f}")
        print(f"True P4:     X={true_x:.4f}, Y={true_y:.4f}, Z={true_z:.4f}")
        print(f"Differences: ΔX={abs(p4.x - true_x) * 1000:.2f}mm, "
              f"ΔY={abs(p4.y - true_y) * 1000:.2f}mm, "
              f"ΔZ={abs(p4.z - true_z) * 1000:.2f}mm")

        # Coordinates should match within 0.1mm
        assert p4.x == pytest.approx(true_x, abs=0.0001)
        assert p4.y == pytest.approx(true_y, abs=0.0001)
        assert p4.z == pytest.approx(true_z, abs=0.0001)

    def test_with_noise(self, true_coords: dict):
        """Test 3D adjustment with realistic noisy observations."""
        np.random.seed(42)

        # Create fresh network
        net = Network(name="Tower Survey with Noise")

        net.add_point(Point("P1", x=1000.0, y=1000.0, z=100.0,
                            fixed_x=True, fixed_y=True, fixed_z=True))
        net.add_point(Point("P2", x=1100.0, y=1000.0, z=100.0,
                            fixed_x=True, fixed_y=True, fixed_z=True))
        net.add_point(Point("P3", x=1050.0, y=1086.603, z=100.0,
                            fixed_x=True, fixed_y=True, fixed_z=True))

        # New point with larger initial error
        net.add_point(Point("P4", x=1051.0, y=1027.0, z=123.0,
                            fixed_x=False, fixed_y=False, fixed_z=False))

        # Add noisy observations
        sigma_dist = 0.002  # 2mm
        sigma_zenith = 0.0003  # ~0.02 gon

        for sta in ["P1", "P2", "P3"]:
            x1, y1, z1 = true_coords[sta]
            x2, y2, z2 = true_coords["P4"]

            dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
            true_dist = np.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
            true_zenith = np.arctan2(np.sqrt(dx ** 2 + dy ** 2), dz)

            # Add noise
            obs_dist = true_dist + np.random.normal(0, sigma_dist)
            obs_zenith = true_zenith + np.random.normal(0, sigma_zenith)

            net.add_observation(DistanceObservation(
                id=f"D_{sta}_P4", station=sta, target="P4",
                value=obs_dist, std_dev=sigma_dist
            ))
            net.add_observation(ZenithObservation(
                id=f"Z_{sta}_P4", station=sta, target="P4",
                value=obs_zenith, std_dev=sigma_zenith
            ))

        # Run adjustment
        adj = LeastSquaresAdjustment(net, verbose=True)
        result = adj.run()

        assert result.converged

        p4 = net.get_point("P4")
        true_x, true_y, true_z = true_coords["P4"]

        print(f"\nWith noise:")
        print(f"  σ₀ = {result.sigma_0:.4f} (should be ~1)")
        print(f"  ΔX = {abs(p4.x - true_x) * 1000:.2f} mm")
        print(f"  ΔY = {abs(p4.y - true_y) * 1000:.2f} mm")
        print(f"  ΔZ = {abs(p4.z - true_z) * 1000:.2f} mm")

        # With noisy observations, allow 5mm tolerance
        assert abs(p4.x - true_x) < 0.005
        assert abs(p4.y - true_y) < 0.005
        assert abs(p4.z - true_z) < 0.005

    def test_apriori_analysis(self, tower_network: Network, true_coords: dict):
        """Test a-priori analysis for 3D network."""
        # Add observations
        for sta in ["P1", "P2", "P3"]:
            true_dist = self._calc_true_distance(true_coords, sta, "P4")
            true_zenith = self._calc_true_zenith(true_coords, sta, "P4")

            tower_network.add_observation(DistanceObservation(
                id=f"D_{sta}_P4", station=sta, target="P4",
                value=true_dist, std_dev=0.002
            ))
            tower_network.add_observation(ZenithObservation(
                id=f"Z_{sta}_P4", station=sta, target="P4",
                value=true_zenith, std_dev=0.0003
            ))

        # A-priori analysis
        result = run_apriori_analysis(tower_network)

        print(f"\n{'=' * 60}")
        print("A-PRIORI ANALYSIS")
        print(f"{'=' * 60}")
        print(f"Redundancy: {result.redundancy}")
        print(f"Parameters: {list(result.param_index.keys())}")

        # Get standard deviations for P4
        stds = result.get_point_std("P4")
        if stds:
            sx, sy, sz = stds
            print(f"\nA-priori standard deviations for P4:")
            print(f"  σX = {sx * 1000:.2f} mm")
            print(f"  σY = {sy * 1000:.2f} mm")
            print(f"  σZ = {sz * 1000:.2f} mm")
            print(f"  σH (Helmert) = {result.get_helmert_point_error('P4') * 1000:.2f} mm")


class TestDirectionObservation:
    """Tests for horizontal direction observation model."""

    def test_direction_computation(self):
        """Test direction computation from coordinates."""
        network = Network()

        # Station at origin
        network.add_point(Point("P1", x=0.0, y=0.0, z=0.0,
                                fixed_x=True, fixed_y=True, fixed_z=True))
        # Target to the east (Y direction, geodetic: X=North, Y=East)
        network.add_point(Point("P2", x=0.0, y=100.0, z=0.0,
                                fixed_x=True, fixed_y=True, fixed_z=True))

        from openadjust.models.direction import DirectionObservation

        obs = DirectionObservation(
            id="R1",
            station="P1",
            target="P2",
            value=0.0,
            std_dev=0.0003
        )

        # Direction to east should be π/2 (100 gon / 90°)
        l0 = obs.compute_l0(network)
        expected = np.pi / 2

        print(f"\nDirection to east: {l0 * 200 / np.pi:.4f} gon")
        print(f"Expected: {expected * 200 / np.pi:.4f} gon (100 gon)")

        assert l0 == pytest.approx(expected, rel=1e-10)

    def test_direction_to_north(self):
        """Test direction to north."""
        network = Network()

        network.add_point(Point("P1", x=0.0, y=0.0, z=0.0,
                                fixed_x=True, fixed_y=True, fixed_z=True))
        # Target to the north (X direction, geodetic: X=North, Y=East)
        network.add_point(Point("P2", x=100.0, y=0.0, z=0.0,
                                fixed_x=True, fixed_y=True, fixed_z=True))

        from openadjust.models.direction import DirectionObservation

        obs = DirectionObservation(
            id="R1",
            station="P1",
            target="P2",
            value=0.0,
            std_dev=0.0003
        )

        l0 = obs.compute_l0(network)
        expected = 0.0  # North = 0 gon

        print(f"\nDirection to north: {l0 * 200 / np.pi:.4f} gon")
        print(f"Expected: 0 gon")

        # Should be 0 or 2π (both represent north)
        assert l0 == pytest.approx(0.0, abs=1e-10) or l0 == pytest.approx(2 * np.pi, abs=1e-10)
