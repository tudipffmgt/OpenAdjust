"""
Main application window.
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget


class MainWindow(QMainWindow):
    """Main window of OpenAdjust."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenAdjust v0.1.0")
        self.setMinimumSize(1200, 800)
        
        # Placeholder content
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        label = QLabel("OpenAdjust - Coming Soon!")
        label.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(label)
        
        info_label = QLabel("Educational Geodetic Network Adjustment Software")
        layout.addWidget(info_label)
        
        self.setCentralWidget(central_widget)


def run_application() -> int:
    """Starts the Qt application."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
