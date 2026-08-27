"""
Serialization layer: Network/Result <-> plain dict.

Pure logic, no file I/O — this is the bridge between the
browser (Vue) and the Python core (Pyodide). All numpy arrays
are converted to nested lists so JavaScript can consume them.
"""

from typing import Optional
import numpy as np

import math



from openadjust.core.network import Network
from openadjust.core.point import Point
from openadjust.core.adjustment import AdjustmentResult
from openadjust.models.distance import DistanceObservation
from openadjust.models.direction import DirectionObservation
from openadjust.models.zenith import ZenithObservation
from openadjust.models.levelling import LevellingObservation

VERSION = "0.2.0"  # browser-first schema

# Umrechnungsfaktoren (GUI arbeitet in gon, Kern in Radiant)
GON_TO_RAD = math.pi / 200.0
RAD_TO_GON = 200.0 / math.pi

# Beobachtungstypen, deren value/std_dev ein Winkel in gon sind (aus der GUI)
_ANGLE_TYPES = {"direction", "zenith"}

_OBS_CLASSES = {
    "distance": DistanceObservation,
    "direction": DirectionObservation,
    "zenith": ZenithObservation,
    "levelling": LevellingObservation,
}

def _orientations_to_gon(result: 'AdjustmentResult') -> dict:
    """Ausgeglichene Orientierungen je Standpunkt, rad -> gon, normiert [0, 400)."""
    out = {}
    for group, o_rad in getattr(result, "orientations", {}).items():
        gon = (o_rad * RAD_TO_GON) % 400.0
        out[group] = float(gon)
    return out
# --- Network -> dict -----------------------------------------------------

def network_to_dict(network: Network, description: str = "") -> dict:
    """Serializes a Network into a JSON-ready dict."""
    return {
        "version": VERSION,
        "name": network.name,
        "description": description,
        "settings": {"include_scale": network.include_scale},
        "points": [
            {
                "id": p.id, "x": p.x, "y": p.y, "z": p.z,
                "fixed_x": p.fixed_x, "fixed_y": p.fixed_y, "fixed_z": p.fixed_z,
            }
            for p in network.points.values()
        ],
        "observations": [_obs_to_dict(o) for o in network.observations],
    }


def _obs_to_dict(obs) -> dict:
    data = {
        "id": obs.id,
        "type": obs.get_observation_type(),
        "station": obs.station,
        "target": obs.target,
        "value": obs.value,
        "std_dev": obs.std_dev,
        "enabled": obs.enabled,
    }
    if isinstance(obs, DistanceObservation):
        data["instrument_height"] = obs.instrument_height
        data["target_height"] = obs.target_height
    return data


# --- dict -> Network -----------------------------------------------------

def dict_to_network(data: dict) -> Network:
    """Rebuilds a Network from a dict (e.g. uploaded .oadj).

    Angle observations (direction, zenith) are provided by the GUI in gon
    and converted to radians here, since the core models work in radians.
    """
    settings = data.get("settings", {})
    network = Network(
        name=data.get("name", "Imported Network"),
        include_scale=settings.get("include_scale", False),
    )

    for pd in data.get("points", []):
        network.add_point(Point(
            id=pd["id"], x=pd["x"], y=pd["y"], z=pd["z"],
            fixed_x=pd.get("fixed_x", False),
            fixed_y=pd.get("fixed_y", False),
            fixed_z=pd.get("fixed_z", False),
        ))

    for od in data.get("observations", []):
        cls = _OBS_CLASSES.get(od["type"])
        if cls is None:
            continue  # silently skip unknown types

        value = od["value"]
        std_dev = od["std_dev"]

        # Winkel: gon -> rad (Wert UND Standardabweichung!)
        if od["type"] in _ANGLE_TYPES:
            value = value * GON_TO_RAD
            std_dev = std_dev * GON_TO_RAD

        kwargs = dict(
            id=od["id"], station=od["station"], target=od["target"],
            value=value, std_dev=std_dev,
            enabled=od.get("enabled", True),
        )
        if cls is DistanceObservation:
            kwargs["instrument_height"] = od.get("instrument_height", 0.0)
            kwargs["target_height"] = od.get("target_height", 0.0)
        network.add_observation(cls(**kwargs))

    return network


# --- AdjustmentResult -> dict --------------------------------------------

def _arr(a: Optional[np.ndarray]):
    """numpy array -> nested list (JS-friendly), or None."""
    return None if a is None else np.asarray(a).tolist()

def _compute_error_ellipses(result: 'AdjustmentResult') -> dict:
    """Computes 2D error ellipse parameters per point from the 2x2 block of Qxx.

    For each point with free x/y, the 2x2 cofactor submatrix is decomposed
    (symmetric eigendecomposition). Semi-axes are scaled with sigma_0.

    Returns: {point_id: {a, b, theta, major_vec, minor_vec}}
      a, b       -- semi-major/minor axis [m] = sigma_0 * sqrt(eigenvalue)
      theta      -- orientation of major axis [gon], from North(X) toward East(Y)
      major_vec  -- [dNorth, dEast] major semi-axis vector [m] (for plotting)
      minor_vec  -- [dNorth, dEast] minor semi-axis vector [m]
    """
    if result.Qxx is None or not result.param_index:
        return {}

    s0 = result.sigma_0
    ellipses = {}

    for pid in result.adjusted_coords:
        kx, ky = f"{pid}_x", f"{pid}_y"
        if kx not in result.param_index or ky not in result.param_index:
            continue  # Festpunkt (x/y fix) -> keine Fehlerellipse

        ix = result.param_index[kx]
        iy = result.param_index[ky]

        # 2x2-Kofaktor-Teilmatrix (Reihenfolge: x=Nord, y=Ost)
        Q = np.array([
            [result.Qxx[ix, ix], result.Qxx[ix, iy]],
            [result.Qxx[iy, ix], result.Qxx[iy, iy]],
        ])

        # Symmetrische Eigenwertzerlegung -> aufsteigende Eigenwerte
        eigvals, eigvecs = np.linalg.eigh(Q)
        eigvals = np.clip(eigvals, 0.0, None)  # numerisches Rauschen abfangen

        lam_major, lam_minor = eigvals[1], eigvals[0]
        v_major = eigvecs[:, 1]   # (Nord, Ost)-Komponenten der großen Halbachse
        v_minor = eigvecs[:, 0]

        a = float(s0 * np.sqrt(lam_major))
        b = float(s0 * np.sqrt(lam_minor))

        # Orientierung: Winkel der großen Halbachse von Nord(X) Richtung Ost(Y)
        theta_gon = float(np.arctan2(v_major[1], v_major[0]) * 200.0 / np.pi)

        ellipses[pid] = {
            "a": a,
            "b": b,
            "theta": theta_gon,
            "major_vec": [a * float(v_major[0]), a * float(v_major[1])],
            "minor_vec": [b * float(v_minor[0]), b * float(v_minor[1])],
        }

    return ellipses

def _compute_point_stds(result: 'AdjustmentResult') -> dict:
    """Standardabweichungen (sx, sy, sz) je Punkt, aus vorhandener Methode."""
    if result.Qxx is None or not result.param_index:
        return {}
    out = {}
    for pid in result.adjusted_coords:
        std = result.get_point_std(pid)
        if std is None:
            continue
        out[pid] = {"sx": std[0], "sy": std[1], "sz": std[2]}
    return out

def _compute_normalized_residuals(result: 'AdjustmentResult') -> list:
    """Normierte Verbesserungen w_i = |v_i| / (sigma_0 * sqrt(q_vivi)).

    Reihenfolge entspricht den aktiven Beobachtungen (wie residuals).
    None, wenn nicht bestimmbar (z.B. q_vivi <= 0 bei r=0 / unkontrolliert).
    """
    if result.residuals is None or result.Qvv is None:
        return []
    out = []
    for i in range(len(result.residuals)):
        try:
            w = result.get_normalized_residual(i)
        except Exception:
            w = None
        out.append(None if w is None else float(w))
    return out




def result_to_dict(result: AdjustmentResult) -> dict:
    """Serializes an AdjustmentResult into a JSON-ready dict."""
    return {
        "converged": result.converged,
        "iterations": result.iterations,
        "sigma_0": result.sigma_0,
        "redundancy": result.redundancy,
        "vPv": result.vPv,
        "adjusted_coords": {
            pid: list(xyz) for pid, xyz in result.adjusted_coords.items()
        },
        "orientations": _orientations_to_gon(result),
        "error_ellipses": _compute_error_ellipses(result),
        "point_std": _compute_point_stds(result),
        "normalized_residuals": _compute_normalized_residuals(result),
        "param_index": result.param_index,
        "residuals": _arr(result.residuals),
        "corrections": _arr(result.corrections),
        "Qxx": _arr(result.Qxx),
        "Qvv": _arr(result.Qvv),
        "design_matrix": _arr(result.design_matrix),
        "normal_matrix": _arr(result.normal_matrix),
        "test": {
            "statistic": result.test_statistic,
            "critical_lower": result.test_critical_lower,
            "critical_upper": result.test_critical_upper,
            "passed": result.test_passed,
        },
    }
