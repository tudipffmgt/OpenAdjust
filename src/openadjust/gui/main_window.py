"""
Main application window for OpenAdjust.

MVP Features:
- Tab-based interface (Points, Observations, Results)
- Editable tables for data entry
- Adjustment button
- Results display
"""

import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTableWidget, QTableWidgetItem, QPushButton,
    QLabel, QStatusBar, QMenuBar, QMenu, QMessageBox,
    QHeaderView, QCheckBox, QComboBox, QDoubleSpinBox,
    QGroupBox, QTextEdit, QSplitter, QToolBar
)
from PyQt6.QtCore import Qt, QLocale
from PyQt6.QtGui import QAction, QIcon, QFont

from openadjust.core.network import Network
from openadjust.core.point import Point
from openadjust.core.adjustment import LeastSquaresAdjustment, run_apriori_analysis


class PointsTab(QWidget):
    """Tab for entering and editing points."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Table for points
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "X [m]", "Y [m]", "Z [m]", "Fix X", "Fix Y", "Fix Z"
        ])

        # Column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        for i in range(1, 4):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        for i in range(4, 7):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()

        self.btn_add = QPushButton("+ Punkt hinzufügen")
        self.btn_add.clicked.connect(self.add_point)
        button_layout.addWidget(self.btn_add)

        self.btn_remove = QPushButton("- Ausgewählte löschen")
        self.btn_remove.clicked.connect(self.remove_selected)
        button_layout.addWidget(self.btn_remove)

        self.btn_example = QPushButton("Beispiel laden")
        self.btn_example.clicked.connect(self.load_example)
        button_layout.addWidget(self.btn_example)

        button_layout.addStretch()
        layout.addLayout(button_layout)

    def add_point(self, point_id: str = "", x: float = 0.0, y: float = 0.0,
                  z: float = 0.0, fix_x: bool = False, fix_y: bool = False,
                  fix_z: bool = False):
        """Adds a new row to the points table."""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Generate default ID if not provided
        if not point_id:
            point_id = f"P{row + 1}"

        # ID
        self.table.setItem(row, 0, QTableWidgetItem(point_id))

        # Coordinates
        for col, val in enumerate([x, y, z], start=1):
            item = QTableWidgetItem(f"{val:.4f}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, col, item)

        # Checkboxes for fixed coordinates
        for col, checked in enumerate([fix_x, fix_y, fix_z], start=4):
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            checkbox = QCheckBox()
            checkbox.setChecked(checked)
            checkbox_layout.addWidget(checkbox)
            self.table.setCellWidget(row, col, checkbox_widget)

    def remove_selected(self):
        """Removes selected rows."""
        rows = set(item.row() for item in self.table.selectedItems())
        for row in sorted(rows, reverse=True):
            self.table.removeRow(row)

    def load_example(self):
        """Loads a simple example network."""
        self.table.setRowCount(0)

        # Simple triangle example
        example_points = [
            ("P1", 1000.0, 1000.0, 100.0, True, True, True),
            ("P2", 1100.0, 1000.0, 100.0, True, True, True),
            ("P3", 1050.0, 1086.603, 100.0, True, True, True),
            ("P4", 1050.0, 1028.868, 125.0, False, False, False),
        ]

        for pid, x, y, z, fx, fy, fz in example_points:
            self.add_point(pid, x, y, z, fx, fy, fz)

    def get_points(self) -> list[Point]:
        """Returns all points from the table."""
        points = []
        for row in range(self.table.rowCount()):
            try:
                point_id = self.table.item(row, 0).text()
                x = float(self.table.item(row, 1).text())
                y = float(self.table.item(row, 2).text())
                z = float(self.table.item(row, 3).text())

                fix_x = self.table.cellWidget(row, 4).findChild(QCheckBox).isChecked()
                fix_y = self.table.cellWidget(row, 5).findChild(QCheckBox).isChecked()
                fix_z = self.table.cellWidget(row, 6).findChild(QCheckBox).isChecked()

                points.append(Point(
                    id=point_id, x=x, y=y, z=z,
                    fixed_x=fix_x, fixed_y=fix_y, fixed_z=fix_z
                ))
            except (ValueError, AttributeError) as e:
                print(f"Error reading row {row}: {e}")

        return points

    def get_point_count(self) -> int:
        """Returns the number of points."""
        return self.table.rowCount()


class ObservationsTab(QWidget):
    """Tab for entering and editing observations."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Table for observations
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Typ", "Station", "Ziel", "Messwert", "σ"
        ])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()

        self.btn_add = QPushButton("+ Beobachtung hinzufügen")
        self.btn_add.clicked.connect(self.add_observation)
        button_layout.addWidget(self.btn_add)

        self.btn_remove = QPushButton("- Ausgewählte löschen")
        self.btn_remove.clicked.connect(self.remove_selected)
        button_layout.addWidget(self.btn_remove)

        self.btn_example = QPushButton("Beispiel laden")
        self.btn_example.clicked.connect(self.load_example)
        button_layout.addWidget(self.btn_example)

        button_layout.addStretch()
        layout.addLayout(button_layout)

    def add_observation(self, obs_id: str = "", obs_type: str = "Strecke",
                        station: str = "", target: str = "",
                        value: float = 0.0, std_dev: float = 0.002):
        """Adds a new observation row."""
        row = self.table.rowCount()
        self.table.insertRow(row)

        if not obs_id:
            obs_id = f"B{row + 1}"

        # ID
        self.table.setItem(row, 0, QTableWidgetItem(obs_id))

        # Type dropdown
        type_combo = QComboBox()
        type_combo.addItems(["Strecke", "Richtung", "Zenitwinkel", "Höhenunterschied"])
        type_combo.setCurrentText(obs_type)
        self.table.setCellWidget(row, 1, type_combo)

        # Station and Target
        self.table.setItem(row, 2, QTableWidgetItem(station))
        self.table.setItem(row, 3, QTableWidgetItem(target))

        # Value and StdDev
        value_item = QTableWidgetItem(f"{value:.4f}")
        value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(row, 4, value_item)

        std_item = QTableWidgetItem(f"{std_dev:.4f}")
        std_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(row, 5, std_item)

    def remove_selected(self):
        """Removes selected rows."""
        rows = set(item.row() for item in self.table.selectedItems())
        for row in sorted(rows, reverse=True):
            self.table.removeRow(row)

    def load_example(self):
        """Loads example observations for the tower survey."""
        self.table.setRowCount(0)

        # Example: Tower survey from 3 stations
        # True coordinates: P4 at (1050, 1028.868, 125)
        import numpy as np

        stations = [
            ("P1", 1000.0, 1000.0, 100.0),
            ("P2", 1100.0, 1000.0, 100.0),
            ("P3", 1050.0, 1086.603, 100.0),
        ]
        target = ("P4", 1050.0, 1028.868, 125.0)

        obs_id = 1
        for sta_name, sx, sy, sz in stations:
            tx, ty, tz = target[1], target[2], target[3]

            # Calculate true distance
            dx, dy, dz = tx - sx, ty - sy, tz - sz
            dist = np.sqrt(dx**2 + dy**2 + dz**2)

            # Calculate true zenith angle
            s_horiz = np.sqrt(dx**2 + dy**2)
            zenith = np.arctan2(s_horiz, dz)
            zenith_gon = zenith * 200.0 / np.pi

            # Add distance observation
            self.add_observation(f"D{obs_id}", "Strecke", sta_name, "P4", dist, 0.002)
            obs_id += 1

            # Add zenith observation
            self.add_observation(f"Z{obs_id}", "Zenitwinkel", sta_name, "P4", zenith_gon, 0.02)
            obs_id += 1

    def get_observations(self, network: Network) -> bool:
        """
        Adds all observations from the table to the network.
        Returns True if successful, False otherwise.
        """
        from openadjust.models.distance import DistanceObservation
        from openadjust.models.zenith import ZenithObservation
        from openadjust.models.direction import DirectionObservation
        from openadjust.models.levelling import LevellingObservation
        import numpy as np

        for row in range(self.table.rowCount()):
            try:
                obs_id = self.table.item(row, 0).text()
                obs_type = self.table.cellWidget(row, 1).currentText()
                station = self.table.item(row, 2).text()
                target = self.table.item(row, 3).text()
                value = float(self.table.item(row, 4).text())
                std_dev = float(self.table.item(row, 5).text())

                if obs_type == "Strecke":
                    obs = DistanceObservation(
                        id=obs_id, station=station, target=target,
                        value=value, std_dev=std_dev
                    )
                elif obs_type == "Zenitwinkel":
                    # Convert from gon to radians
                    value_rad = value * np.pi / 200.0
                    std_rad = std_dev * np.pi / 200.0
                    obs = ZenithObservation(
                        id=obs_id, station=station, target=target,
                        value=value_rad, std_dev=std_rad
                    )
                elif obs_type == "Richtung":
                    # Convert from gon to radians
                    value_rad = value * np.pi / 200.0
                    std_rad = std_dev * np.pi / 200.0
                    obs = DirectionObservation(
                        id=obs_id, station=station, target=target,
                        value=value_rad, std_dev=std_rad
                    )
                elif obs_type == "Höhenunterschied":
                    obs = LevellingObservation(
                        id=obs_id, station=station, target=target,
                        value=value, std_dev=std_dev
                    )
                else:
                    print(f"Unknown observation type: {obs_type}")
                    continue

                network.add_observation(obs)

            except (ValueError, AttributeError, KeyError) as e:
                print(f"Error reading observation row {row}: {e}")
                return False

        return True

    def get_observation_count(self) -> int:
        """Returns the number of observations."""
        return self.table.rowCount()


class ResultsTab(QWidget):
    """Tab for displaying adjustment results."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Statistics group
        stats_group = QGroupBox("Statistik")
        stats_layout = QVBoxLayout(stats_group)

        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setFont(QFont("Consolas", 10))
        self.stats_text.setMaximumHeight(150)
        stats_layout.addWidget(self.stats_text)

        layout.addWidget(stats_group)

        # Adjusted coordinates group
        coords_group = QGroupBox("Ausgeglichene Koordinaten")
        coords_layout = QVBoxLayout(coords_group)

        self.coords_table = QTableWidget()
        self.coords_table.setColumnCount(7)
        self.coords_table.setHorizontalHeaderLabels([
            "ID", "X [m]", "Y [m]", "Z [m]", "σX [mm]", "σY [mm]", "σZ [mm]"
        ])

        header = self.coords_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        coords_layout.addWidget(self.coords_table)
        layout.addWidget(coords_group)

        # Residuals group
        residuals_group = QGroupBox("Verbesserungen")
        residuals_layout = QVBoxLayout(residuals_group)

        self.residuals_table = QTableWidget()
        self.residuals_table.setColumnCount(5)
        self.residuals_table.setHorizontalHeaderLabels([
            "ID", "Typ", "Station→Ziel", "v", "v/σ"
        ])

        header = self.residuals_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        residuals_layout.addWidget(self.residuals_table)
        layout.addWidget(residuals_group)

    def display_results(self, result, network: Network):
        """Displays the adjustment results."""
        # Statistics
        stats = f"""Ausgleichung {'konvergiert' if result.converged else 'NICHT konvergiert'}
Iterationen: {result.iterations}
Redundanz: {result.redundancy}
σ₀ (a posteriori): {result.sigma_0:.4f}
vPv: {result.vPv:.6f}

Globaler Modelltest (α=0.05):
  Testgröße: {result.test_statistic:.2f}
  Kritischer Bereich: [{result.test_critical_lower:.2f}, {result.test_critical_upper:.2f}]
  Test bestanden: {'✓ Ja' if result.test_passed else '✗ Nein'}
"""
        self.stats_text.setText(stats)

        # Adjusted coordinates
        self.coords_table.setRowCount(0)
        for point_id, (x, y, z) in result.adjusted_coords.items():
            row = self.coords_table.rowCount()
            self.coords_table.insertRow(row)

            self.coords_table.setItem(row, 0, QTableWidgetItem(point_id))
            self.coords_table.setItem(row, 1, QTableWidgetItem(f"{x:.4f}"))
            self.coords_table.setItem(row, 2, QTableWidgetItem(f"{y:.4f}"))
            self.coords_table.setItem(row, 3, QTableWidgetItem(f"{z:.4f}"))

            # Standard deviations
            stds = result.get_point_std(point_id)
            if stds:
                sx, sy, sz = stds
                self.coords_table.setItem(row, 4, QTableWidgetItem(f"{sx*1000:.2f}"))
                self.coords_table.setItem(row, 5, QTableWidgetItem(f"{sy*1000:.2f}"))
                self.coords_table.setItem(row, 6, QTableWidgetItem(f"{sz*1000:.2f}"))
            else:
                self.coords_table.setItem(row, 4, QTableWidgetItem("—"))
                self.coords_table.setItem(row, 5, QTableWidgetItem("—"))
                self.coords_table.setItem(row, 6, QTableWidgetItem("—"))

        # Residuals
        self.residuals_table.setRowCount(0)
        if result.residuals is not None:
            observations = network.get_enabled_observations()
            for i, obs in enumerate(observations):
                row = self.residuals_table.rowCount()
                self.residuals_table.insertRow(row)

                self.residuals_table.setItem(row, 0, QTableWidgetItem(obs.id))
                self.residuals_table.setItem(row, 1, QTableWidgetItem(obs.get_observation_type()))
                self.residuals_table.setItem(row, 2, QTableWidgetItem(f"{obs.station}→{obs.target}"))

                v = result.residuals[i]
                # Display in appropriate units
                if obs.get_observation_type() in ["direction", "zenith"]:
                    v_display = f"{v * 200/3.14159:.4f} gon"
                else:
                    v_display = f"{v*1000:.2f} mm"

                self.residuals_table.setItem(row, 3, QTableWidgetItem(v_display))

                # Normalized residual
                w = result.get_normalized_residual(i)
                if w is not None:
                    self.residuals_table.setItem(row, 4, QTableWidgetItem(f"{w:.2f}"))
                else:
                    self.residuals_table.setItem(row, 4, QTableWidgetItem("—"))


class MainWindow(QMainWindow):
    """Main window of OpenAdjust."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenAdjust v0.1.0")
        self.setMinimumSize(900, 700)

        self.network = None

        self.setup_ui()
        self.setup_menu()
        self.setup_statusbar()

    def setup_ui(self):
        """Sets up the main UI components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Tab widget
        self.tabs = QTabWidget()

        self.points_tab = PointsTab()
        self.observations_tab = ObservationsTab()
        self.results_tab = ResultsTab()

        self.tabs.addTab(self.points_tab, "Punkte")
        self.tabs.addTab(self.observations_tab, "Beobachtungen")
        self.tabs.addTab(self.results_tab, "Ergebnisse")

        layout.addWidget(self.tabs)

        # Adjustment button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.btn_apriori = QPushButton("A-priori Analyse")
        self.btn_apriori.clicked.connect(self.run_apriori)
        button_layout.addWidget(self.btn_apriori)

        self.btn_adjust = QPushButton("Ausgleichung durchführen")
        self.btn_adjust.setStyleSheet("font-weight: bold; padding: 10px 20px;")
        self.btn_adjust.clicked.connect(self.run_adjustment)
        button_layout.addWidget(self.btn_adjust)

        button_layout.addStretch()
        layout.addLayout(button_layout)

    def setup_menu(self):
        """Sets up the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&Datei")

        new_action = QAction("&Neu", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)

        file_menu.addSeparator()

        exit_action = QAction("&Beenden", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = menubar.addMenu("&Hilfe")

        about_action = QAction("&Über OpenAdjust", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_statusbar(self):
        """Sets up the status bar."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.update_statusbar()

    def update_statusbar(self):
        """Updates the status bar with current counts."""
        n_points = self.points_tab.get_point_count()
        n_obs = self.observations_tab.get_observation_count()
        self.statusbar.showMessage(f"Punkte: {n_points} | Beobachtungen: {n_obs}")

    def new_project(self):
        """Creates a new empty project."""
        self.points_tab.table.setRowCount(0)
        self.observations_tab.table.setRowCount(0)
        self.results_tab.stats_text.clear()
        self.results_tab.coords_table.setRowCount(0)
        self.results_tab.residuals_table.setRowCount(0)
        self.network = None
        self.update_statusbar()

    def build_network(self) -> Optional[Network]:
        """Builds a Network object from the GUI data."""
        network = Network(name="GUI Network")

        # Add points
        points = self.points_tab.get_points()
        if not points:
            QMessageBox.warning(self, "Fehler", "Keine Punkte definiert!")
            return None

        for point in points:
            try:
                network.add_point(point)
            except ValueError as e:
                QMessageBox.warning(self, "Fehler", f"Punkt-Fehler: {e}")
                return None

        # Add observations
        if not self.observations_tab.get_observations(network):
            QMessageBox.warning(self, "Fehler", "Fehler beim Lesen der Beobachtungen!")
            return None

        if not network.observations:
            QMessageBox.warning(self, "Fehler", "Keine Beobachtungen definiert!")
            return None

        return network

    def run_apriori(self):
        """Runs a-priori analysis."""
        network = self.build_network()
        if not network:
            return

        try:
            result = run_apriori_analysis(network)
            self.results_tab.display_results(result, network)
            self.tabs.setCurrentIndex(2)  # Switch to results tab
            self.statusbar.showMessage("A-priori Analyse abgeschlossen")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"A-priori Analyse fehlgeschlagen:\n{e}")

    def run_adjustment(self):
        """Runs the full adjustment."""
        network = self.build_network()
        if not network:
            return

        self.network = network

        try:
            adj = LeastSquaresAdjustment(
                network,
                max_iterations=10,
                convergence_threshold=1e-10,
                verbose=False
            )
            result = adj.run()

            self.results_tab.display_results(result, network)
            self.tabs.setCurrentIndex(2)  # Switch to results tab

            if result.converged:
                self.statusbar.showMessage(
                    f"Ausgleichung konvergiert in {result.iterations} Iterationen | σ₀ = {result.sigma_0:.4f}"
                )
            else:
                self.statusbar.showMessage("Ausgleichung NICHT konvergiert!")

        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Ausgleichung fehlgeschlagen:\n{e}")

    def show_about(self):
        """Shows the about dialog."""
        QMessageBox.about(
            self,
            "Über OpenAdjust",
            """<h2>OpenAdjust v0.1.0</h2>
            <p>Educational Geodetic Network Adjustment Software</p>
            <p>Entwickelt für die Lehre der Ausgleichungsrechnung.</p>
            <p><b>Unterstützte Beobachtungstypen:</b></p>
            <ul>
                <li>Strecken (2D/3D)</li>
                <li>Zenitwinkel</li>
                <li>Horizontalrichtungen</li>
                <li>Höhenunterschiede</li>
            </ul>
            <p>Lizenz: GPL v3</p>
            """
        )


def run_application() -> int:
    """Starts the Qt application."""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(run_application())
