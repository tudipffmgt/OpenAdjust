"""
Network plot widget with error ellipses using matplotlib.

Point symbols according to Pelzer (1985):
- Datum points: filled circle (●) - define datum in free adjustment
- Fixed points: triangle unfilled (△) - variance-free, define datum
- New points: circle unfilled (○) - coordinates to be determined
"""

import numpy as np
from typing import Optional, TYPE_CHECKING

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel, QCheckBox
from PyQt6.QtCore import Qt

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.patches import Ellipse
import matplotlib.pyplot as plt

if TYPE_CHECKING:
    from openadjust.core.network import Network
    from openadjust.core.adjustment import AdjustmentResult

from openadjust.core.error_ellipse import compute_all_error_ellipses, ErrorEllipse


class NetworkPlotWidget(QWidget):
    """Widget for displaying geodetic network with error ellipses."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.network: Optional['Network'] = None
        self.result: Optional['AdjustmentResult'] = None
        self.ellipses: dict[str, ErrorEllipse] = {}
        self.ellipse_scale = 500.0  # Deutlich größerer Startwert!

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Matplotlib figure
        self.figure = Figure(figsize=(10, 8), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        self.toolbar = NavigationToolbar(self.canvas, self)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        # Controls
        controls_layout = QHBoxLayout()

        controls_layout.addWidget(QLabel("Ellipsen-Skalierung:"))

        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setMinimum(1)
        self.scale_slider.setMaximum(200)
        self.scale_slider.setValue(50)  # Startwert in der Mitte
        self.scale_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.scale_slider.valueChanged.connect(self.on_scale_changed)
        controls_layout.addWidget(self.scale_slider)

        self.scale_label = QLabel("1:500")
        self.scale_label.setMinimumWidth(60)
        controls_layout.addWidget(self.scale_label)

        # Checkbox für Ellipsen anzeigen
        self.show_ellipses_cb = QCheckBox("Ellipsen anzeigen")
        self.show_ellipses_cb.setChecked(True)
        self.show_ellipses_cb.stateChanged.connect(self.refresh_plot)
        controls_layout.addWidget(self.show_ellipses_cb)

        controls_layout.addStretch()

        self.btn_refresh = QPushButton("Aktualisieren")
        self.btn_refresh.clicked.connect(self.refresh_plot)
        controls_layout.addWidget(self.btn_refresh)

        layout.addLayout(controls_layout)

        # Legende hinzufügen
        self._add_legend_info(layout)

    def _add_legend_info(self, layout):
        """Fügt eine Legende für Punktsymbole hinzu."""
        legend_layout = QHBoxLayout()
        legend_layout.addWidget(QLabel("Legende:"))
        legend_layout.addWidget(QLabel("△ Festpunkt"))
        legend_layout.addWidget(QLabel("○ Neupunkt"))
        legend_layout.addWidget(QLabel("● Datumspunkt"))
        legend_layout.addStretch()
        layout.addLayout(legend_layout)

    def on_scale_changed(self, value: int):
        """Called when the ellipse scale slider changes."""
        self.scale_label.setText(f"×{value * 10}")
        self.refresh_plot()

    def set_data(self, network: 'Network', result: Optional['AdjustmentResult'] = None):
        self.network = network
        self.result = result

        if result is not None:
            self.ellipses = compute_all_error_ellipses(result)
        else:
            self.ellipses = {}

        self.refresh_plot()

    def refresh_plot(self):
        if self.network is None:
            return

        self.ax.clear()

        self._draw_connections()
        self._draw_ellipses()  # Ellipsen zuerst (hinter den Punkten)
        self._draw_points()

        self._setup_axes()

        self.canvas.draw()

    def _draw_connections(self):
        """Draws lines between observed point pairs."""
        if self.network is None:
            return

        drawn = set()

        for obs in self.network.observations:
            pair = tuple(sorted([obs.station, obs.target]))
            if pair in drawn:
                continue
            drawn.add(pair)

            try:
                p1 = self.network.get_point(obs.station)
                p2 = self.network.get_point(obs.target)

                self.ax.plot([p1.x, p2.x], [p1.y, p2.y],
                            'k-', linewidth=0.5, alpha=0.3, zorder=1)
            except KeyError:
                pass

    def _draw_points(self):
        """
        Draws points with Pelzer symbology:
        - Fixed points (Festpunkte): unfilled triangle △
        - New points (Neupunkte): unfilled circle ○
        - Datum points: filled circle ● (for free adjustment)
        """
        if self.network is None:
            return

        for point_id, point in self.network.points.items():
            is_fixed_xy = point.fixed_x and point.fixed_y

            if is_fixed_xy:
                # Festpunkt: Dreieck (nicht gefüllt) nach Pelzer
                self.ax.plot(point.x, point.y, '^',  # Dreieck nach oben
                            markerfacecolor='white',
                            markeredgecolor='red',
                            markeredgewidth=2,
                            markersize=10,
                            zorder=10)
                self.ax.annotate(point_id, (point.x, point.y),
                                xytext=(5, 5), textcoords='offset points',
                                fontsize=9, fontweight='bold', color='red')
            else:
                # Neupunkt: Kreis (nicht gefüllt) nach Pelzer
                self.ax.plot(point.x, point.y, 'o',
                            markerfacecolor='white',
                            markeredgecolor='blue',
                            markeredgewidth=1.5,
                            markersize=8,
                            zorder=10)
                self.ax.annotate(point_id, (point.x, point.y),
                                xytext=(5, 5), textcoords='offset points',
                                fontsize=8, color='blue')

    def _draw_ellipses(self):
        """Draws error ellipses for points with computed uncertainties."""
        if self.network is None or not self.ellipses:
            return

        if not self.show_ellipses_cb.isChecked():
            return

        # Ellipsen sind in Metern berechnet (A, B in m)
        # Für die Visualisierung: scale konvertiert m zu Plot-Einheiten
        # Ein typischer Wert: sH = 0.002m = 2mm sollte als ~0.5m im Plot erscheinen
        # Also: scale = 0.5 / 0.002 = 250
        # Mit Slider: ellipse_scale = 500 → scale = 1000 / 500 * 250 = 500

        # Einfachere Logik: Slider-Wert direkt als Multiplikator
        # scale_factor = slider_value * 10 (bei slider=50 → scale=500)
        scale_factor = self.scale_slider.value() * 10

        for point_id, ellipse in self.ellipses.items():
            try:
                point = self.network.get_point(point_id)
            except KeyError:
                continue

            # A und B sind in Metern, multipliziere für Sichtbarkeit
            width = 2 * ellipse.A * scale_factor
            height = 2 * ellipse.B * scale_factor

            # Nur zeichnen wenn groß genug
            if width < 0.001 and height < 0.001:
                continue

            ell = Ellipse(
                xy=(point.x, point.y),
                width=width,
                height=height,
                angle=ellipse.phi_deg,
                facecolor='lightgreen',
                edgecolor='darkgreen',
                alpha=0.5,
                linewidth=1.5,
                zorder=5
            )
            self.ax.add_patch(ell)

    def _setup_axes(self):
        self.ax.set_xlabel('X [m]', fontsize=10)
        self.ax.set_ylabel('Y [m]', fontsize=10)

        # Titel mit Ellipsen-Info
        if self.ellipses:
            max_sH = max(e.sH * 1000 for e in self.ellipses.values())
            # Hinweis wenn a-priori Ellipsen (σ₀ ≈ 0 oder σ₀ = 1 gesetzt)
            sigma_hint = ""
            if self.result and self.result.sigma_0 < 0.001:
                sigma_hint = " [a-priori, σ₀=1]"
            self.ax.set_title(f'Netzplot mit Fehlerellipsen (max. sH = {max_sH:.1f} mm){sigma_hint}',
                              fontsize=12, fontweight='bold')
        else:
            self.ax.set_title('Netzplot', fontsize=12, fontweight='bold')

        self.ax.set_aspect('equal')
        self.ax.grid(True, alpha=0.3)

        # Auto-scale with padding
        if self.network and self.network.points:
            xs = [p.x for p in self.network.points.values()]
            ys = [p.y for p in self.network.points.values()]

            x_range = max(xs) - min(xs) if max(xs) != min(xs) else 100
            y_range = max(ys) - min(ys) if max(ys) != min(ys) else 100

            x_margin = x_range * 0.15 + 10
            y_margin = y_range * 0.15 + 10

            self.ax.set_xlim(min(xs) - x_margin, max(xs) + x_margin)
            self.ax.set_ylim(min(ys) - y_margin, max(ys) + y_margin)
