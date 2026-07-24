"""
Controller Wrapper Configuration GUI (gui_qt.py)
PySide6 (Qt 6) Next-Generation Main GUI Window.
Features 6 core tabs (Dashboard, Remapping, Tuning, Advanced, Utilities, Customization),
sub-pixel 240Hz vector stick radar visualizers, 7 theme color presets, high-DPI scaling,
and native Win32 single instance guard.
"""

import sys
import os
import argparse
import configparser
import threading
import time

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget,
    QStackedWidget, QLabel, QFrame
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QIcon

from single_instance import ensure_single_instance
from styles.theme_manager import ThemeManager
from views.dashboard_view import DashboardView
from views.remapping_view import RemappingView
from views.tuning_view import TuningView
from views.advanced_view import AdvancedView
from views.utilities_view import UtilitiesView
from views.customization_view import CustomizationView


class MainWindow(QMainWindow):
    """
    Main PySide6 Configuration Window for UR-XD Controller Wrapper.
    """

    state_updated = Signal(object)

    def __init__(self):
        super().__init__()

        # Ensure Single Instance Socket Lock (Port 65433)
        self.lock_socket = ensure_single_instance("gui", 65433)

        self.setWindowTitle("Controller Wrapper Configuration (PySide6 Next-Gen)")
        self.resize(1080, 740)
        self.setMinimumSize(960, 640)

        # Config & Theme Manager
        self.config = configparser.ConfigParser()
        self.config_file = 'config.ini'
        self.load_config()

        self.theme_manager = ThemeManager(self.config_file)
        self.current_state = None

        self.setup_ui()
        self.apply_theme()

        # Connect Signal for State Updates
        self.state_updated.connect(self.on_state_updated)

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                self.config.read(self.config_file, encoding='utf-8')
            except Exception as e:
                print(f"Error loading config.ini: {e}")

    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
        except Exception as e:
            print(f"Error saving config.ini: {e}")

    def apply_theme(self, theme_key=None, font_family=None):
        """Apply dynamic QSS theme and update vector canvas colors."""
        qss = self.theme_manager.generate_qss(theme_key=theme_key, font_family=font_family)
        QApplication.instance().setStyleSheet(qss)

        # Update canvas colors on dashboard
        active_theme = self.theme_manager.get_active_theme()
        if hasattr(self, 'view_dashboard'):
            self.view_dashboard.js_left.set_theme_colors(
                primary_hex=active_theme['primary'],
                glow_hex=active_theme['glow'],
                accent_green_hex=active_theme['accent_green']
            )
            self.view_dashboard.js_right.set_theme_colors(
                primary_hex=active_theme['primary'],
                glow_hex=active_theme['glow'],
                accent_green_hex=active_theme['accent_green']
            )

    def setup_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)

        # 1. Left Sidebar Navigation
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("GlassCard")
        sidebar_frame.setFixedWidth(210)
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(8, 16, 8, 16)
        sidebar_layout.setSpacing(12)

        lbl_brand = QLabel("🎮 UR-XD 2C FIX")
        lbl_brand.setStyleSheet("font-weight: bold; font-size: 16px; color: #f3e8ff; padding-left: 8px;")
        sidebar_layout.addWidget(lbl_brand)

        self.sidebar_nav = QListWidget()
        self.sidebar_nav.setObjectName("SidebarNav")
        self.sidebar_nav.addItems([
            "📊 Dashboard",
            "🎮 Remapping",
            "🎯 Tuning",
            "⚙️ Advanced",
            "🛠️ Utilities",
            "🎨 Customization"
        ])
        self.sidebar_nav.setCurrentRow(0)
        self.sidebar_nav.currentRowChanged.connect(self.on_tab_changed)

        sidebar_layout.addWidget(self.sidebar_nav)
        sidebar_layout.addStretch()

        lbl_ver = QLabel("PySide6 v2.3-Revamp")
        lbl_ver.setStyleSheet("color: #a992cb; font-size: 11px; padding-left: 8px;")
        sidebar_layout.addWidget(lbl_ver)

        root_layout.addWidget(sidebar_frame)

        # 2. Main Stacked Views (6 Core Tabs)
        self.stacked_views = QStackedWidget()

        self.view_dashboard = DashboardView(self)
        self.view_remapping = RemappingView(self)
        self.view_tuning = TuningView(self)
        self.view_advanced = AdvancedView(self)
        self.view_utilities = UtilitiesView(self)
        self.view_customization = CustomizationView(self)

        self.stacked_views.addWidget(self.view_dashboard)
        self.stacked_views.addWidget(self.view_remapping)
        self.stacked_views.addWidget(self.view_tuning)
        self.stacked_views.addWidget(self.view_advanced)
        self.stacked_views.addWidget(self.view_utilities)
        self.stacked_views.addWidget(self.view_customization)

        root_layout.addWidget(self.stacked_views)

    def on_tab_changed(self, index):
        self.stacked_views.setCurrentIndex(index)

    def on_state_updated(self, state):
        self.current_state = state
        self.view_dashboard.update_state(state)


def main():
    # Enable High DPI Scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
