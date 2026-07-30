"""
Main Application Window Shell for PySide6 UI (gui_v2).
Provides system tray integration, window state lifecycle management,
non-blocking IPC telemetry worker integration, and debounced configuration saving.
"""

import sys
import ctypes
import os
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, QSystemTrayIcon, QMenu,
    QApplication, QMessageBox
)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt, QEvent, Slot

from single_instance import ensure_single_instance, PORT_GUI
from gui_v2.workers.telemetry_worker import UDPTelemetryWorker
from gui_v2.utils.debounced_saver import DebouncedConfigSaver

from gui_v2.views.dashboard_view import DashboardView
from gui_v2.views.tuning_view import TuningView
from gui_v2.views.remapping_view import RemappingView
from gui_v2.views.customization_view import CustomizationView


def restore_console_window():
    """Restores and focuses the native Windows console window if available."""
    if sys.platform == "win32":
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                SW_RESTORE = 9
                ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception as e:
            print(f"[MainWindow] Console recovery failed: {e}")


class MainWindow(QMainWindow):
    """
    Main PySide6 application window with system tray lifecycle support,
    decoupled 1000Hz IPC telemetry handling, and debounced disk saving.
    """

    def __init__(self, config_manager=None, theme_manager=None, parent=None):
        super().__init__(parent)
        # Ensure single instance GUI guard
        ensure_single_instance("Ultimate-2C-GUI", PORT_GUI)

        self.config = config_manager
        self.theme_mgr = theme_manager

        self.setWindowTitle("8BitDo Ultimate 2C Controller Suite v2.3")
        self.resize(1100, 750)
        self.setMinimumSize(900, 600)

        # Debounced config saver (300ms single-shot)
        self.debounced_saver = DebouncedConfigSaver(
            save_callback=self._do_save_config,
            delay_ms=300,
            parent=self
        )

        # 1000Hz Decoupled Telemetry Worker
        self.telemetry_worker = UDPTelemetryWorker(port=9999, target_fps=144.0, parent=self)

        self.setup_tray_icon()
        self.setup_ui()
        self._connect_signals()

        # Start background telemetry thread
        self.telemetry_worker.start()

    def setup_tray_icon(self):
        """Initializes QSystemTrayIcon with restore, console recovery, and exit actions."""
        self.tray_icon = QSystemTrayIcon(self)
        app_icon = QApplication.style().standardIcon(QApplication.style().SP_ComputerIcon)
        self.setWindowIcon(app_icon)
        self.tray_icon.setIcon(app_icon)

        tray_menu = QMenu(self)

        show_action = QAction("Open GUI", self)
        show_action.triggered.connect(self.restore_window)
        tray_menu.addAction(show_action)

        console_action = QAction("Show Console", self)
        console_action.triggered.connect(restore_console_window)
        tray_menu.addAction(console_action)

        tray_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_icon_activated)
        self.tray_icon.show()

    def setup_ui(self):
        """Builds tabbed view layout container."""
        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(8, 8, 8, 8)

        self.tab_widget = QTabWidget(self)

        # Initialize views
        self.dashboard_view = DashboardView(controller_config=self.config, parent=self)
        self.tuning_view = TuningView(controller_config=self.config, parent=self)
        self.remapping_view = RemappingView(controller_config=self.config, parent=self)
        self.customization_view = CustomizationView(controller_config=self.config, parent=self)

        self.tab_widget.addTab(self.dashboard_view, "Dashboard")
        self.tab_widget.addTab(self.tuning_view, "Tuning")
        self.tab_widget.addTab(self.remapping_view, "Remapping")
        self.tab_widget.addTab(self.customization_view, "Customization")

        layout.addWidget(self.tab_widget)
        self.setCentralWidget(central_widget)

    def _connect_signals(self):
        """Connects worker telemetry signals to dashboard and view slots."""
        self.telemetry_worker.telemetry_updated.connect(self.dashboard_view.update_telemetry)
        if hasattr(self.dashboard_view, "on_telemetry_updated"):
            self.telemetry_worker.telemetry_updated.connect(self.dashboard_view.on_telemetry_updated)

    def _do_save_config(self):
        """Internal callback executed by DebouncedConfigSaver."""
        if self.config and hasattr(self.config, "save"):
            try:
                self.config.save()
            except Exception as e:
                print(f"[MainWindow] Error saving config: {e}")

    def request_config_save(self):
        """Public interface for views to trigger a debounced config save."""
        self.debounced_saver.mark_dirty()

    def _on_tray_icon_activated(self, reason: QSystemTrayIcon.ActivationReason):
        """Restores window on tray icon double click or trigger."""
        if reason in (QSystemTrayIcon.ActivationReason.DoubleClick, QSystemTrayIcon.ActivationReason.Trigger):
            self.restore_window()

    def restore_window(self):
        """Restores and focuses the main application window."""
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def changeEvent(self, event):
        """Intercepts minimize events to minimize to tray without blocking."""
        if event.type() == QEvent.WindowStateChange and self.isMinimized():
            self.hide()
            event.ignore()
        else:
            super().changeEvent(event)

    def closeEvent(self, event):
        """Ensures worker thread is cleanly shut down before exiting."""
        if self.telemetry_worker and self.telemetry_worker.isRunning():
            self.telemetry_worker.stop()
        self.debounced_saver.flush()
        self.tray_icon.hide()
        super().closeEvent(event)

    def quit_application(self):
        """Full application quit action."""
        self.close()
        QApplication.quit()
