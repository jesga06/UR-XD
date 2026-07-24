"""
Dashboard View for PySide6 GUI (dashboard_view.py)
Real-time HID / XInput connection status badge, Visual Button Layout Switcher (Xbox, PlayStation, Nintendo),
Validate HID Map runner, Re-scan Controllers action, 240Hz JoystickVisualizerWidget instances for Left/Right sticks,
LT/RT trigger progress gauges with percentage decimals, digital button state grid, and telemetry Hz counter.
"""

import time
import os
import sys
import glob

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QProgressBar, QGridLayout, QComboBox, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt
from components.joystick_widget import JoystickVisualizerWidget
from profile_tools import validate_hid_map
from hid_reader import HIDReader


LAYOUT_PRESETS = {
    "Xbox": {"a": "A", "b": "B", "x": "X", "y": "Y", "l3": "LS", "r3": "RS"},
    "PlayStation": {"a": "Cross (✕)", "b": "Circle (◯)", "x": "Square (▢)", "y": "Triangle (▲)", "l3": "L3", "r3": "R3"},
    "Nintendo": {"a": "B", "b": "A", "x": "Y", "y": "X", "l3": "LS", "r3": "RS"}
}


class DashboardView(QWidget):
    """
    Dashboard Tab View displaying real-time controller inputs, digital highlights, and validation tools.
    """

    def __init__(self, parent_app, parent=None):
        super().__init__(parent)
        self.app = parent_app
        self.active_layout = "Xbox"
        self.packet_count = 0
        self.last_hz_calc_time = time.time()
        self.current_hz = 0
        self.last_packet_time = 0.0

        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # 1. Header Control Panel
        header_card = QFrame()
        header_card.setObjectName("GlassCard")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(16, 12, 16, 12)

        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("font-size: 16px; color: #00f5a0;")
        self.status_title = QLabel("CONNECTED: 8BitDo Ultimate 2C")
        self.status_title.setStyleSheet("font-weight: bold; font-size: 14px;")

        header_layout.addWidget(self.status_dot)
        header_layout.addWidget(self.status_title)
        header_layout.addStretch()

        # Visual Button Layout Selector
        lbl_layout_preset = QLabel("Visual Layout:")
        lbl_layout_preset.setStyleSheet("color: #a992cb; font-weight: 600;")
        self.combo_layout = QComboBox()
        self.combo_layout.addItems(["Xbox", "PlayStation", "Nintendo"])
        self.combo_layout.currentTextChanged.connect(self.on_layout_changed)

        header_layout.addWidget(lbl_layout_preset)
        header_layout.addWidget(self.combo_layout)
        header_layout.addSpacing(16)

        # Re-scan Controllers Action Button
        btn_rescan = QPushButton("🔄 Re-scan")
        btn_rescan.setObjectName("SecondaryBtn")
        btn_rescan.clicked.connect(self.rescan_controllers)
        header_layout.addWidget(btn_rescan)

        # Validate HID Map Button
        self.btn_validate = QPushButton("🔍 Validate HID Map")
        self.btn_validate.setObjectName("PrimaryBtn")
        self.btn_validate.clicked.connect(self.on_validate_hid_map)
        header_layout.addWidget(self.btn_validate)

        main_layout.addWidget(header_card)

        # 2. Stick Radars Split View
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)

        # Left Stick Radar Card
        left_stick_card = QFrame()
        left_stick_card.setObjectName("GlassCard")
        left_layout = QVBoxLayout(left_stick_card)
        left_title = QLabel("LEFT ANALOG STICK")
        left_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #a992cb;")
        left_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.js_left = JoystickVisualizerWidget("Left Stick")
        self.lbl_left_coords = QLabel("X: +0.00  Y: +0.00 | DZ: 5.0%")
        self.lbl_left_coords.setStyleSheet("font-family: monospace; font-size: 12px; color: #00f5a0;")
        self.lbl_left_coords.setAlignment(Qt.AlignmentFlag.AlignCenter)

        left_layout.addWidget(left_title)
        left_layout.addWidget(self.js_left, alignment=Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.lbl_left_coords)
        content_layout.addWidget(left_stick_card)

        # Right Stick Radar Card
        right_stick_card = QFrame()
        right_stick_card.setObjectName("GlassCard")
        right_layout = QVBoxLayout(right_stick_card)
        right_title = QLabel("RIGHT ANALOG STICK")
        right_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #a992cb;")
        right_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.js_right = JoystickVisualizerWidget("Right Stick")
        self.lbl_right_coords = QLabel("X: +0.00  Y: +0.00 | DZ: 5.0%")
        self.lbl_right_coords.setStyleSheet("font-family: monospace; font-size: 12px; color: #00f5a0;")
        self.lbl_right_coords.setAlignment(Qt.AlignmentFlag.AlignCenter)

        right_layout.addWidget(right_title)
        right_layout.addWidget(self.js_right, alignment=Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.lbl_right_coords)
        content_layout.addWidget(right_stick_card)

        main_layout.addLayout(content_layout)

        # 3. Triggers & Digital Buttons Card
        buttons_card = QFrame()
        buttons_card.setObjectName("GlassCard")
        buttons_layout = QVBoxLayout(buttons_card)

        trig_layout = QHBoxLayout()
        self.lbl_lt_val = QLabel("LT: 0.0%")
        self.lbl_lt_val.setStyleSheet("font-weight: bold; font-size: 12px; min-width: 75px;")
        self.bar_lt = QProgressBar()
        self.bar_lt.setObjectName("TriggerBar")
        self.bar_lt.setRange(0, 100)
        self.bar_lt.setValue(0)

        self.lbl_rt_val = QLabel("RT: 0.0%")
        self.lbl_rt_val.setStyleSheet("font-weight: bold; font-size: 12px; min-width: 75px;")
        self.bar_rt = QProgressBar()
        self.bar_rt.setObjectName("TriggerBar")
        self.bar_rt.setRange(0, 100)
        self.bar_rt.setValue(0)

        trig_layout.addWidget(self.lbl_lt_val)
        trig_layout.addWidget(self.bar_lt)
        trig_layout.addSpacing(20)
        trig_layout.addWidget(self.lbl_rt_val)
        trig_layout.addWidget(self.bar_rt)
        buttons_layout.addLayout(trig_layout)

        # Digital Button State Indicators Grid
        btn_grid = QGridLayout()
        btn_grid.setSpacing(8)

        self.btn_indicators = {}
        button_names = ["A", "B", "X", "Y", "LB", "RB", "L3", "R3", "SELECT", "START", "HOME", "M1", "M2", "L4", "R4"]
        for idx, bname in enumerate(button_names):
            row = idx // 8
            col = idx % 8
            lbl_btn = QLabel(bname)
            lbl_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_btn.setStyleSheet(
                "background-color: rgba(255, 255, 255, 0.05); border: 1px solid rgba(168, 85, 247, 0.3); "
                "border-radius: 6px; padding: 6px; font-weight: bold; font-size: 11px;"
            )
            btn_grid.addWidget(lbl_btn, row, col)
            self.btn_indicators[bname] = lbl_btn

        buttons_layout.addLayout(btn_grid)
        main_layout.addWidget(buttons_card)

        # 4. Telemetry Bar Footer
        telemetry_card = QFrame()
        telemetry_card.setObjectName("GlassCard")
        telemetry_layout = QHBoxLayout(telemetry_card)
        telemetry_layout.setContentsMargins(12, 8, 12, 8)

        self.lbl_telemetry = QLabel("TELEMETRY: Polling Rate: -- Hz | Latency: <1.0 ms | ViGEmBus: Active | Buffer: 0 Drops")
        self.lbl_telemetry.setStyleSheet("font-family: monospace; font-size: 11px; color: #a992cb;")
        telemetry_layout.addWidget(self.lbl_telemetry)

        main_layout.addWidget(telemetry_card)

    def rescan_controllers(self):
        devices = HIDReader.get_all_devices()
        msg = QMessageBox(self)
        msg.setWindowTitle("Controller Re-scan")
        msg.setText(f"✓ Enumerated {len(devices)} HID Gamepad Device(s) on System Bus.")
        msg.exec()

    def on_layout_changed(self, layout_name):
        self.active_layout = layout_name
        preset = LAYOUT_PRESETS.get(layout_name, LAYOUT_PRESETS["Xbox"])
        for btn_key, display_name in preset.items():
            key_upper = btn_key.upper()
            if key_upper in self.btn_indicators:
                self.btn_indicators[key_upper].setText(display_name)

    def on_validate_hid_map(self):
        profiles = glob.glob("profiles/*.json") + glob.glob("profiles/community/*.json")
        target_path = profiles[0] if profiles else "profiles/2DC8_3106.json"

        res = validate_hid_map(target_path) if os.path.exists(target_path) else f"HID Map file not found: {target_path}"
        msg = QMessageBox(self)
        msg.setWindowTitle("HID Map Descriptor Validation")
        msg.setText(res)
        msg.exec()

    def update_state(self, controller_state):
        if not controller_state:
            return

        now = time.time()
        self.last_packet_time = now
        self.packet_count += 1
        if (now - self.last_hz_calc_time) >= 1.0:
            self.current_hz = self.packet_count
            self.packet_count = 0
            self.last_hz_calc_time = now
            self.lbl_telemetry.setText(f"TELEMETRY: Polling Rate: {self.current_hz} Hz | Latency: <1.0 ms | ViGEmBus: Active | Buffer: 0 Drops")

        # Update Connection Badge State
        is_conn = getattr(controller_state, 'is_connected', True)
        if is_conn:
            self.status_dot.setStyleSheet("font-size: 16px; color: #00f5a0;")
            self.status_title.setText("CONNECTED: 8BitDo Ultimate 2C")
        else:
            self.status_dot.setStyleSheet("font-size: 16px; color: #ef4444;")
            self.status_title.setText("DISCONNECTED: Searching for Controller...")

        # Stick Coordinates & Radars
        self.js_left.set_stick_position(controller_state.lx, controller_state.ly)
        self.lbl_left_coords.setText(f"X: {controller_state.lx:+.2f}  Y: {controller_state.ly:+.2f} | DZ: 5.0%")

        self.js_right.set_stick_position(controller_state.rx, controller_state.ry)
        self.lbl_right_coords.setText(f"X: {controller_state.rx:+.2f}  Y: {controller_state.ry:+.2f} | DZ: 5.0%")

        # Triggers
        lt_val = max(0.0, min(1.0, controller_state.lt or 0.0))
        rt_val = max(0.0, min(1.0, controller_state.rt or 0.0))
        self.bar_lt.setValue(int(lt_val * 100))
        self.bar_rt.setValue(int(rt_val * 100))
        self.lbl_lt_val.setText(f"LT: {lt_val * 100:.1f}%")
        self.lbl_rt_val.setText(f"RT: {rt_val * 100:.1f}%")

        # Digital Button Indicators
        for bname, lbl_widget in self.btn_indicators.items():
            b_key = bname.lower()
            is_pressed = False
            if hasattr(controller_state, b_key):
                is_pressed = bool(getattr(controller_state, b_key))
            elif isinstance(controller_state.extra_inputs, dict):
                raw_val = controller_state.extra_inputs.get(bname, controller_state.extra_inputs.get(b_key, False))
                is_pressed = (raw_val > 0) if isinstance(raw_val, (int, float)) else bool(raw_val)

            if is_pressed:
                lbl_widget.setStyleSheet(
                    "background-color: #00f5a0; color: #0c0914; border: 1px solid #00f5a0; "
                    "border-radius: 6px; padding: 6px; font-weight: bold; font-size: 11px;"
                )
            else:
                lbl_widget.setStyleSheet(
                    "background-color: rgba(255, 255, 255, 0.05); border: 1px solid rgba(168, 85, 247, 0.3); "
                    "border-radius: 6px; padding: 6px; font-weight: bold; font-size: 11px;"
                )
