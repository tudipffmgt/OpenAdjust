"""
Tests for the Point class.
"""

import pytest
from openadjust.core.point import Point


class TestPoint:
    """Test cases for Point class."""
    
    def test_create_point(self):
        """Test basic point creation."""
        p = Point(id="P1", x=100.0, y=200.0, z=50.0)
        assert p.id == "P1"
        assert p.x == 100.0
        assert p.y == 200.0
        assert p.z == 50.0
    
    def test_point_default_values(self):
        """Test default values."""
        p = Point(id="P1", x=0.0, y=0.0)
        assert p.z == 0.0
        assert p.fixed_x is False
        assert p.fixed_y is False
        assert p.fixed_z is False
    
    def test_point_is_fixed(self):
        """Test fixed point detection."""
        p = Point(id="P1", x=0.0, y=0.0, z=0.0, 
                  fixed_x=True, fixed_y=True, fixed_z=True)
        assert p.is_fully_fixed() is True
        assert p.is_fully_free() is False
    
    def test_point_distance(self):
        """Test distance calculation."""
        p1 = Point(id="P1", x=0.0, y=0.0, z=0.0)
        p2 = Point(id="P2", x=3.0, y=4.0, z=0.0)
        
        assert p1.horizontal_distance_to(p2) == pytest.approx(5.0)
