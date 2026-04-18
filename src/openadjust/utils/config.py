"""
Configuration management.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json


class AngleUnit(Enum):
    """Angle units."""
    GON = "gon"
    DEGREE = "degree"


class CoordinateSystem(Enum):
    """Coordinate system conventions."""
    XY_EAST_NORTH = "xy_east_north"
    YX_NORTH_EAST = "yx_north_east"
    UTM = "utm"
    GAUSS_KRUEGER = "gauss_krueger"


@dataclass
class ProjectConfig:
    """Project configuration."""
    
    angle_unit: AngleUnit = AngleUnit.GON
    coordinate_system: CoordinateSystem = CoordinateSystem.XY_EAST_NORTH
    language: str = "de"
    max_iterations: int = 10
    convergence_threshold: float = 1e-10
    significance_level: float = 0.05
    decimal_places: int = 4
    
    def save(self, filepath: Path) -> None:
        """Saves configuration to JSON file."""
        data = {
            "angle_unit": self.angle_unit.value,
            "coordinate_system": self.coordinate_system.value,
            "language": self.language,
            "max_iterations": self.max_iterations,
            "convergence_threshold": self.convergence_threshold,
            "significance_level": self.significance_level,
            "decimal_places": self.decimal_places,
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def load(cls, filepath: Path) -> 'ProjectConfig':
        """Loads configuration from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(
            angle_unit=AngleUnit(data.get("angle_unit", "gon")),
            coordinate_system=CoordinateSystem(data.get("coordinate_system", "xy_east_north")),
            language=data.get("language", "de"),
            max_iterations=data.get("max_iterations", 10),
            convergence_threshold=data.get("convergence_threshold", 1e-10),
            significance_level=data.get("significance_level", 0.05),
            decimal_places=data.get("decimal_places", 4),
        )
