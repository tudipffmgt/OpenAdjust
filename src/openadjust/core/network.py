"""
Network class - Container for points and observations.
"""

from dataclasses import dataclass, field
from typing import Optional
import numpy as np

from openadjust.core.point import Point
from openadjust.core.observation import Observation


@dataclass
class Network:
    """
    Container for a geodetic network consisting of points and observations.
    
    This class manages the network data and provides methods for building
    the matrices required for least squares adjustment.
    
    Attributes:
        name: Name of the network/project
        points: Dictionary of points (key: point ID)
        observations: List of all observations
        include_scale: If True, include a scale parameter for distance observations
    """

    name: str = "Unnamed Network"
    points: dict[str, Point] = field(default_factory=dict)
    observations: list[Observation] = field(default_factory=list)
    include_scale: bool = False  # NEW: Scale parameter for distance networks

    def add_point(self, point: Point) -> None:
        """Adds a point to the network."""
        if point.id in self.points:
            raise ValueError(f"Point with ID '{point.id}' already exists")
        self.points[point.id] = point

    def add_observation(self, obs: Observation) -> None:
        """Adds an observation to the network."""
        # Validate that station and target exist
        if obs.station not in self.points:
            raise ValueError(f"Station point '{obs.station}' not found in network")
        if obs.target not in self.points:
            raise ValueError(f"Target point '{obs.target}' not found in network")
        self.observations.append(obs)

    def get_point(self, point_id: str) -> Point:
        """Returns a point by ID."""
        if point_id not in self.points:
            raise KeyError(f"Point '{point_id}' not found")
        return self.points[point_id]

    def get_enabled_observations(self) -> list[Observation]:
        """Returns list of enabled observations only."""
        return [obs for obs in self.observations if obs.enabled]

    def get_unknown_parameters(self) -> dict[str, int]:
        """
        Builds a dictionary mapping parameter names to indices.

        Only includes unfixed coordinates. This defines the columns of the design matrix.
        If include_scale is True, adds a scale parameter at the end.

        Returns:
            Dictionary like {'P1_x': 0, 'P1_y': 1, 'P2_x': 2, ..., 'scale': n}
        """
        param_index = {}
        idx = 0

        for point_id, point in self.points.items():
            if not point.fixed_x:
                param_index[f"{point_id}_x"] = idx
                idx += 1
            if not point.fixed_y:
                param_index[f"{point_id}_y"] = idx
                idx += 1
            if not point.fixed_z:
                param_index[f"{point_id}_z"] = idx
                idx += 1

        # Add scale parameter if requested
        if self.include_scale:
            param_index["scale"] = idx

        return param_index

    def get_num_observations(self) -> int:
        """Returns number of enabled observations."""
        return len(self.get_enabled_observations())

    def get_num_unknowns(self) -> int:
        """Returns number of unknown parameters."""
        return len(self.get_unknown_parameters())

    def get_redundancy(self) -> int:
        """Returns the redundancy (degrees of freedom) = n - u."""
        return self.get_num_observations() - self.get_num_unknowns()

    def has_scale_parameter(self) -> bool:
        """Returns True if network includes a scale parameter."""
        return self.include_scale

    def __repr__(self) -> str:
        scale_str = ", scale=True" if self.include_scale else ""
        return (f"Network(name='{self.name}', "
                f"points={len(self.points)}, "
                f"observations={len(self.observations)}, "
                f"redundancy={self.get_redundancy()}{scale_str})")
