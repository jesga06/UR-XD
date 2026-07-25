"""
Main Window Frame Shell for PySide6 UI.
Contains the primary QMainWindow container, geometry configuration parsing,
and the tab skeleton setup.
"""

import os
import re
import sys
import configparser
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QScrollArea, QLabel
)
from PySide6.QtCore import Qt

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from gui_v2.views.dashboard_view import DashboardView
from ipc_threads import UDPTelemetryWorker, FilePollerWorker


class MainWindow(QMainWindow):
    """
    The primary application window for UR-XD.
    """
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("UR-XD")
        self.dashboard_view: DashboardView | None = None
        self.udp_worker: UDPTelemetryWorker | None = None
        self.file_worker: FilePollerWorker | None = None

        self._load_geometry()
        self._setup_tabs()
        self._init_ipc_workers()

    def _load_geometry(self) -> None:
        """
        Parses geometry and window dimensions from config.ini ([UI] geometry)
        and applies them to the main window.
        Expected format is the legacy Tkinter format: 'WxH+X+Y' (e.g., '900x700+100+100')
        """
        config = configparser.ConfigParser()
        width, height = 900, 700
        x, y = 100, 100
        
        config_path = "config.ini"
        
        if os.path.exists(config_path):
            config.read(config_path, encoding='utf-8')
            if config.has_section("UI") and config.has_option("UI", "geometry"):
                geometry_str = config.get("UI", "geometry")
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
        """
        self.tab_widget = QTabWidget(self)
        self.setCentralWidget(self.tab_widget)
        
        tab_names = [
            "Dashboard",
            "Remapping",
            "Tuning",
            "Advanced",
            "Utilities",
            "Customization"
        ]
        
        for name in tab_names:
            if name == "Dashboard":
                scroll_area = QScrollArea()
                scroll_area.setWidgetResizable(True)
                self.dashboard_view = DashboardView()
                scroll_area.setWidget(self.dashboard_view)
                self.tab_widget.addTab(scroll_area, name)
            else:
                tab = self._create_scrollable_tab(name)
                self.tab_widget.addTab(tab, name)

    def _create_scrollable_tab(self, tab_name: str) -> QScrollArea:
        """
        Creates a QScrollArea wrapping an empty QWidget for a specific tab.
        """
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        placeholder = QLabel(f"[{tab_name} Panel Placeholder]")
        placeholder.setStyleSheet("color: rgba(255, 255, 255, 0.4); font-size: 18px;")
        layout.addWidget(placeholder)
        
        scroll_area.setWidget(content_widget)
        return scroll_area

    def _init_ipc_workers(self) -> None:
        """
        Initializes and starts background IPC QThread workers.
        Binds signals to the DashboardView slots.
        """
        if not self.dashboard_view:
            return

        self.udp_worker = UDPTelemetryWorker(parent=self)
        self.file_worker = FilePollerWorker(parent=self)

        self.udp_worker.telemetry_received.connect(self.dashboard_view.update_telemetry)
        self.file_worker.status_updated.connect(self.dashboard_view.update_status)
        self.file_worker.diagnostics_updated.connect(self.dashboard_view.update_diagnostics)

        self.udp_worker.start()
        self.file_worker.start()

    def closeEvent(self, event) -> None:
        """
        Cleanly stops QThread workers on window close.
        """
        if self.udp_worker:
            self.udp_worker.stop()
        if self.file_worker:
            self.file_worker.stop()
        super().closeEvent(event)


