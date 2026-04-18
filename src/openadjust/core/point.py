"""
Point class for representing survey points with 3D coordinates.
"""

from dataclasses import dataclass, field
from typing import Optional
import numpy as np


@dataclass
class Point:
    """
    Represents a survey point with 3D coordinates.
    
    Attributes:
        id: Unique identifier for the point
        x: X coordinate (Easting/Rechtswert)
        y: Y coordinate (Northing/Hochwert)
        z: Z coordinate (Height/Höhe)
        fixed_x: If True, X coordinate is held fixed during adjustment
        fixed_y: If True, Y coordinate is held fixed during adjustment
        fixed_z: If True, Z coordinate is held fixed during adjustment
        std_x: A posteriori standard deviation of X (after adjustment)
        std_y: A posteriori standard deviation of Y (after adjustment)
        std_z: A posteriori standard deviation of Z (after adjustment)
    """
    
    id: str
    x: float
    y: float
    z: float = 0.0
    
    # Festlegung (Datum)
    fixed_x: bool = False
    fixed_y: bool = False
    fixed_z: bool = False
    
    # A-posteriori Genauigkeiten (werden nach Ausgleichung gefüllt)
    std_x: Optional[float] = None
    std_y: Optional[float] = None
    std_z: Optional[float] = None
    
    def is_fully_fixed(self) -> bool:
        """Returns True if all coordinates are fixed."""
        return self.fixed_x and self.fixed_y and self.fixed_z
    
    def is_fully_free(self) -> bool:
        """Returns True if no coordinates are fixed."""
        return not self.fixed_x and not self.fixed_y and not self.fixed_z
    
    def get_coordinates(self) -> tuple[float, float, float]:
        """Returns coordinates as tuple (x, y, z)."""
        return (self.x, self.y, self.z)
    
    def set_coordinates(self, x: float, y: float, z: Optional[float] = None) -> None:
        """Updates coordinates."""
        self.x = x
        self.y = y
        if z is not None:
            self.z = z
    
    def distance_to(self, other: 'Point') -> float:
        """Calculates 3D distance to another point."""
        return np.sqrt(
            (other.x - self.x)**2 + 
            (other.y - self.y)**2 + 
            (other.z - self.z)**2
        )
    
    def horizontal_distance_to(self, other: 'Point') -> float:
        """Calculates 2D horizontal distance to another point."""
        return np.sqrt(
            (other.x - self.x)**2 + 
            (other.y - self.y)**2
        )
    
    def __repr__(self) -> str:
        fixed_str = ""
        if self.fixed_x or self.fixed_y or self.fixed_z:
            fixed_parts = []
            if self.fixed_x: fixed_parts.append("X")
            if self.fixed_y: fixed_parts.append("Y")
            if self.fixed_z: fixed_parts.append("Z")
            fixed_str = f", fixed={','.join(fixed_parts)}"
        return f"Point(id='{self.id}', x={self.x:.4f}, y={self.y:.4f}, z={self.z:.4f}{fixed_str})"
