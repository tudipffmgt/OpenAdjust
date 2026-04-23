"""
Glossary dialog with LaTeX formula support using matplotlib mathtext.
"""

import io
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QTextBrowser, QSplitter, QPushButton, QLineEdit, QLabel
)
from PyQt6.QtCore import Qt, QUrl, QByteArray
from PyQt6.QtGui import QFont, QPixmap, QImage

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from matplotlib import mathtext

from openadjust.edu.glossary import GLOSSARY, get_full_explanation, get_related_terms


def latex_to_pixmap(latex: str, fontsize: int = 14, dpi: int = 150) -> QPixmap:
    """
    Renders LaTeX formula to QPixmap using matplotlib mathtext.

    Args:
        latex: LaTeX string (e.g., r"$\sigma_0 = \sqrt{\frac{v^T P v}{r}}$")
        fontsize: Font size in points
        dpi: Resolution

    Returns:
        QPixmap with rendered formula
    """
    fig = plt.figure(figsize=(0.01, 0.01), dpi=dpi)
    fig.patch.set_alpha(0)

    text = fig.text(0, 0, latex, fontsize=fontsize)

    # Get bounding box
    fig.canvas.draw()
    bbox = text.get_window_extent(fig.canvas.get_renderer())

    # Resize figure to fit text
    width = bbox.width / dpi + 0.1
    height = bbox.height / dpi + 0.1
    fig.set_size_inches(width, height)

    # Adjust text position
    text.set_position((0.05, 0.2))

    # Render to buffer
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, transparent=True,
                bbox_inches='tight', pad_inches=0.02)
    plt.close(fig)

    # Convert to QPixmap
    buf.seek(0)
    img = QImage()
    img.loadFromData(QByteArray(buf.getvalue()))
    return QPixmap.fromImage(img)


class GlossaryDialog(QDialog):
    """Dialog displaying the glossary with searchable terms and LaTeX formulas."""

    def __init__(self, parent=None, initial_term: str = None):
        super().__init__(parent)
        self.setWindowTitle("OpenAdjust Glossar - Ausgleichungsrechnung")
        self.setMinimumSize(1000, 700)

        self.setup_ui()
        self.populate_list()

        if initial_term and initial_term in GLOSSARY:
            self.select_term(initial_term)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Suche:"))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Begriff eingeben...")
        self.search_input.textChanged.connect(self.filter_list)
        search_layout.addWidget(self.search_input)

        layout.addLayout(search_layout)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Term list
        self.term_list = QListWidget()
        self.term_list.setMaximumWidth(280)
        self.term_list.currentItemChanged.connect(self.on_term_selected)
        splitter.addWidget(self.term_list)

        # Content browser
        self.content_browser = QTextBrowser()
        self.content_browser.setOpenExternalLinks(True)
        self.content_browser.setFont(QFont("Segoe UI", 11))
        self.content_browser.anchorClicked.connect(self.on_link_clicked)
        splitter.addWidget(self.content_browser)

        splitter.setSizes([280, 720])
        layout.addWidget(splitter)

        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = QPushButton("Schließen")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def populate_list(self):
        self.term_list.clear()

        for term_id, entry in sorted(GLOSSARY.items(), key=lambda x: x[1]["term"]):
            item = QListWidgetItem(entry["term"])
            item.setData(Qt.ItemDataRole.UserRole, term_id)
            self.term_list.addItem(item)

    def filter_list(self, text: str):
        text = text.lower()

        for i in range(self.term_list.count()):
            item = self.term_list.item(i)
            term_id = item.data(Qt.ItemDataRole.UserRole)
            entry = GLOSSARY[term_id]

            matches = (text in entry["term"].lower() or
                      text in entry["short"].lower())

            item.setHidden(not matches)

    def on_term_selected(self, current, previous):
        if current is None:
            return

        term_id = current.data(Qt.ItemDataRole.UserRole)
        self.display_term(term_id)

    def display_term(self, term_id: str):
        if term_id not in GLOSSARY:
            return

        entry = GLOSSARY[term_id]
        html = entry["long"]

        # Add related terms
        related = get_related_terms(term_id)
        if related:
            html += "<h3>Verwandte Begriffe</h3><p>"
            links = []
            for rel_id in related:
                if rel_id in GLOSSARY:
                    rel_term = GLOSSARY[rel_id]["term"]
                    links.append(f'<a href="glossary:{rel_id}">{rel_term}</a>')
            html += " | ".join(links)
            html += "</p>"

        self.content_browser.setHtml(html)

    def on_link_clicked(self, url):
        if url.scheme() == "glossary":
            term_id = url.path()
            self.select_term(term_id)

    def select_term(self, term_id: str):
        for i in range(self.term_list.count()):
            item = self.term_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == term_id:
                self.term_list.setCurrentItem(item)
                break
