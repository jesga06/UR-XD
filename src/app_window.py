"""
Main Window Frame Shell for PySide6 UI.
Contains the primary QMainWindow container, geometry configuration parsing,
and the tab skeleton setup.
"""

import os
import re
import configparser
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QScrollArea, QLabel
)
from PySide6.QtCore import Qt


class MainWindow(QMainWindow):
    """
    The primary application window for the Ultimate 2C DInput Fix.
    """
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Ultimate 2C DInput Fix")
        self._load_geometry()
        self._setup_tabs()

    def _load_geometry(self) -> None:
        """
        Parses geometry and window dimensions from config.ini ([UI] geometry)
        and applies them to the main window.
        Expected format is the legacy Tkinter format: 'WxH+X+Y' (e.g., '900x700+100+100')
        """
        config = configparser.ConfigParser()
        # Default geometry fallback
        width, height = 900, 700
        x, y = 100, 100
        
        config_path = "config.ini"
        
        if os.path.exists(config_path):
            config.read(config_path, encoding='utf-8')
            if config.has_section("UI") and config.has_option("UI", "geometry"):
                geometry_str = config.get("UI", "geometry")
                # Parse '900x700+100+100' or similar
                match = re.match(r"(\d+)x(\d+)(?:[+-](\d+)[+-](\d+))?", geometry_str)
                if match:
                    groups = match.groups()
                    width = int(groups[0])
                    height = int(groups[1])
                    if groups[2] is not None and groups[3] is not None:
                        x = int(groups[2])
                        y = int(groups[3])
        
        self.setGeometry(x, y, width, height)

    def _setup_tabs(self) -> None:
        """
        Sets up the primary tab bar navigation system containing the 6 main sections.
        Wraps each tab in a scrollable container.
        """
        self.tab_widget = QTabWidget(self)
        self.setCentralWidget(self.tab_widget)
        
        # Define the placeholder tabs required by Phase 2 architecture
        tab_names = [
            "Dashboard",
            "Remapping",
            "Tuning",
            "Advanced",
            "Utilities",
            "Customization"
        ]
        
        for name in tab_names:
            tab = self._create_scrollable_tab(name)
            self.tab_widget.addTab(tab, name)

    def _create_scrollable_tab(self, tab_name: str) -> QScrollArea:
        """
        Creates a QScrollArea wrapping an empty QWidget for a specific tab.
        """
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        # We can apply the glass-card style to the scroll area if desired, but 
        # normally we apply it to inner elements.
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Placeholder text
        placeholder = QLabel(f"[{tab_name} Panel Placeholder]")
        # Force a generic styling to ensure it's visible in deep space theme if needed,
        # but the global QSS handles it.
        placeholder.setStyleSheet("color: rgba(255, 255, 255, 0.4); font-size: 18px;")
        layout.addWidget(placeholder)
        
        scroll_area.setWidget(content_widget)
        return scroll_area

