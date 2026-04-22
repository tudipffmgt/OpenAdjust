"""
Tests based on Navratil's tunnel network example.
Reference: Navratil, Ausgleichungsrechnung II, Kapitel 4.4

Verified against original tables from the book.
"""

import pytest
import numpy as np
from openadjust.core.point import Point
from openadjust.core.network import Network
from openadjust.core.adjustment import run_apriori_analysis
from openadjust.models.distance import DistanceObservation


class TestNavratilNetwork:
    """Test cases based on Navratil's tunnel network example."""

    @pytest.fixture
    def network(self) -> Network:
        """Creates the Navratil tunnel network with 22 points."""
        net = Network(name="Navratil Tunnelnetz", include_scale=True)

        # Koordinaten nach Navratil Tabelle 4.3
        # y = Tunnelrichtung (-100 bis +100)
        # x = Querrichtung (10 oder -10)

        # Obere Reihe (Punkte 1-11): x = 10
        for i in range(11):
            pnr = str(i + 1)
            y = -100 + i * 20
            x = 10
            net.add_point(Point(id=pnr, x=y, y=x, z=0.0, fixed_z=True))

        # Untere Reihe (Punkte 12-22): x = -10
        for i in range(11):
            pnr = str(i + 12)
            y = -100 + i * 20
            x = -10
            net.add_point(Point(id=pnr, x=y, y=x, z=0.0, fixed_z=True))

        return net

    @pytest.fixture
    def observations(self, network: Network) -> list[DistanceObservation]:
        """Creates all 102 distance observations."""
        obs_list = []
        obs_id = 0

        def get_neighbors(pnr: int) -> list[int]:
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

        for pnr in range(1, 23):
            station = str(pnr)
            for neighbor in get_neighbors(pnr):
                target = str(neighbor)

                p1 = network.get_point(station)
                p2 = network.get_point(target)
                distance = p1.horizontal_distance_to(p2)

                # Genauigkeit: 2mm + 1ppm (Navratil S.73)
                sigma_mm = 2.0 + 1.0 * distance / 1000.0

                obs = DistanceObservation(
                    id=f"D{obs_id}",
                    station=station,
                    target=target,
                    value=distance,
                    std_dev=sigma_mm  # σ in mm wie Navratil
                )
                obs_list.append(obs)
                obs_id += 1

        return obs_list

    def test_network_creation(self, network: Network):
        """Test network geometry."""
        assert len(network.points) == 22
        assert network.include_scale == True

    def test_observation_count(self, network: Network, observations: list):
        """Test observation count (102 according to Navratil p.73)."""
        assert len(observations) == 102

    def test_apriori_fixed_1_12(self, network: Network, observations: list):
        """
        Test: Zwangsfreie Ausgleichung mit Festpunkten 1 und 12.
        Reference: Navratil Tabelle 4.4 (S.75)

        Expected values from book:
        - Punkt 11: sy=14.2mm, sx=37.1mm, sH=39.7mm
        - Punkt 2:  sy=2.0mm,  sx=2.0mm,  sH=2.8mm
        - Redundanz: 61
        """
        for obs in observations:
            network.add_observation(obs)

        # Festpunkte 1 und 12
        network.get_point("1").fixed_x = True
        network.get_point("1").fixed_y = True
        network.get_point("12").fixed_x = True
        network.get_point("12").fixed_y = True

        result = run_apriori_analysis(network)

        # Redundanz: 102 Beob. - 41 Unbekannte (40 Koord. + 1 Maßstab) = 61
        assert result.redundancy == 61, f"Expected 61, got {result.redundancy}"

        # Punkt 11: Navratil Tabelle 4.4 zeigt sy=14.2, sx=37.1, sH=39.7
        sH_11 = result.get_helmert_point_error("11")
        assert sH_11 is not None
        sH_11_mm = sH_11 * 1000 if sH_11 < 1 else sH_11  # Handle both units

        print(f"\nPunkt 11 (Navratil Tabelle 4.4):")
        print(f"  sH berechnet: {sH_11_mm:.1f} mm")
        print(f"  sH erwartet:  39.7 mm")

        # Toleranz 5% für numerische Unterschiede
        assert abs(sH_11_mm - 39.7) < 2.0, f"sH_11 = {sH_11_mm:.1f} mm, erwartet ~39.7 mm"

    def test_apriori_fixed_corners(self, network: Network, observations: list):
        """
        Test: Gezwängte Ausgleichung mit Festpunkten 1, 11, 12, 22.
        Reference: Navratil Tabelle 4.7 (S.77)

        Expected values:
        - Punkt 6: sy=1.6mm, sx=5.1mm, sH=5.4mm
        - Redundanz: 65
        """
        for obs in observations:
            network.add_observation(obs)

        # Festpunkte 1, 11, 12, 22
        for pid in ["1", "11", "12", "22"]:
            network.get_point(pid).fixed_x = True
            network.get_point(pid).fixed_y = True

        result = run_apriori_analysis(network)

        # Redundanz: 102 Beob. - 37 Unbekannte (36 Koord. + 1 Maßstab) = 65
        assert result.redundancy == 65, f"Expected 65, got {result.redundancy}"

        # Punkt 6: Navratil Tabelle 4.7 zeigt sy=1.6, sx=5.1, sH=5.4
        sH_6 = result.get_helmert_point_error("6")
        assert sH_6 is not None
        sH_6_mm = sH_6 * 1000 if sH_6 < 1 else sH_6

        print(f"\nPunkt 6 (Navratil Tabelle 4.7):")
        print(f"  sH berechnet: {sH_6_mm:.1f} mm")
        print(f"  sH erwartet:  5.4 mm")

        # Toleranz für numerische Unterschiede
        assert abs(sH_6_mm - 5.4) < 1.0, f"sH_6 = {sH_6_mm:.1f} mm, erwartet ~5.4 mm"

    def test_compare_all_points_table_4_4(self, network: Network, observations: list):
        """
        Vergleicht alle Punkte mit Navratil Tabelle 4.4.
        """
        for obs in observations:
            network.add_observation(obs)

        network.get_point("1").fixed_x = True
        network.get_point("1").fixed_y = True
        network.get_point("12").fixed_x = True
        network.get_point("12").fixed_y = True

        result = run_apriori_analysis(network)

        # Referenzwerte aus Navratil Tabelle 4.4
        expected_sH = {
            "2": 2.8, "3": 5.2, "4": 8.1, "5": 11.5, "6": 15.3,
            "7": 19.6, "8": 24.1, "9": 29.0, "10": 34.2, "11": 39.7,
            "13": 2.8, "14": 5.2, "15": 8.1, "16": 11.5, "17": 15.3,
            "18": 19.6, "19": 24.1, "20": 29.0, "21": 34.2, "22": 39.7
        }

        print(f"\n{'='*50}")
        print("Vergleich mit Navratil Tabelle 4.4")
        print(f"{'='*50}")
        print(f"{'Pkt':>4} {'sH_calc':>10} {'sH_exp':>10} {'Diff':>10}")

        max_diff = 0
        for pnr, expected in expected_sH.items():
            sH = result.get_helmert_point_error(pnr)
            if sH:
                sH_mm = sH * 1000 if sH < 1 else sH
                diff = abs(sH_mm - expected)
                max_diff = max(max_diff, diff)
                print(f"{pnr:>4} {sH_mm:>10.1f} {expected:>10.1f} {diff:>10.2f}")

        print(f"\nMaximale Abweichung: {max_diff:.2f} mm")

        # Alle Punkte sollten innerhalb von 1mm übereinstimmen
        assert max_diff < 1.0, f"Maximale Abweichung {max_diff:.2f} mm zu groß"


class TestDistanceDerivatives:
    """Test distance observation derivatives."""

    def test_horizontal_distance_with_scale(self):
        """Test derivatives for horizontal distance including scale."""
        network = Network(include_scale=True)
        network.add_point(Point("A", x=0.0, y=0.0, z=0.0, fixed_z=True))
        network.add_point(Point("B", x=100.0, y=0.0, z=0.0, fixed_z=True))

        obs = DistanceObservation(
            id="D1", station="A", target="B",
            value=100.0, std_dev=2.0
        )

        param_index = {"A_x": 0, "A_y": 1, "B_x": 2, "B_y": 3, "scale": 4}
        A_row = obs.compute_A_row(network, param_index)

        # Coordinate derivatives
        assert A_row[0] == pytest.approx(-1.0)  # ∂s/∂xA
        assert A_row[2] == pytest.approx(1.0)   # ∂s/∂xB

        # Scale derivative: s/1000 = 100/1000 = 0.1
        assert A_row[4] == pytest.approx(0.1)
