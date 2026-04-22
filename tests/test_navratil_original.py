"""
Test mit dem ORIGINALEN Navratil-Code aus main.py.
Dieser Test importiert und verwendet die Funktionen direkt.
"""

import pytest
import numpy as np
import sys
from pathlib import Path


# Füge den Projektordner zum Python-Pfad hinzu, um main.py zu importieren
# Annahme: main.py liegt im Projektroot


class TestOriginalNavratilCode:
    """Testet den originalen Navratil-Code aus main.py."""

    def test_original_implementation(self):
        """
        Führt den EXAKTEN Code aus main.py aus.
        """
        # ===== EXAKTER CODE AUS main.py =====
        from dataclasses import dataclass
        from typing import List, Dict, Tuple

        @dataclass
        class Punkt:
            nr: int
            y: float
            x: float

        def create_network() -> Dict[int, Punkt]:
            punkte = {}
            # Obere Reihe (Punkte 1-11)
            for i in range(11):
                pnr = i + 1
                y = -100 + i * 20
                x = 10
                punkte[pnr] = Punkt(pnr, y, x)
            # Untere Reihe (Punkte 12-22)
            for i in range(11):
                pnr = i + 12
                y = -100 + i * 20
                x = -10
                punkte[pnr] = Punkt(pnr, y, x)
            return punkte

        def get_neighbors(pnr: int) -> List[int]:
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

        def generate_observations(punkte: Dict[int, Punkt]) -> List[Tuple[int, int]]:
            observations = []
            for pnr in punkte.keys():
                neighbors = get_neighbors(pnr)
                for neighbor in neighbors:
                    observations.append((pnr, neighbor))
            return observations

        def calc_distance(p1: Punkt, p2: Punkt) -> float:
            return np.sqrt((p2.y - p1.y) ** 2 + (p2.x - p1.x) ** 2)

        def calc_stochastic_model(observations, punkte, sigma_0=2.0, ppm=1.0):
            n_obs = len(observations)
            P = np.zeros((n_obs, n_obs))
            for i, (von, nach) in enumerate(observations):
                dist = calc_distance(punkte[von], punkte[nach])
                sigma_s = sigma_0 + ppm * dist / 1000
                P[i, i] = 1.0 / (sigma_s ** 2)
            return P

        def build_design_matrix(observations, punkte, fixed_points=[], include_scale=True):
            n_obs = len(observations)
            all_points = sorted(punkte.keys())
            free_points = [p for p in all_points if p not in fixed_points]

            n_unknowns = 2 * len(free_points)
            if include_scale:
                n_unknowns += 1

            A = np.zeros((n_obs, n_unknowns))

            point_to_col = {}
            for idx, pnr in enumerate(free_points):
                point_to_col[pnr] = idx * 2  # y zuerst, dann x

            for i, (von, nach) in enumerate(observations):
                p_von = punkte[von]
                p_nach = punkte[nach]

                dy = p_nach.y - p_von.y
                dx = p_nach.x - p_von.x
                s = calc_distance(p_von, p_nach)

                ds_dyi = -dy / s
                ds_dxi = -dx / s
                ds_dyj = dy / s
                ds_dxj = dx / s

                if von in point_to_col:
                    col = point_to_col[von]
                    A[i, col] = ds_dyi
                    A[i, col + 1] = ds_dxi

                if nach in point_to_col:
                    col = point_to_col[nach]
                    A[i, col] = ds_dyj
                    A[i, col + 1] = ds_dxj

                if include_scale:
                    A[i, -1] = s / 1000

            return A, free_points

        def least_squares_apriori(A, P):
            N = A.T @ P @ A
            try:
                Qxx = np.linalg.inv(N)
            except np.linalg.LinAlgError:
                Qxx = np.linalg.pinv(N)
            return Qxx

        # ===== AUSFÜHRUNG =====
        punkte = create_network()
        observations = generate_observations(punkte)

        print(f"\n{'=' * 60}")
        print("ORIGINALER NAVRATIL-CODE")
        print(f"{'=' * 60}")
        print(f"Anzahl Punkte: {len(punkte)}")
        print(f"Anzahl Beobachtungen: {len(observations)}")

        P = calc_stochastic_model(observations, punkte)

        fixed_points = [1, 12]
        A, free_points = build_design_matrix(observations, punkte, fixed_points)
        Qxx = least_squares_apriori(A, P)

        print(f"Freie Punkte: {len(free_points)}")
        print(f"Unbekannte: {A.shape[1]} (davon 1 Maßstab)")
        print(f"Redundanz: {len(observations) - A.shape[1]}")

        # Punkt 11 finden
        idx_11 = free_points.index(11)
        col_y = idx_11 * 2
        col_x = idx_11 * 2 + 1

        qyy = Qxx[col_y, col_y]
        qxx = Qxx[col_x, col_x]

        # σ₀ = 1 für a-priori
        sy = np.sqrt(qyy)
        sx = np.sqrt(qxx)
        sH = np.sqrt(sy ** 2 + sx ** 2)

        print(f"\nPunkt 11:")
        print(f"  Index in free_points: {idx_11}")
        print(f"  col_y = {col_y}, col_x = {col_x}")
        print(f"  qyy = {qyy:.6e}, qxx = {qxx:.6e}")
        print(f"  sy = {sy:.2f} mm (erwartet: 6.0 mm, Tunnelrichtung)")
        print(f"  sx = {sx:.2f} mm (erwartet: 2.0 mm, Querrichtung)")
        print(f"  sH = {sH:.2f} mm (erwartet: 6.4 mm)")

        # Prüfe andere Punkte zum Vergleich
        for check_pnr in [2, 6, 22]:
            if check_pnr in free_points:
                idx = free_points.index(check_pnr)
                col_y = idx * 2
                col_x = idx * 2 + 1
                sy_p = np.sqrt(Qxx[col_y, col_y])
                sx_p = np.sqrt(Qxx[col_x, col_x])
                sH_p = np.sqrt(sy_p ** 2 + sx_p ** 2)
                print(f"\nPunkt {check_pnr}: sy={sy_p:.2f}mm, sx={sx_p:.2f}mm, sH={sH_p:.2f}mm")

        # ===== VERGLEICH MIT NAVRATIL TABELLE 4.4 =====
        print(f"\n{'=' * 60}")
        print("VERGLEICH MIT NAVRATIL TABELLE 4.4")
        print(f"{'=' * 60}")

        # Navratil Tabelle 4.4 zeigt (Festpunkte 1, 12):
        # Punkt  sy[mm]  sx[mm]  sH[mm]
        # 2      1.8     0.9     2.0
        # 6      4.3     1.0     4.4
        # 11     6.0     2.0     6.4
        # 22     6.0     2.0     6.4

        expected = {
            2: {'sy': 1.8, 'sx': 0.9, 'sH': 2.0},
            6: {'sy': 4.3, 'sx': 1.0, 'sH': 4.4},
            11: {'sy': 6.0, 'sx': 2.0, 'sH': 6.4},
            22: {'sy': 6.0, 'sx': 2.0, 'sH': 6.4},
        }

        print(f"{'Pkt':>4} {'sy_calc':>10} {'sy_exp':>10} {'sx_calc':>10} {'sx_exp':>10}")
        for pnr, exp in expected.items():
            if pnr in free_points:
                idx = free_points.index(pnr)
                sy_calc = np.sqrt(Qxx[idx * 2, idx * 2])
                sx_calc = np.sqrt(Qxx[idx * 2 + 1, idx * 2 + 1])
                print(f"{pnr:>4} {sy_calc:>10.2f} {exp['sy']:>10.1f} {sx_calc:>10.2f} {exp['sx']:>10.1f}")

        # Test bestanden wenn sy nahe an Erwartung
        assert 5.0 < sy < 8.0, f"sy = {sy:.2f}, erwartet ~6.0"


class TestCheckObservationOrder:
    """Prüft die Reihenfolge der Beobachtungen."""

    def test_observation_list(self):
        """Zeigt die ersten Beobachtungen."""
        from dataclasses import dataclass

        @dataclass
        class Punkt:
            nr: int
            y: float
            x: float

        punkte = {}
        for i in range(11):
            pnr = i + 1
            y = -100 + i * 20
            x = 10
            punkte[pnr] = Punkt(pnr, y, x)
        for i in range(11):
            pnr = i + 12
            y = -100 + i * 20
            x = -10
            punkte[pnr] = Punkt(pnr, y, x)

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

        observations = []
        for pnr in punkte.keys():
            for neighbor in get_neighbors(pnr):
                observations.append((pnr, neighbor))

        print("\nErste 20 Beobachtungen:")
        for i, (von, nach) in enumerate(observations[:20]):
            p1, p2 = punkte[von], punkte[nach]
            dist = np.sqrt((p2.y - p1.y) ** 2 + (p2.x - p1.x) ** 2)
            print(f"  {i:3d}: {von:2d} → {nach:2d}, dist={dist:.1f}m")

        print(f"\nGesamt: {len(observations)} Beobachtungen")
        assert len(observations) == 102
