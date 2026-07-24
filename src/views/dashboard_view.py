"""
Dashboard View for PySide6 GUI (dashboard_view.py)
Real-time HID / XInput connection status badge, backend mode radio toggles,
240Hz sub-pixel JoystickVisualizerWidget instances for Left/Right sticks,
LT/RT trigger progress gauges, digital button state grid, and telemetry bar.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QRadioButton, QButtonGroup,
    QProgressBar, QGridLayout, QComboBox, QPushButton
)
from PySide6.QtCore import Qt, QTimer
from components.joystick_widget import JoystickVisualizerWidget


class DashboardView(QWidget):
    """
    Dashboard Tab View displaying real-time controller inputs and telemetry.
    """

    def __init__(self, parent_app, parent=None):
        super().__init__(parent)
        self.app = parent_app
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # 1. Header Control Panel (Status Badge, Backend Toggle, Profile Selector)
        header_card = QFrame()
        header_card.setObjectName("GlassCard")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(16, 12, 16, 12)

        # Connection Status Dot & Title
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("font-size: 16px; color: #00f5a0;")
        self.status_title = QLabel("CONNECTED: 8BitDo Ultimate 2C")
        self.status_title.setStyleSheet("font-weight: bold; font-size: 14px;")

        header_layout.addWidget(self.status_dot)
        header_layout.addWidget(self.status_title)
        header_layout.addStretch()

        # Backend Mode Radios
        mode_label = QLabel("Backend Mode:")
        mode_label.setStyleSheet("color: #a992cb; font-weight: 600;")
        self.radio_dinput = QRadioButton("DInput")
        self.radio_xinput = QRadioButton("XInput")
        self.radio_dinput.setChecked(True)

        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.radio_dinput, 0)
        self.mode_group.addButton(self.radio_xinput, 1)

        header_layout.addWidget(mode_label)
        header_layout.addWidget(self.radio_dinput)
        header_layout.addWidget(self.radio_xinput)
        header_layout.addSpacing(20)

        # Profile Manager Dropdown
        profile_label = QLabel("Profile:")
        profile_label.setStyleSheet("color: #a992cb; font-weight: 600;")
        self.combo_profiles = QComboBox()
        self.combo_profiles.addItems(["Default", "Competitive", "Racing", "Chill"])

        self.btn_save_prof = QPushButton("💾")
        self.btn_save_prof.setObjectName("SecondaryBtn")
        self.btn_save_prof.setFixedWidth(36)

        header_layout.addWidget(profile_label)
        header_layout.addWidget(self.combo_profiles)
        header_layout.addWidget(self.btn_save_prof)

        main_layout.addWidget(header_card)

        # 2. Main Content Split View (Analog Sticks Left/Right & Button Matrix)
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

        # Trigger Gauges
        trig_layout = QHBoxLayout()
        lbl_lt = QLabel("LT:")
        lbl_lt.setStyleSheet("font-weight: bold;")
        self.bar_lt = QProgressBar()
        self.bar_lt.setObjectName("TriggerBar")
        self.bar_lt.setRange(0, 100)
        self.bar_lt.setValue(0)

        lbl_rt = QLabel("RT:")
        lbl_rt.setStyleSheet("font-weight: bold;")
        self.bar_rt = QProgressBar()
        self.bar_rt.setObjectName("TriggerBar")
        self.bar_rt.setRange(0, 100)
        self.bar_rt.setValue(0)

        trig_layout.addWidget(lbl_lt)
        trig_layout.addWidget(self.bar_lt)
        trig_layout.addSpacing(20)
        trig_layout.addWidget(lbl_rt)
        trig_layout.addWidget(self.bar_rt)
        buttons_layout.addLayout(trig_layout)

        # Digital Button State Indicators Grid
        btn_grid = QGridLayout()
        btn_grid.setSpacing(8)

        self.btn_indicators = {}
        button_names = ["A", "B", "X", "Y", "LB", "RB", "L3", "R3", "SELECT", "START", "HOME", "M1", "M2"]
        for idx, bname in enumerate(button_names):
            row = idx // 7
            col = idx % 7
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

        self.lbl_telemetry = QLabel("TELEMETRY: Polling Rate: 250 Hz | Latency: <1.0 ms | ViGEmBus: Active | Drops: 0")
        self.lbl_telemetry.setStyleSheet("font-family: monospace; font-size: 11px; color: #a992cb;")
        telemetry_layout.addWidget(self.lbl_telemetry)

        main_layout.addWidget(telemetry_card)

    def update_state(self, controller_state):
        """Update live controls from ControllerState object."""
        if not controller_state:
            return

        # Update Sticks
        self.js_left.set_stick_position(controller_state.lx, controller_state.ly)
        self.lbl_left_coords.setText(f"X: {controller_state.lx:+.2f}  Y: {controller_state.ly:+.2f} | DZ: 5.0%")

        self.js_right.set_stick_position(controller_state.rx, controller_state.ry)
        self.lbl_right_coords.setText(f"X: {controller_state.rx:+.2f}  Y: {controller_state.ry:+.2f} | DZ: 5.0%")

        # Update Triggers
        self.bar_lt.setValue(int((controller_state.lt or 0.0) * 100))
        self.bar_rt.setValue(int((controller_state.rt or 0.0) * 100))
