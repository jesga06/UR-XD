"""
System Tray Integration for PySide6 UI.
Manages the tray icon, context menu, and visibility toggling.
"""

import ctypes
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QMainWindow
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QRadialGradient, QPen
from PySide6.QtCore import Qt

from theme import ACCENT_NEON

def create_tray_icon() -> QIcon:
    """
    Generates a 64x64 dynamic QIcon with a circular gradient ring
    matching the deep space/purple theme.
    """
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Draw a gradient ring
    gradient = QRadialGradient(32, 32, 32)
    gradient.setColorAt(0, QColor(0, 0, 0, 0)) # Transparent center
    gradient.setColorAt(0.7, QColor(0, 0, 0, 0))
    gradient.setColorAt(0.8, QColor(ACCENT_NEON))
    gradient.setColorAt(1, QColor(0, 0, 0, 0))
    
    painter.setBrush(gradient)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(0, 0, 64, 64)
    
    # Draw a solid inner circle just for some style
    painter.setBrush(QColor(ACCENT_NEON))
    painter.drawEllipse(24, 24, 16, 16)
    
    painter.end()
    
    return QIcon(pixmap)


class TrayManager:
    """
    Manages the QSystemTrayIcon and its lifecycle.
    """
    def __init__(self, main_window: QMainWindow):
        self.main_window = main_window
        self.app = QApplication.instance()
        
        self.tray = QSystemTrayIcon(create_tray_icon(), self.app)
        self.tray.setToolTip("Ultimate 2C DInput Fix")
        
        # Setup Context Menu
        self.menu = QMenu()
        
        self.action_open = self.menu.addAction("Open Config")
        self.action_open.triggered.connect(self._open_config)
        
        self.action_console = self.menu.addAction("Show Console")
        self.action_console.triggered.connect(self._show_console)
        
        self.menu.addSeparator()
        
        self.action_quit = self.menu.addAction("Quit")
        self.action_quit.triggered.connect(self._quit_app)
        
        self.tray.setContextMenu(self.menu)
        
        # Connect double-click to toggle visibility
        self.tray.activated.connect(self._on_tray_activated)
        
        self.tray.show()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """
        Handles double clicks to toggle the main window visibility.
        """
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.main_window.isVisible():
                self.main_window.hide()
            else:
                self._open_config()

    def _open_config(self) -> None:
        """
        Restores and brings the main window to the front.
        """
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()

    def _show_console(self) -> None:
        """
        Uses Windows native ctypes calls to bring the minimized CLI console window to the foreground.
        """
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception as e:
            print(f"[TrayManager] Failed to show console: {e}")

    def _quit_app(self) -> None:
        """
        Gracefully disconnects listeners, removes the tray icon, and exits the application.
        """
        self.tray.activated.disconnect(self._on_tray_activated)
        self.tray.hide()
        if self.app:
            self.app.quit()
