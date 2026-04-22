"""
Simulation of geodetic observations from coordinates.

Generates synthetic observations with realistic noise for testing
and educational purposes.
"""

import numpy as np
from typing import TYPE_CHECKING, Optional
from dataclasses import dataclass

if TYPE_CHECKING:
    from openadjust.core.network import Network
    from openadjust.core.point import Point


@dataclass
class NoiseModel:
    """
    Stochastic model for observation noise.

    For distances: σ = base_std + ppm * distance / 1e6
    For angles: σ = angle_std (constant)
    """
    # Distance noise
    distance_base_std: float = 0.002  # 2mm in meters
    distance_ppm: float = 1.0  # 1 ppm

    # Angle noise (radians)
    direction_std: float = 0.0003  # ~0.02 gon = 0.3 mgon
    zenith_std: float = 0.0003  # ~0.02 gon

    def get_distance_std(self, distance: float) -> float:
        """Returns standard deviation for a distance observation."""
        return self.distance_base_std + self.distance_ppm * distance / 1e6

    def get_direction_std(self) -> float:
        """Returns standard deviation for a direction observation."""
        return self.direction_std

    def get_zenith_std(self) -> float:
        """Returns standard deviation for a zenith angle observation."""
        return self.zenith_std


def simulate_distance(p1: 'Point', p2: 'Point',
                      noise_model: Optional[NoiseModel] = None,
                      add_noise: bool = True,
                      seed: Optional[int] = None) -> tuple[float, float]:
    """
    Simulates a distance observation between two points.

    Args:
        p1: Station point
        p2: Target point
        noise_model: Stochastic model for noise
        add_noise: If True, add random noise to the observation
        seed: Random seed for reproducibility

    Returns:
        Tuple of (observed_distance, std_dev)
    """
    if noise_model is None:
        noise_model = NoiseModel()

    if seed is not None:
        np.random.seed(seed)

    # True distance from coordinates
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    dz = p2.z - p1.z
    true_distance = np.sqrt(dx ** 2 + dy ** 2 + dz ** 2)

    # Standard deviation
    std_dev = noise_model.get_distance_std(true_distance)

    # Add noise if requested
    if add_noise:
        noise = np.random.normal(0, std_dev)
        observed_distance = true_distance + noise
    else:
        observed_distance = true_distance

    return observed_distance, std_dev


def simulate_horizontal_distance(p1: 'Point', p2: 'Point',
                                 noise_model: Optional[NoiseModel] = None,
                                 add_noise: bool = True,
                                 seed: Optional[int] = None) -> tuple[float, float]:
    """
    Simulates a horizontal distance observation between two points.

    Args:
        p1: Station point
        p2: Target point
        noise_model: Stochastic model for noise
        add_noise: If True, add random noise
        seed: Random seed

    Returns:
        Tuple of (observed_distance, std_dev)
    """
    if noise_model is None:
        noise_model = NoiseModel()

    if seed is not None:
        np.random.seed(seed)

    # True horizontal distance
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    true_distance = np.sqrt(dx ** 2 + dy ** 2)

    # Standard deviation
    std_dev = noise_model.get_distance_std(true_distance)

    # Add noise
    if add_noise:
        noise = np.random.normal(0, std_dev)
        observed_distance = true_distance + noise
    else:
        observed_distance = true_distance

    return observed_distance, std_dev


def simulate_direction(p1: 'Point', p2: 'Point',
                       orientation: float = 0.0,
                       noise_model: Optional[NoiseModel] = None,
                       add_noise: bool = True,
                       seed: Optional[int] = None) -> tuple[float, float]:
    """
    Simulates a horizontal direction observation.

    Args:
        p1: Station point
        p2: Target point
        orientation: Orientation unknown (radians)
        noise_model: Stochastic model
        add_noise: If True, add random noise
        seed: Random seed

    Returns:
        Tuple of (observed_direction, std_dev) in radians
    """
    if noise_model is None:
        noise_model = NoiseModel()

    if seed is not None:
        np.random.seed(seed)

    # True bearing
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    bearing = np.arctan2(dx, dy)  # Geodetic convention
    if bearing < 0:
        bearing += 2 * np.pi

    # Direction = bearing - orientation
    true_direction = bearing - orientation
    if true_direction < 0:
        true_direction += 2 * np.pi

    # Standard deviation
    std_dev = noise_model.get_direction_std()

    # Add noise
    if add_noise:
        noise = np.random.normal(0, std_dev)
        observed_direction = true_direction + noise
    else:
        observed_direction = true_direction

    return observed_direction, std_dev


def simulate_zenith_angle(p1: 'Point', p2: 'Point',
                          instrument_height: float = 0.0,
                          target_height: float = 0.0,
                          noise_model: Optional[NoiseModel] = None,
                          add_noise: bool = True,
                          seed: Optional[int] = None) -> tuple[float, float]:
    """
    Simulates a zenith angle observation.

    Args:
        p1: Station point
        p2: Target point
        instrument_height: Height of instrument
        target_height: Height of target
        noise_model: Stochastic model
        add_noise: If True, add random noise
        seed: Random seed

    Returns:
        Tuple of (observed_zenith, std_dev) in radians
    """
    if noise_model is None:
        noise_model = NoiseModel()

    if seed is not None:
        np.random.seed(seed)

    # Height difference
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    dz = (p2.z + target_height) - (p1.z + instrument_height)

    # Horizontal distance
    s_horiz = np.sqrt(dx ** 2 + dy ** 2)

    # Zenith angle
    true_zenith = np.arctan2(s_horiz, dz)

    # Standard deviation
    std_dev = noise_model.get_zenith_std()

    # Add noise
    if add_noise:
        noise = np.random.normal(0, std_dev)
        observed_zenith = true_zenith + noise
    else:
        observed_zenith = true_zenith

    return observed_zenith, std_dev


def perturb_coordinates(network: 'Network',
                        std_xy: float = 0.01,
                        std_z: float = 0.01,
                        seed: Optional[int] = None) -> dict[str, tuple[float, float, float]]:
    """
    Perturbs coordinates to create approximate values for adjustment.

    This simulates the situation where we have approximate coordinates
    and need to refine them through adjustment.

    Args:
        network: The network with true coordinates
        std_xy: Standard deviation for XY perturbation (meters)
        std_z: Standard deviation for Z perturbation (meters)
        seed: Random seed

    Returns:
        Dictionary of original coordinates {point_id: (x, y, z)}
    """
    if seed is not None:
        np.random.seed(seed)

    original_coords = {}

    for point_id, point in network.points.items():
        # Store original
        original_coords[point_id] = (point.x, point.y, point.z)

        # Perturb if not fixed
        if not point.fixed_x:
            point.x += np.random.normal(0, std_xy)
        if not point.fixed_y:
            point.y += np.random.normal(0, std_xy)
        if not point.fixed_z:
            point.z += np.random.normal(0, std_z)

    return original_coords
