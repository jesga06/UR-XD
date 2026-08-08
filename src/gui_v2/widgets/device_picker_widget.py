"""
HID Device Picker Widget (device_picker_widget.py)
Provides Disconnected / Waiting View (State A) showing system USB HID devices
and allowing manual device selection for profile assignment or calibration wizard launch.
"""

import sys
import os
from typing import List, Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QPushButton, QGridLayout, QSizePolicy
)
from PySide6.QtGui import QFont, QCursor
from PySide6.QtCore import Qt, Signal, QTimer, Slot, QThread

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from hid_reader import HIDReader
from gui_v2.services.theme_manager import ThemeManager, color_to_rgba_str, color_to_hex6


class DeviceCard(QFrame):
    """
    Individual card representing a connected USB HID device.
    """
    card_clicked = Signal(dict)

    def __init__(self, device_info: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.device_info = device_info
        self.setObjectName("device_card")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setup_ui()
        self._setup_theme_sync()

    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        prod_name = self.device_info.get("product_string") or "Generic USB HID Device"
        vid = self.device_info.get("vendor_id", 0)
        pid = self.device_info.get("product_id", 0)
        iface = self.device_info.get("interface_number", -1)

        self.title_label = QLabel(f"🎮 {prod_name}")
        self.title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))

        info_str = f"VID: {vid:04X} | PID: {pid:04X}"
        if iface != -1:
            info_str += f" | Interface: {iface}"
        
        self.details_label = QLabel(info_str)
        self.details_label.setFont(QFont("JetBrains Mono", 9))

        self.action_btn = QPushButton("Select / Calibrate Controller")
        self.action_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.action_btn.clicked.connect(self._on_click)

        layout.addWidget(self.title_label)
        layout.addWidget(self.details_label)
        layout.addWidget(self.action_btn)

    def _setup_theme_sync(self) -> None:
        try:
            tm = ThemeManager.get_instance()
            tm.theme_changed.connect(self.on_theme_changed)
            self.on_theme_changed(tm.tokens)
        except Exception:
            pass

    @Slot(dict)
    def on_theme_changed(self, tokens: dict) -> None:
        try:
            tm = ThemeManager.get_instance()
            bg_color = tm.get_color("background")
            accent_1 = tm.get_color("accent_1")
            accent_2 = tm.get_color("accent_2")

            bg_glass = color_to_rgba_str(bg_color, alpha_override=0.85)
            border_glass = color_to_rgba_str(accent_1, alpha_override=0.35)

            self.setStyleSheet(f"""
                QFrame#device_card {{
                    background-color: {bg_glass};
                    border: 1px solid {border_glass};
                    border-radius: 10px;
                }}
                QFrame#device_card:hover {{
                    border: 1px solid {color_to_hex6(accent_1)};
                    background-color: {color_to_rgba_str(accent_1, alpha_override=0.15)};
                }}
            """)
            self.title_label.setStyleSheet(f"color: #ffffff;")
            self.details_label.setStyleSheet(f"color: {color_to_hex6(accent_2)};")
            self.action_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color_to_rgba_str(accent_1, alpha_override=0.2)};
                    color: {color_to_hex6(accent_1)};
                    border: 1px solid {color_to_rgba_str(accent_1, alpha_override=0.5)};
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {color_to_hex6(accent_1)};
                    color: #ffffff;
                }}
            """)
        except RuntimeError:
            pass

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_click()
        super().mousePressEvent(event)

    def _on_click(self) -> None:
        self.card_clicked.emit(self.device_info)


class DeviceEnumWorker(QThread):
    devices_found = Signal(list)

    def run(self):
        try:
            devices = HIDReader.get_all_devices()
        except Exception:
            devices = []
        self.devices_found.emit(devices)


class DevicePickerWidget(QWidget):
    """
    State A View Widget: Displays waiting banner and real-time grid of all detected USB HID devices.
    """
    device_selected = Signal(dict)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._last_devices_fingerprint = ""
        self._enum_worker: Optional[DeviceEnumWorker] = None
        self.setup_ui()
        self._setup_theme_sync()

        # Continuous background polling timer for HID device updates (2s interval)
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(2000)
        self._poll_timer.timeout.connect(self.refresh_devices)
        self._poll_timer.start()

        self.refresh_devices()

    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Header Status Card (Capped vertical height per Issue #13)
        self.header_card = QFrame()
        self.header_card.setObjectName("header_card")
        self.header_card.setMaximumHeight(85)
        self.header_card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        header_layout = QVBoxLayout(self.header_card)
        header_layout.setContentsMargins(20, 14, 20, 14)

        self.title = QLabel("No compatible controller connected. Waiting for a controller...")
        self.title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.subtitle = QLabel("Select a detected USB HID device below to link a profile or launch calibration.")
        self.subtitle.setFont(QFont("Segoe UI", 10))
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout.addWidget(self.title)
        header_layout.addWidget(self.subtitle)
        main_layout.addWidget(self.header_card)

        # Scroll area for device grid
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)
        self.grid_layout.setSpacing(12)

        self.scroll.setWidget(self.grid_container)
        main_layout.addWidget(self.scroll)

    def _setup_theme_sync(self) -> None:
        try:
            tm = ThemeManager.get_instance()
            tm.theme_changed.connect(self.on_theme_changed)
            self.on_theme_changed(tm.tokens)
        except Exception:
            pass

    @Slot(dict)
    def on_theme_changed(self, tokens: dict) -> None:
        try:
            tm = ThemeManager.get_instance()
            bg_color = tm.get_color("background")
            accent_1 = tm.get_color("accent_1")
            accent_2 = tm.get_color("accent_2")

            bg_glass = color_to_rgba_str(bg_color, alpha_override=0.85)
            border_glass = color_to_rgba_str(accent_1, alpha_override=0.35)

            self.header_card.setStyleSheet(f"""
                QFrame#header_card {{
                    background-color: {bg_glass};
                    border: 1px solid {border_glass};
                    border-radius: 12px;
                }}
            """)
            self.title.setStyleSheet(f"color: {color_to_hex6(accent_1)};")
            self.subtitle.setStyleSheet(f"color: {color_to_hex6(accent_2)};")
        except RuntimeError:
            pass

    def refresh_devices(self) -> None:
        """Triggers asynchronous non-blocking background HID device enumeration."""
        if self._enum_worker and self._enum_worker.isRunning():
            return
        self._enum_worker = DeviceEnumWorker(self)
        self._enum_worker.devices_found.connect(self._on_devices_enumerated)
        self._enum_worker.start()

    @Slot(list)
    def _on_devices_enumerated(self, devices: list) -> None:
        """Processes enumerated HID devices and updates grid UI on the main thread."""
        fingerprint = str([(d.get("vendor_id"), d.get("product_id"), d.get("path")) for d in devices if isinstance(d, dict)])
        if fingerprint == self._last_devices_fingerprint:
            return
        self._last_devices_fingerprint = fingerprint

        # Clear existing grid items
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        filtered_devices = []
        for d in devices:
            prod = d.get("product_string", "") or ""
            vid = d.get("vendor_id", 0)
            pid = d.get("product_id", 0)

            # Exclude virtual Xbox 360 controller (0x045E:0x028E) spawned by vgamepad
            if vid == 0x045E and pid == 0x028E:
                continue
            # Exclude system keyboards and mice
            if any(kw in prod.upper() for kw in ("KEYBOARD", "MOUSE", "SYSTEM CONTROL")):
                continue
            filtered_devices.append(d)

        if not filtered_devices:
            no_dev_label = QLabel("No USB HID devices currently enumerated.\nPlug in a controller or press any button to awaken the device.")
            no_dev_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_dev_label.setFont(QFont("Segoe UI", 11))
            no_dev_label.setStyleSheet("color: rgba(255, 255, 255, 0.5); padding: 40px;")
            self.grid_layout.addWidget(no_dev_label, 0, 0, 1, 2)
            return

        row, col = 0, 0
        for dev in filtered_devices:
            card = DeviceCard(dev, self)
            card.card_clicked.connect(self.device_selected.emit)
            self.grid_layout.addWidget(card, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1
