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
    orientations: dict[str, float] = field(default_factory=dict)

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
        param_index = {}
        idx = 0
        for point_id, point in self.points.items():
            if not point.fixed_x:
                param_index[f"{point_id}_x"] = idx;
                idx += 1
            if not point.fixed_y:
                param_index[f"{point_id}_y"] = idx;
                idx += 1
            if not point.fixed_z:
                param_index[f"{point_id}_z"] = idx;
                idx += 1

        # Orientierungsunbekannte: eine je Gruppe mit Richtungsbeobachtungen
        seen = []
        for obs in self.get_enabled_observations():
            if obs.get_observation_type() == "direction":
                g = getattr(obs, "orientation_group", obs.station) or obs.station
                if g not in seen:
                    seen.append(g)
                    param_index[f"orientation_{g}"] = idx;
                    idx += 1

        if self.include_scale:
            param_index["scale"] = idx;
            idx += 1
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

    def initialize_orientations(self) -> None:
        groups: dict[str, list] = {}
        for obs in self.get_enabled_observations():
            if obs.get_observation_type() == "direction":
                g = getattr(obs, "orientation_group", obs.station) or obs.station
                groups.setdefault(g, []).append(obs)
        for g, obs_list in groups.items():
            s = c = 0.0
            for obs in obs_list:
                sta = self.get_point(obs.station); tgt = self.get_point(obs.target)
                bearing = np.arctan2(tgt.y - sta.y, tgt.x - sta.x)
                o = bearing - obs.value          # r = bearing - o
                s += np.sin(o); c += np.cos(o)
            self.orientations[g] = float(np.arctan2(s, c))


    def __repr__(self) -> str:
        scale_str = ", scale=True" if self.include_scale else ""
        return (f"Network(name='{self.name}', "
                f"points={len(self.points)}, "
                f"observations={len(self.observations)}, "
                f"redundancy={self.get_redundancy()}{scale_str})")


