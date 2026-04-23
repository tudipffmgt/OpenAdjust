"""
Main application window for OpenAdjust.

Features:
- Tab-based interface (Points, Observations, Results, Network Plot)
- Editable tables for data entry
- Adjustment calculation
- Network visualization with error ellipses
- Interactive glossary with tooltips
"""

import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTableWidget, QTableWidgetItem, QPushButton,
    QLabel, QStatusBar, QMenuBar, QMenu, QMessageBox,
    QHeaderView, QCheckBox, QComboBox, QDoubleSpinBox,
    QGroupBox, QTextEdit, QSplitter, QToolBar, QToolTip
)
from PyQt6.QtCore import Qt, QLocale, QUrl
from PyQt6.QtGui import QAction, QIcon, QFont, QDesktopServices

import numpy as np

from openadjust.core.network import Network
from openadjust.core.point import Point
from openadjust.core.adjustment import LeastSquaresAdjustment, run_apriori_analysis
from openadjust.gui.widgets.network_plot import NetworkPlotWidget
from openadjust.gui.dialogs.glossary_dialog import GlossaryDialog
from openadjust.edu.glossary import get_tooltip, GLOSSARY


class ClickableLabel(QLabel):
    """Label that opens glossary on click."""

    def __init__(self, text: str, term_id: str, parent=None):
        super().__init__(text, parent)
        self.term_id = term_id
        # Entfernt: cursor: pointer (nicht in Qt CSS unterstützt)
        self.setStyleSheet("color: #4a86e8; text-decoration: underline;")
        self.setCursor(Qt.CursorShape.PointingHandCursor)  # Das setzt den Cursor korrekt

        tooltip = get_tooltip(term_id)
        if tooltip:
            self.setToolTip(f"{tooltip}\n\nKlicken für Details...")

    def mousePressEvent(self, event):
        dialog = GlossaryDialog(self.window(), self.term_id)
        dialog.exec()


class PointsTab(QWidget):
    """Tab for entering and editing points."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Info label with tooltip
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("Punkte mit Koordinaten eingeben."))
        info_layout.addWidget(ClickableLabel("Was sind Festpunkte?", "fehlerellipse"))
        info_layout.addStretch()
        layout.addLayout(info_layout)

        # Table for points
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "X [m]", "Y [m]", "Z [m]", "Fix X", "Fix Y", "Fix Z"
        ])

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
        row = self.table.rowCount()
        self.table.insertRow(row)

        if not point_id:
            point_id = f"P{row + 1}"

        self.table.setItem(row, 0, QTableWidgetItem(point_id))

        for col, val in enumerate([x, y, z], start=1):
            item = QTableWidgetItem(f"{val:.4f}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, col, item)

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
        rows = set(item.row() for item in self.table.selectedItems())
        for row in sorted(rows, reverse=True):
            self.table.removeRow(row)

    def load_example(self):
        self.table.setRowCount(0)

        example_points = [
            ("P1", 1000.0, 1000.0, 100.0, True, True, True),
            ("P2", 1100.0, 1000.0, 100.0, True, True, True),
            ("P3", 1050.0, 1086.603, 100.0, True, True, True),
            ("P4", 1050.0, 1028.868, 125.0, False, False, False),
        ]

        for pid, x, y, z, fx, fy, fz in example_points:
            self.add_point(pid, x, y, z, fx, fy, fz)

    def get_points(self) -> list[Point]:
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
        return self.table.rowCount()


class ObservationsTab(QWidget):
    """Tab for entering and editing observations."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Info with glossary links
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("Beobachtungen eingeben."))
        info_layout.addWidget(ClickableLabel("Was ist die Gewichtsmatrix?", "gewichtsmatrix"))
        info_layout.addStretch()
        layout.addLayout(info_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Typ", "Station", "Ziel", "Messwert", "σ"
        ])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table)

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
        row = self.table.rowCount()
        self.table.insertRow(row)

        if not obs_id:
            obs_id = f"B{row + 1}"

        self.table.setItem(row, 0, QTableWidgetItem(obs_id))

        type_combo = QComboBox()
        type_combo.addItems(["Strecke", "Richtung", "Zenitwinkel", "Höhenunterschied"])
        type_combo.setCurrentText(obs_type)
        self.table.setCellWidget(row, 1, type_combo)

        self.table.setItem(row, 2, QTableWidgetItem(station))
        self.table.setItem(row, 3, QTableWidgetItem(target))

        value_item = QTableWidgetItem(f"{value:.4f}")
        value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(row, 4, value_item)

        std_item = QTableWidgetItem(f"{std_dev:.4f}")
        std_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(row, 5, std_item)

    def remove_selected(self):
        rows = set(item.row() for item in self.table.selectedItems())
        for row in sorted(rows, reverse=True):
            self.table.removeRow(row)

    def load_example(self):
        self.table.setRowCount(0)

        stations = [
            ("P1", 1000.0, 1000.0, 100.0),
            ("P2", 1100.0, 1000.0, 100.0),
            ("P3", 1050.0, 1086.603, 100.0),
        ]
        target = ("P4", 1050.0, 1028.868, 125.0)

        obs_id = 1
        for sta_name, sx, sy, sz in stations:
            tx, ty, tz = target[1], target[2], target[3]

            dx, dy, dz = tx - sx, ty - sy, tz - sz
            dist = np.sqrt(dx**2 + dy**2 + dz**2)

            s_horiz = np.sqrt(dx**2 + dy**2)
            zenith = np.arctan2(s_horiz, dz)
            zenith_gon = zenith * 200.0 / np.pi

            self.add_observation(f"D{obs_id}", "Strecke", sta_name, "P4", dist, 0.002)
            obs_id += 1

            self.add_observation(f"Z{obs_id}", "Zenitwinkel", sta_name, "P4", zenith_gon, 0.02)
            obs_id += 1

    def get_observations(self, network: Network) -> bool:
        from openadjust.models.distance import DistanceObservation
        from openadjust.models.zenith import ZenithObservation
        from openadjust.models.direction import DirectionObservation
        from openadjust.models.levelling import LevellingObservation

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
                    value_rad = value * np.pi / 200.0
                    std_rad = std_dev * np.pi / 200.0
                    obs = ZenithObservation(
                        id=obs_id, station=station, target=target,
                        value=value_rad, std_dev=std_rad
                    )
                elif obs_type == "Richtung":
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
                    continue

                network.add_observation(obs)

            except (ValueError, AttributeError, KeyError) as e:
                print(f"Error reading observation row {row}: {e}")
                return False

        return True

    def get_observation_count(self) -> int:
        return self.table.rowCount()


class ResultsTab(QWidget):
    """Tab for displaying adjustment results with clickable explanations."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Statistics group with clickable terms
        stats_group = QGroupBox("Statistik")
        stats_layout = QVBoxLayout(stats_group)

        # Clickable labels for terms
        terms_layout = QHBoxLayout()
        terms_layout.addWidget(ClickableLabel("σ₀ (Sigma Null)", "sigma_0"))
        terms_layout.addWidget(QLabel("|"))
        terms_layout.addWidget(ClickableLabel("Globaler Modelltest", "globaltest"))
        terms_layout.addWidget(QLabel("|"))
        terms_layout.addWidget(ClickableLabel("Redundanz", "redundanz"))
        terms_layout.addStretch()
        stats_layout.addLayout(terms_layout)

        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setFont(QFont("Consolas", 10))
        self.stats_text.setMaximumHeight(150)
        stats_layout.addWidget(self.stats_text)

        layout.addWidget(stats_group)

        # Adjusted coordinates group
        coords_group = QGroupBox("Ausgeglichene Koordinaten")
        coords_layout = QVBoxLayout(coords_group)

        coords_info = QHBoxLayout()
        coords_info.addWidget(ClickableLabel("Was ist die Kofaktormatrix?", "qxx_matrix"))
        coords_info.addWidget(QLabel("|"))
        coords_info.addWidget(ClickableLabel("Helmert-Punktlagefehler", "helmert_fehler"))
        coords_info.addStretch()
        coords_layout.addLayout(coords_info)

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

        residuals_info = QHBoxLayout()
        residuals_info.addWidget(ClickableLabel("Was sind Verbesserungen?", "verbesserung"))
        residuals_info.addWidget(QLabel("|"))
        residuals_info.addWidget(ClickableLabel("Ausreißertest", "ausreissertest"))
        residuals_info.addStretch()
        residuals_layout.addLayout(residuals_info)

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

        self.coords_table.setRowCount(0)
        for point_id, (x, y, z) in result.adjusted_coords.items():
            row = self.coords_table.rowCount()
            self.coords_table.insertRow(row)

            self.coords_table.setItem(row, 0, QTableWidgetItem(point_id))
            self.coords_table.setItem(row, 1, QTableWidgetItem(f"{x:.4f}"))
            self.coords_table.setItem(row, 2, QTableWidgetItem(f"{y:.4f}"))
            self.coords_table.setItem(row, 3, QTableWidgetItem(f"{z:.4f}"))

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
                if obs.get_observation_type() in ["direction", "zenith"]:
                    v_display = f"{v * 200/3.14159:.4f} gon"
                else:
                    v_display = f"{v*1000:.2f} mm"

                self.residuals_table.setItem(row, 3, QTableWidgetItem(v_display))

                w = result.get_normalized_residual(i)
                if w is not None:
                    item = QTableWidgetItem(f"{w:.2f}")
                    # Highlight potential outliers
                    if abs(w) > 3:
                        item.setBackground(Qt.GlobalColor.red)
                    elif abs(w) > 2:
                        item.setBackground(Qt.GlobalColor.yellow)
                    self.residuals_table.setItem(row, 4, item)
                else:
                    self.residuals_table.setItem(row, 4, QTableWidgetItem("—"))


class MainWindow(QMainWindow):
    """Main window of OpenAdjust."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenAdjust v0.1.0")
        self.setMinimumSize(1100, 800)

        self.network = None
        self.result = None

        self.setup_ui()
        self.setup_menu()
        self.setup_statusbar()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Tab widget
        self.tabs = QTabWidget()

        self.points_tab = PointsTab()
        self.observations_tab = ObservationsTab()
        self.results_tab = ResultsTab()
        self.plot_tab = NetworkPlotWidget()

        self.tabs.addTab(self.points_tab, "Punkte")
        self.tabs.addTab(self.observations_tab, "Beobachtungen")
        self.tabs.addTab(self.results_tab, "Ergebnisse")
        self.tabs.addTab(self.plot_tab, "Netzplot")

        layout.addWidget(self.tabs)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.btn_apriori = QPushButton("A-priori Analyse")
        self.btn_apriori.setToolTip("Berechnet Genauigkeiten ohne Messwerte (nur Netzgeometrie)")
        self.btn_apriori.clicked.connect(self.run_apriori)
        button_layout.addWidget(self.btn_apriori)

        self.btn_adjust = QPushButton("Ausgleichung durchführen")
        self.btn_adjust.setStyleSheet("font-weight: bold; padding: 10px 20px;")
        self.btn_adjust.setToolTip("Führt die vermittelnde Ausgleichung durch")
        self.btn_adjust.clicked.connect(self.run_adjustment)
        button_layout.addWidget(self.btn_adjust)

        button_layout.addStretch()
        layout.addLayout(button_layout)

    def setup_menu(self):
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

        glossary_action = QAction("&Glossar", self)
        glossary_action.setShortcut("F1")
        glossary_action.triggered.connect(self.show_glossary)
        help_menu.addAction(glossary_action)

        help_menu.addSeparator()

        about_action = QAction("&Über OpenAdjust", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_statusbar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.update_statusbar()

    def update_statusbar(self):
        n_points = self.points_tab.get_point_count()
        n_obs = self.observations_tab.get_observation_count()
        self.statusbar.showMessage(f"Punkte: {n_points} | Beobachtungen: {n_obs}")

    def new_project(self):
        self.points_tab.table.setRowCount(0)
        self.observations_tab.table.setRowCount(0)
        self.results_tab.stats_text.clear()
        self.results_tab.coords_table.setRowCount(0)
        self.results_tab.residuals_table.setRowCount(0)
        self.network = None
        self.result = None
        self.update_statusbar()

    def build_network(self) -> Optional[Network]:
        network = Network(name="GUI Network")

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

        if not self.observations_tab.get_observations(network):
            QMessageBox.warning(self, "Fehler", "Fehler beim Lesen der Beobachtungen!")
            return None

        if not network.observations:
            QMessageBox.warning(self, "Fehler", "Keine Beobachtungen definiert!")
            return None

        return network

    def run_apriori(self):
        network = self.build_network()
        if not network:
            return

        try:
            result = run_apriori_analysis(network)
            self.network = network
            self.result = result

            self.results_tab.display_results(result, network)
            self.plot_tab.set_data(network, result)

            self.tabs.setCurrentIndex(2)
            self.statusbar.showMessage("A-priori Analyse abgeschlossen")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"A-priori Analyse fehlgeschlagen:\n{e}")

    def run_adjustment(self):
        network = self.build_network()
        if not network:
            return

        try:
            adj = LeastSquaresAdjustment(
                network,
                max_iterations=10,
                convergence_threshold=1e-10,
                verbose=False
            )
            result = adj.run()

            self.network = network
            self.result = result

            self.results_tab.display_results(result, network)
            self.plot_tab.set_data(network, result)

            self.tabs.setCurrentIndex(2)

            if result.converged:
                self.statusbar.showMessage(
                    f"Ausgleichung konvergiert in {result.iterations} Iterationen | σ₀ = {result.sigma_0:.4f}"
                )
            else:
                self.statusbar.showMessage("Ausgleichung NICHT konvergiert!")

        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Ausgleichung fehlgeschlagen:\n{e}")

    def show_glossary(self):
        dialog = GlossaryDialog(self)
        dialog.exec()

    def show_about(self):
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
            <p><b>Features:</b></p>
            <ul>
                <li>Netzplot mit Fehlerellipsen</li>
                <li>Interaktives Glossar</li>
                <li>Globaler Modelltest</li>
            </ul>
            <p>Lizenz: GPL v3</p>
            """
        )


def run_application() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(run_application())
