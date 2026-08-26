"""
Project file handling for OpenAdjust.

Project files use JSON format (.oadj) for easy inspection and version control.
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from openadjust.core.network import Network
from openadjust.core.point import Point
from openadjust.core.observation import Observation
from openadjust.models.distance import DistanceObservation
from openadjust.models.direction import DirectionObservation
from openadjust.models.zenith import ZenithObservation
from openadjust.models.levelling import LevellingObservation


VERSION = "0.1.0"


def save_project(filepath: str, network: Network,
                 description: str = "") -> bool:
    """
    Saves a network to a project file (.oadj).

    Args:
        filepath: Path to save the file
        network: Network object to save
        description: Optional project description

    Returns:
        True if successful, False otherwise
    """
    project = {
        "version": VERSION,
        "created": datetime.now().isoformat(),
        "name": network.name,
        "description": description,
        "settings": {
            "include_scale": network.include_scale
        },
        "points": [],
        "observations": []
    }

    # Serialize points
    for point_id, point in network.points.items():
        project["points"].append({
            "id": point.id,
            "x": point.x,
            "y": point.y,
            "z": point.z,
            "fixed_x": point.fixed_x,
            "fixed_y": point.fixed_y,
            "fixed_z": point.fixed_z
        })

    # Serialize observations
    for obs in network.observations:
        obs_data = {
            "id": obs.id,
            "type": obs.get_observation_type(),
            "station": obs.station,
            "target": obs.target,
            "value": obs.value,
            "std_dev": obs.std_dev,
            "enabled": obs.enabled
        }

        # Add type-specific fields
        if isinstance(obs, DistanceObservation):
            obs_data["instrument_height"] = obs.instrument_height
            obs_data["target_height"] = obs.target_height

        project["observations"].append(obs_data)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(project, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving project: {e}")
        return False


def load_project(filepath: str) -> Optional[Network]:
    """
    Loads a network from a project file (.oadj).

    Args:
        filepath: Path to the project file

    Returns:
        Network object or None if loading failed
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            project = json.load(f)
    except Exception as e:
        print(f"Error loading project: {e}")
        return None

    # Check version
    file_version = project.get("version", "0.0.0")
    # Future: handle version migrations

    # Create network
    settings = project.get("settings", {})
    network = Network(
        name=project.get("name", "Imported Network"),
        include_scale=settings.get("include_scale", False)
    )

    # Load points
    for point_data in project.get("points", []):
        point = Point(
            id=point_data["id"],
            x=point_data["x"],
            y=point_data["y"],
            z=point_data["z"],
            fixed_x=point_data.get("fixed_x", False),
            fixed_y=point_data.get("fixed_y", False),
            fixed_z=point_data.get("fixed_z", False)
        )
        network.add_point(point)

    # Load observations
    for obs_data in project.get("observations", []):
        obs_type = obs_data["type"]

        if obs_type == "distance":
            obs = DistanceObservation(
                id=obs_data["id"],
                station=obs_data["station"],
                target=obs_data["target"],
                value=obs_data["value"],
                std_dev=obs_data["std_dev"],
                enabled=obs_data.get("enabled", True),
                instrument_height=obs_data.get("instrument_height", 0.0),
                target_height=obs_data.get("target_height", 0.0)
            )
        elif obs_type == "direction":
            obs = DirectionObservation(
                id=obs_data["id"],
                station=obs_data["station"],
                target=obs_data["target"],
                value=obs_data["value"],
                std_dev=obs_data["std_dev"],
                enabled=obs_data.get("enabled", True)
            )
        elif obs_type == "zenith":
            obs = ZenithObservation(
                id=obs_data["id"],
                station=obs_data["station"],
                target=obs_data["target"],
                value=obs_data["value"],
                std_dev=obs_data["std_dev"],
                enabled=obs_data.get("enabled", True)
            )
        elif obs_type == "levelling":
            obs = LevellingObservation(
                id=obs_data["id"],
                station=obs_data["station"],
                target=obs_data["target"],
                value=obs_data["value"],
                std_dev=obs_data["std_dev"],
                enabled=obs_data.get("enabled", True)
            )
        else:
            print(f"Unknown observation type: {obs_type}")
            continue

        network.add_observation(obs)

    return network
