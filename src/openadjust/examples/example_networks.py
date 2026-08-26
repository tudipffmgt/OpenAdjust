"""
Predefined example networks for learning geodetic adjustment.

Each example includes:
- Network geometry (points)
- Observations
- Description and learning objectives
- Suggested exercises
"""

import numpy as np
from typing import Optional
from dataclasses import dataclass

from openadjust.core.network import Network
from openadjust.core.point import Point
from openadjust.models.distance import DistanceObservation
from openadjust.models.zenith import ZenithObservation
from openadjust.models.direction import DirectionObservation
from openadjust.models.levelling import LevellingObservation


@dataclass
class ExampleInfo:
    """Information about an example network."""
    id: str
    name: str
    category: str
    description: str
    learning_goals: list[str]
    exercises: list[str]
    reference: str = ""


EXAMPLES = {
    "simple_triangle": ExampleInfo(
        id="simple_triangle",
        name="Einfaches Dreieck",
        category="Einführung",
        description="""
Ein einfaches 2D-Dreiecksnetz mit 2 Festpunkten und 1 Neupunkt.
Ideal für den Einstieg in die Ausgleichungsrechnung.

Geometrie:
- P1, P2: Festpunkte auf einer Basislinie (100m Abstand)
- P3: Neupunkt bildet gleichseitiges Dreieck

Beobachtungen:
- 3 Strecken zwischen allen Punkten
""",
        learning_goals=[
            "Grundprinzip der vermittelnden Ausgleichung verstehen",
            "Zusammenhang zwischen Redundanz und Genauigkeit",
            "Interpretation von σ₀ und Verbesserungen"
        ],
        exercises=[
            "Führe die Ausgleichung durch und interpretiere σ₀",
            "Was passiert, wenn du P1 als einzigen Festpunkt verwendest?",
            "Verdopple die Standardabweichung einer Strecke - wie ändern sich die Ergebnisse?"
        ]
    ),

    "navratil_tunnel_1_12": ExampleInfo(
        id="navratil_tunnel_1_12",
        name="Tunnelnetz (Festpunkte 1, 12)",
        category="Navratil",
        description="""
Streckennetz für Tunnelvermessung nach Navratil, Kapitel 4.4.

Geometrie:
- 22 Punkte in 2 parallelen Reihen (Tunnelröhren)
- Festpunkte 1 und 12 am linken Rand (vor Durchschlag)
- Punkte 11 und 22 am rechten Rand haben größte Unsicherheit

Dies simuliert die Situation VOR dem Tunneldurchschlag.
""",
        learning_goals=[
            "Einfluss der Festpunktwahl auf Punktgenauigkeiten",
            "Fehlerfortpflanzung in Polygonzügen",
            "Interpretation von Fehlerellipsen"
        ],
        exercises=[
            "Vergleiche die Genauigkeit von Punkt 6 und Punkt 11",
            "Warum sind die Ellipsen in Tunnelrichtung länger?",
            "Wechsle zu Festpunkten 1, 11 und beobachte die Änderungen"
        ],
        reference="Navratil (2020): Ausgleichungsrechnung II, Tabelle 4.4"
    ),

    "navratil_tunnel_corners": ExampleInfo(
        id="navratil_tunnel_corners",
        name="Tunnelnetz (Eckpunkte fest)",
        category="Navratil",
        description="""
Gezwängte Ausgleichung mit allen 4 Eckpunkten als Festpunkte.

Geometrie:
- Festpunkte: 1, 11, 12, 22 (alle Ecken)
- Alle anderen Punkte sind Neupunkte

Dies simuliert die Situation NACH dem Tunneldurchschlag
mit Anschluss an beide Portale.
""",
        learning_goals=[
            "Unterschied zwischen zwangsfreier und gezwängter Ausgleichung",
            "Auswirkung von Spannungen im Festpunktfeld",
            "Kritische Beurteilung von Genauigkeitsangaben"
        ],
        exercises=[
            "Vergleiche die maximalen Fehler mit der Variante 'Festpunkte 1, 12'",
            "Was bedeuten die kleineren Ellipsen? Ist das Netz wirklich genauer?",
            "Führe eine Simulation mit fehlerhaften Festpunktkoordinaten durch"
        ],
        reference="Navratil (2020): Ausgleichungsrechnung II, Tabelle 4.7"
    ),

    "neitzel_levelling": ExampleInfo(
        id="neitzel_levelling",
        name="Höhennetz (Nivellement)",
        category="Neitzel",
        description="""
Angeschlossenes Höhennetz nach Neitzel (2024).

Geometrie:
- 3 Festpunkte: A, B, C (Höhenbolzen)
- 3 Neupunkte: 1, 2, 3 (zu bestimmende Höhen)
- 8 Höhenunterschied-Beobachtungen

Besonderheit: Lineares Ausgleichungsproblem (keine Iteration nötig).
""",
        learning_goals=[
            "Ausgleichung von Höhennetzen",
            "Lineare vs. nicht-lineare Beobachtungsgleichungen",
            "Gewichtung nach Streckenlänge"
        ],
        exercises=[
            "Warum konvergiert dieses Netz in 1-2 Iterationen?",
            "Berechne die Redundanz und prüfe das Ergebnis",
            "Welcher Neupunkt hat die höchste Genauigkeit? Warum?"
        ],
        reference="Neitzel (2024): Zur Ausgleichung angeschlossener Höhennetze, zfv 6/2024"
    ),

    "tower_3d": ExampleInfo(
        id="tower_3d",
        name="3D Turmvermessung",
        category="3D Tachymetrie",
        description="""
3D-Polaraufnahme eines erhöhten Punktes (z.B. Turmspitze).

Geometrie:
- 3 Festpunkte bilden Dreieck am Boden
- 1 Neupunkt (P4) ist 25m erhöht
- Beobachtungen: Schrägstrecken + Zenitwinkel

Typische Anwendung in der Ingenieurgeodäsie.
""",
        learning_goals=[
            "Kombination verschiedener Beobachtungstypen",
            "3D-Koordinatenbestimmung mit Tachymeter",
            "Geometrische Stärke der Konfiguration"
        ],
        exercises=[
            "Vergleiche die Genauigkeit in X, Y und Z - warum unterscheiden sie sich?",
            "Was passiert, wenn du nur Strecken (ohne Zenitwinkel) verwendest?",
            "Füge einen 4. Standpunkt hinzu - wie verbessert sich die Genauigkeit?"
        ]
    ),

    "lagenetz_komplex": ExampleInfo(
        id="lagenetz_komplex",
        name="Komplexes Lagenetz",
        category="Fortgeschritten",
        description="""
Größeres 2D-Lagenetz mit verschiedenen Punktkategorien.

Geometrie:
- 2 Festpunkte (varianzfrei, definieren Datum)
- 2 Anschlusspunkte (mit bekannter Unsicherheit)
- 4 Neupunkte (zu bestimmen)
- Kombination aus Strecken und Richtungen

Realistische Netzkonfiguration für Ingenieurvermessung.
""",
        learning_goals=[
            "Umgang mit verschiedenen Punktkategorien",
            "Kombination von Strecken und Richtungen",
            "Einfluss der Netzgeometrie auf Genauigkeit"
        ],
        exercises=[
            "Identifiziere den Punkt mit der größten Unsicherheit",
            "Wie wirkt sich das Entfernen einer Beobachtung aus?",
            "Plane zusätzliche Beobachtungen zur Verbesserung der schwächsten Stelle"
        ]
    )
}


def get_example_list() -> list[dict]:
    """Returns list of available examples with metadata."""
    return [
        {
            "id": info.id,
            "name": info.name,
            "category": info.category,
            "description": info.description.split('\n')[1].strip()  # First line
        }
        for info in EXAMPLES.values()
    ]


def load_example(example_id: str) -> Optional[tuple[Network, ExampleInfo]]:
    """
    Loads an example network.

    Returns:
        Tuple of (Network, ExampleInfo) or None if not found
    """
    if example_id not in EXAMPLES:
        return None

    info = EXAMPLES[example_id]

    if example_id == "simple_triangle":
        network = _create_simple_triangle()
    elif example_id == "navratil_tunnel_1_12":
        network = _create_navratil_tunnel([1, 12])
    elif example_id == "navratil_tunnel_corners":
        network = _create_navratil_tunnel([1, 11, 12, 22])
    elif example_id == "neitzel_levelling":
        network = _create_neitzel_levelling()
    elif example_id == "tower_3d":
        network = _create_tower_3d()
    elif example_id == "lagenetz_komplex":
        network = _create_complex_network()
    else:
        return None

    return network, info


def _create_simple_triangle() -> Network:
    """Creates a simple equilateral triangle network."""
    net = Network(name="Einfaches Dreieck")

    # Points
    net.add_point(Point("P1", x=0.0, y=0.0, z=0.0,
                        fixed_x=True, fixed_y=True, fixed_z=True))
    net.add_point(Point("P2", x=100.0, y=0.0, z=0.0,
                        fixed_x=True, fixed_y=True, fixed_z=True))
    net.add_point(Point("P3", x=50.0, y=86.603, z=0.0,
                        fixed_x=False, fixed_y=False, fixed_z=True))

    # Observations (with small noise for realism)
    np.random.seed(42)
    sigma = 0.002

    pairs = [("P1", "P2", 100.0), ("P1", "P3", 100.0), ("P2", "P3", 100.0)]
    for i, (sta, tgt, true_dist) in enumerate(pairs):
        obs_dist = true_dist + np.random.normal(0, sigma)
        net.add_observation(DistanceObservation(
            id=f"D{i + 1}", station=sta, target=tgt,
            value=obs_dist, std_dev=sigma
        ))

    return net


def _create_navratil_tunnel(fixed_points: list[int]) -> Network:
    """Creates the Navratil tunnel network."""
    net = Network(name=f"Navratil Tunnelnetz (Festpunkte {fixed_points})",
                  include_scale=True)

    # Points
    for i in range(11):
        pnr = i + 1
        x = -100 + i * 20
        y = 10
        is_fixed = pnr in fixed_points
        net.add_point(Point(id=str(pnr), x=x, y=y, z=0.0,
                            fixed_x=is_fixed, fixed_y=is_fixed, fixed_z=True))

    for i in range(11):
        pnr = i + 12
        x = -100 + i * 20
        y = -10
        is_fixed = pnr in fixed_points
        net.add_point(Point(id=str(pnr), x=x, y=y, z=0.0,
                            fixed_x=is_fixed, fixed_y=is_fixed, fixed_z=True))

    # Observations
    def get_neighbors(pnr):
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
            p1 = net.get_point(station)
            p2 = net.get_point(target)
            distance = np.sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2)
            sigma = 2.0 + 1.0 * distance / 1000  # mm

            net.add_observation(DistanceObservation(
                id=f"D{obs_id}", station=station, target=target,
                value=distance, std_dev=sigma
            ))
            obs_id += 1

    return net


def _create_neitzel_levelling() -> Network:
    """Creates the Neitzel levelling network."""
    net = Network(name="Neitzel Höhennetz")

    # Fixed points
    net.add_point(Point("A", x=0.0, y=0.0, z=332.851,
                        fixed_x=True, fixed_y=True, fixed_z=True))
    net.add_point(Point("B", x=100.0, y=0.0, z=330.437,
                        fixed_x=True, fixed_y=True, fixed_z=True))
    net.add_point(Point("C", x=50.0, y=100.0, z=334.595,
                        fixed_x=True, fixed_y=True, fixed_z=True))

    # New points (approximate heights)
    net.add_point(Point("1", x=30.0, y=30.0, z=333.0,
                        fixed_x=True, fixed_y=True, fixed_z=False))
    net.add_point(Point("2", x=60.0, y=30.0, z=332.0,
                        fixed_x=True, fixed_y=True, fixed_z=False))
    net.add_point(Point("3", x=45.0, y=60.0, z=336.0,
                        fixed_x=True, fixed_y=True, fixed_z=False))

    # Observations from Neitzel Table 1
    obs_data = [
        ("L1", "A", "3", 2.964, 0.87),
        ("L2", "A", "1", 0.811, 0.82),
        ("L3", "2", "1", 1.765, 0.72),
        ("L4", "B", "1", 3.220, 1.04),
        ("L5", "B", "2", 1.463, 0.90),
        ("L6", "2", "C", 2.693, 0.71),
        ("L7", "2", "3", 3.917, 1.12),
        ("L8", "C", "3", 1.218, 0.55),
    ]

    for obs_id, station, target, delta_h, weight in obs_data:
        std_dev = 1.0 / np.sqrt(weight)
        net.add_observation(LevellingObservation(
            id=obs_id, station=station, target=target,
            value=delta_h, std_dev=std_dev
        ))

    return net


def _create_tower_3d() -> Network:
    """Creates a 3D tower survey network."""
    net = Network(name="3D Turmvermessung")

    # Ground points (equilateral triangle)
    net.add_point(Point("P1", x=1000.0, y=1000.0, z=100.0,
                        fixed_x=True, fixed_y=True, fixed_z=True))
    net.add_point(Point("P2", x=1100.0, y=1000.0, z=100.0,
                        fixed_x=True, fixed_y=True, fixed_z=True))
    net.add_point(Point("P3", x=1050.0, y=1086.603, z=100.0,
                        fixed_x=True, fixed_y=True, fixed_z=True))

    # Tower point (elevated)
    true_coords = (1050.0, 1028.868, 125.0)
    net.add_point(Point("P4", x=1050.5, y=1028.5, z=124.5,
                        fixed_x=False, fixed_y=False, fixed_z=False))

    # Observations from each ground point
    np.random.seed(42)
    obs_id = 1

    for sta_name in ["P1", "P2", "P3"]:
        sta = net.get_point(sta_name)
        dx = true_coords[0] - sta.x
        dy = true_coords[1] - sta.y
        dz = true_coords[2] - sta.z

        true_dist = np.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
        s_horiz = np.sqrt(dx ** 2 + dy ** 2)
        true_zenith = np.arctan2(s_horiz, dz)

        # Distance
        sigma_dist = 0.002
        net.add_observation(DistanceObservation(
            id=f"D{obs_id}", station=sta_name, target="P4",
            value=true_dist + np.random.normal(0, sigma_dist),
            std_dev=sigma_dist
        ))
        obs_id += 1

        # Zenith angle
        sigma_zenith = 0.0003
        net.add_observation(ZenithObservation(
            id=f"Z{obs_id}", station=sta_name, target="P4",
            value=true_zenith + np.random.normal(0, sigma_zenith),
            std_dev=sigma_zenith
        ))
        obs_id += 1

    return net


def _create_complex_network() -> Network:
    """Creates a more complex 2D network with various point types."""
    net = Network(name="Komplexes Lagenetz")

    # Fixed points (Festpunkte)
    net.add_point(Point("FP1", x=0.0, y=0.0, z=0.0,
                        fixed_x=True, fixed_y=True, fixed_z=True))
    net.add_point(Point("FP2", x=200.0, y=0.0, z=0.0,
                        fixed_x=True, fixed_y=True, fixed_z=True))

    # Connection points (Anschlusspunkte) - have known coordinates but with uncertainty
    # In real adjustment, these would be weighted differently
    net.add_point(Point("AP1", x=0.0, y=150.0, z=0.0,
                        fixed_x=True, fixed_y=True, fixed_z=True))
    net.add_point(Point("AP2", x=200.0, y=150.0, z=0.0,
                        fixed_x=True, fixed_y=True, fixed_z=True))

    # New points (Neupunkte)
    net.add_point(Point("NP1", x=50.0, y=50.0, z=0.0,
                        fixed_x=False, fixed_y=False, fixed_z=True))
    net.add_point(Point("NP2", x=150.0, y=50.0, z=0.0,
                        fixed_x=False, fixed_y=False, fixed_z=True))
    net.add_point(Point("NP3", x=50.0, y=100.0, z=0.0,
                        fixed_x=False, fixed_y=False, fixed_z=True))
    net.add_point(Point("NP4", x=150.0, y=100.0, z=0.0,
                        fixed_x=False, fixed_y=False, fixed_z=True))

    # Distance observations
    np.random.seed(123)
    sigma_dist = 0.002

    distance_pairs = [
        ("FP1", "NP1"), ("FP1", "NP3"),
        ("FP2", "NP2"), ("FP2", "NP4"),
        ("AP1", "NP3"), ("AP2", "NP4"),
        ("NP1", "NP2"), ("NP1", "NP3"),
        ("NP2", "NP4"), ("NP3", "NP4"),
        ("NP1", "NP4"), ("NP2", "NP3")  # Diagonals for stability
    ]

    for i, (sta, tgt) in enumerate(distance_pairs):
        p1 = net.get_point(sta)
        p2 = net.get_point(tgt)
        true_dist = np.sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2)

        net.add_observation(DistanceObservation(
            id=f"D{i + 1}", station=sta, target=tgt,
            value=true_dist + np.random.normal(0, sigma_dist),
            std_dev=sigma_dist
        ))

    # Direction observations from fixed points
    sigma_dir = 0.0003  # radians
    dir_sets = [
        ("FP1", ["NP1", "NP3", "FP2"]),
        ("FP2", ["NP2", "NP4", "FP1"]),
    ]

    dir_id = 1
    for sta, targets in dir_sets:
        sta_point = net.get_point(sta)
        for tgt in targets:
            tgt_point = net.get_point(tgt)
            dx = tgt_point.x - sta_point.x
            dy = tgt_point.y - sta_point.y
            true_dir = np.arctan2(dx, dy)
            if true_dir < 0:
                true_dir += 2 * np.pi

            net.add_observation(DirectionObservation(
                id=f"R{dir_id}", station=sta, target=tgt,
                value=true_dir + np.random.normal(0, sigma_dir),
                std_dev=sigma_dir
            ))
            dir_id += 1

    return net
