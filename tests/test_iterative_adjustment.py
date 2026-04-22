"""
Tests for the iterative least squares adjustment.
"""

import pytest
import numpy as np
from openadjust.core.point import Point
from openadjust.core.network import Network
from openadjust.core.adjustment import LeastSquaresAdjustment
from openadjust.models.distance import DistanceObservation


class TestIterativeAdjustment:
    """Tests for iterative least squares adjustment."""

    def test_simple_triangle_converges(self):
        """Test adjustment with a simple triangle network."""
        net = Network(name="Simple Triangle")

        # Fixed points
        net.add_point(Point("P1", x=0.0, y=0.0, z=0.0,
                           fixed_x=True, fixed_y=True, fixed_z=True))
        net.add_point(Point("P2", x=100.0, y=0.0, z=0.0,
                           fixed_x=True, fixed_y=True, fixed_z=True))

        # Free point with approximate coordinates
        true_x = 50.0
        true_y = 86.602540378  # 100 * sin(60°)
        net.add_point(Point("P3", x=50.5, y=86.0, z=0.0, fixed_z=True))

        # Perfect observations
        d1 = np.sqrt(true_x**2 + true_y**2)  # ~100.0
        d2 = np.sqrt((true_x - 100)**2 + true_y**2)  # ~100.0

        net.add_observation(DistanceObservation(
            id="D1", station="P1", target="P3", value=d1, std_dev=0.002
        ))
        net.add_observation(DistanceObservation(
            id="D2", station="P2", target="P3", value=d2, std_dev=0.002
        ))
        net.add_observation(DistanceObservation(
            id="D3", station="P1", target="P2", value=100.0, std_dev=0.002
        ))

        adj = LeastSquaresAdjustment(net, max_iterations=10, verbose=True)
        result = adj.run()

        assert result.converged, "Triangle network should converge"

        p3 = net.get_point("P3")
        assert abs(p3.x - true_x) < 0.001
        assert abs(p3.y - true_y) < 0.001

    def test_adjustment_with_noise(self):
        """Test adjustment with noisy observations."""
        np.random.seed(42)

        net = Network(name="Noisy Triangle")

        true_coords = {
            "P1": (0.0, 0.0),
            "P2": (100.0, 0.0),
            "P3": (50.0, 86.602540378)
        }

        net.add_point(Point("P1", x=0.0, y=0.0, z=0.0,
                           fixed_x=True, fixed_y=True, fixed_z=True))
        net.add_point(Point("P2", x=100.0, y=0.0, z=0.0,
                           fixed_x=True, fixed_y=True, fixed_z=True))
        net.add_point(Point("P3", x=50.01, y=86.61, z=0.0, fixed_z=True))

        pairs = [("P1", "P3"), ("P2", "P3"), ("P1", "P2")]
        for i, (sta, tgt) in enumerate(pairs):
            x1, y1 = true_coords[sta]
            x2, y2 = true_coords[tgt]
            true_dist = np.sqrt((x2-x1)**2 + (y2-y1)**2)
            noise = np.random.normal(0, 0.002)

            net.add_observation(DistanceObservation(
                id=f"D{i}", station=sta, target=tgt,
                value=true_dist + noise, std_dev=0.002
            ))

        adj = LeastSquaresAdjustment(net, verbose=True)
        result = adj.run()

        assert result.converged
        assert result.redundancy == 1
        assert result.residuals is not None

    def test_navratil_network_without_scale(self):
        """
        Test Navratil network WITHOUT scale parameter.
        This should converge quickly.
        """
        np.random.seed(123)

        # Network WITHOUT scale parameter
        net = Network(name="Navratil ohne Maßstab", include_scale=False)

        true_coords = {}

        # Add points
        for i in range(11):
            pnr = str(i + 1)
            x = -100 + i * 20
            y = 10
            true_coords[pnr] = (x, y)
            fixed_xy = (pnr == "1")
            net.add_point(Point(id=pnr, x=x, y=y, z=0.0,
                               fixed_x=fixed_xy, fixed_y=fixed_xy, fixed_z=True))

        for i in range(11):
            pnr = str(i + 12)
            x = -100 + i * 20
            y = -10
            true_coords[pnr] = (x, y)
            fixed_xy = (pnr == "12")
            net.add_point(Point(id=pnr, x=x, y=y, z=0.0,
                               fixed_x=fixed_xy, fixed_y=fixed_xy, fixed_z=True))

        def get_neighbors(pnr: int) -> list[int]:
            neighbors = []
            if pnr <= 11:
                if pnr > 1: neighbors.append(pnr - 1)
                if pnr < 11: neighbors.append(pnr + 1)
                neighbors.append(pnr + 11)
                if pnr > 1: neighbors.append(pnr + 10)
                if pnr < 11: neighbors.append(pnr + 12)
            else:
                if pnr > 12: neighbors.append(pnr - 1)
                if pnr < 22: neighbors.append(pnr + 1)
                neighbors.append(pnr - 11)
                if pnr > 12: neighbors.append(pnr - 12)
                if pnr < 22: neighbors.append(pnr - 10)
            return neighbors

        obs_id = 0
        for pnr in range(1, 23):
            station = str(pnr)
            for neighbor in get_neighbors(pnr):
                target = str(neighbor)
                x1, y1 = true_coords[station]
                x2, y2 = true_coords[target]
                true_dist = np.sqrt((x2-x1)**2 + (y2-y1)**2)

                sigma = 0.002 + 1e-6 * true_dist
                noise = np.random.normal(0, sigma)

                net.add_observation(DistanceObservation(
                    id=f"D{obs_id}", station=station, target=target,
                    value=true_dist + noise, std_dev=sigma
                ))
                obs_id += 1

        # Perturb free points
        for pnr in range(2, 12):
            p = net.get_point(str(pnr))
            p.x += np.random.normal(0, 0.01)
            p.y += np.random.normal(0, 0.01)
        for pnr in range(13, 23):
            p = net.get_point(str(pnr))
            p.x += np.random.normal(0, 0.01)
            p.y += np.random.normal(0, 0.01)

        adj = LeastSquaresAdjustment(net, max_iterations=10, verbose=True)
        result = adj.run()

        # Should converge without scale parameter
        assert result.converged, "Network without scale should converge"
        assert result.redundancy == 62  # 102 - 40 (no scale)

        print(f"\nσ₀ = {result.sigma_0:.4f}")


class TestAdjustmentStatistics:
    """Tests for adjustment statistics."""

    def test_global_model_test(self):
        """Test that global model test works correctly."""
        np.random.seed(42)

        net = Network(name="Perfect Triangle")

        net.add_point(Point("P1", x=0.0, y=0.0, z=0.0,
                           fixed_x=True, fixed_y=True, fixed_z=True))
        net.add_point(Point("P2", x=100.0, y=0.0, z=0.0,
                           fixed_x=True, fixed_y=True, fixed_z=True))
        net.add_point(Point("P3", x=50.0, y=86.6, z=0.0, fixed_z=True))

        net.add_observation(DistanceObservation(
            id="D1", station="P1", target="P3", value=100.0, std_dev=0.002
        ))
        net.add_observation(DistanceObservation(
            id="D2", station="P2", target="P3", value=100.0, std_dev=0.002
        ))
        net.add_observation(DistanceObservation(
            id="D3", station="P1", target="P2", value=100.0, std_dev=0.002
        ))

        adj = LeastSquaresAdjustment(net, verbose=True)
        result = adj.run()

        print(f"\nσ₀ = {result.sigma_0}")
        print(f"vPv = {result.vPv}")
        assert result.converged
