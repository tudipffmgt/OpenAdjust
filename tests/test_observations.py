"""
Tests for observation classes.
"""

import pytest
import numpy as np
from openadjust.core.point import Point
from openadjust.core.network import Network
from openadjust.models.direction import DirectionObservation
from openadjust.models.distance import DistanceObservation


class TestDirectionObservation:
    """Test cases for DirectionObservation."""

    def test_compute_l0_east(self):
        """Test direction calculation - target to the east (geodetic: Y=East)."""
        network = Network()
        network.add_point(Point("P1", x=0.0, y=0.0, z=0.0))
        network.add_point(Point("P2", x=0.0, y=100.0, z=0.0))

        obs = DirectionObservation(
            id="R1", station="P1", target="P2",
            value=0.0, std_dev=0.001
        )

        l0 = obs.compute_l0(network)
        # East direction should be π/2 (100 gon) in geodetic convention
        assert l0 == pytest.approx(np.pi / 2, rel=1e-10)


class TestDistanceObservation:
    """Test cases for DistanceObservation."""

    def test_compute_l0(self):
        """Test distance calculation."""
        network = Network()
        network.add_point(Point("P1", x=0.0, y=0.0, z=0.0))
        network.add_point(Point("P2", x=3.0, y=4.0, z=0.0))

        obs = DistanceObservation(
            id="D1", station="P1", target="P2",
            value=5.0, std_dev=0.001
        )

        l0 = obs.compute_l0(network)
        assert l0 == pytest.approx(5.0)
