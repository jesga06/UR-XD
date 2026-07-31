"""
Native GUI Calibration Wizard Dialog (calibration_wizard_dialog.py)
PySide6 native multi-step calibration wizard.
Guides users through 15-second XInput auto-detection, rest state baselining,
real-time HID report byte/bitmask button detection, analog stick range tracking,
and profile saving.
"""

import os
import sys
import json
import time
import ctypes
import configparser
import threading
from typing import Dict, Any, Optional, List, Tuple

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar,
    QStackedWidget, QWidget, QComboBox, QFrame, QGroupBox, QFormLayout
)
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt, QTimer, Signal, Slot

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from hid_reader import HIDReader, RawHIDReport
from backend_xinput import XInputBackend, XINPUT_STATE, XINPUT_GAMEPAD_A, XINPUT_GAMEPAD_B
from gui_v2.services.theme_manager import ThemeManager, color_to_rgba_str, color_to_hex6


BUTTON_TARGET_MAPS = {
    "xbox": [
        ("a", "Action Button A (Bottom)"),
        ("b", "Action Button B (Right)"),
        ("x", "Action Button X (Left)"),
        ("y", "Action Button Y (Top)"),
        ("lb", "Left Bumper (LB)"),
        ("rb", "Right Bumper (RB)"),
        ("select", "Select / Back Button"),
        ("start", "Start Button"),
        ("home", "Home / Guide Button"),
        ("l3", "Left Stick Click (LS / L3)"),
        ("r3", "Right Stick Click (RS / R3)")
    ],
    "playstation": [
        ("a", "Cross (X) Button (Bottom)"),
        ("b", "Circle (O) Button (Right)"),
        ("x", "Square (■) Button (Left)"),
        ("y", "Triangle (▲) Button (Top)"),
        ("lb", "L1 Bumper"),
        ("rb", "R1 Bumper"),
        ("select", "Share / Select Button"),
        ("start", "Options / Start Button"),
        ("home", "PS / Home Button"),
        ("l3", "L3 Click"),
        ("r3", "R3 Click")
    ],
    "nintendo": [
        ("a", "Button B (Bottom)"),
        ("b", "Button A (Right)"),
        ("x", "Button Y (Left)"),
        ("y", "Button X (Top)"),
        ("lb", "L Bumper"),
        ("rb", "R Bumper"),
        ("select", "- (Minus) Button"),
        ("start", "+ (Plus) Button"),
        ("home", "Home Button"),
        ("l3", "LS Click"),
        ("r3", "RS Click")
    ]
}

AXIS_TARGETS = [
    ("lx", "Move Left Stick RIGHT"),
    ("ly", "Move Left Stick UP"),
    ("rx", "Move Right Stick RIGHT"),
    ("ry", "Move Right Stick UP"),
    ("lt", "Press Left Trigger"),
    ("rt", "Press Right Trigger")
]


class NativeCalibrationWizardDialog(QDialog):
    """
    Multi-step PySide6 GUI Calibration Wizard Dialog.
    Step 0: XInput Auto-Detect (15s Countdown + Skip Button)
    Step 1: Welcome & Layout Selection
    Step 2: Rest State Baseline Capture
    Step 3: Interactive Button Byte/Bitmask Mapping
    Step 4: Analog Stick & Trigger Range Calibration
    Step 5: Save & Finish
    """
    calibration_complete = Signal(str)  # Emits path to saved profile JSON
    hid_report_received = Signal(object)  # Thread-safe signal for incoming RawHIDReport

    def __init__(self, device_info: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.device_info = device_info
        self.setWindowTitle("Controller Calibration Wizard")
        self.setMinimumSize(720, 540)

        self.layout_type: str = "xbox"
        self.reader: Optional[HIDReader] = None
        self.latest_report: Optional[RawHIDReport] = None
        self.baselines: Dict[int, List[int]] = {}  # { report_id: byte_list }
        
        self.profile_data: Dict[str, Any] = {
            "name": self.device_info.get("product_string") or "Custom Gamepad",
            "vid": f"{self.device_info.get('vendor_id', 0):04X}",
            "pid": f"{self.device_info.get('product_id', 0):04X}",
            "layout": "xbox",
            "has_report_id": True,
            "reports": {}
        }

        # Step tracking
        self.button_target_idx: int = 0
        self.axis_target_idx: int = 0
        self.axis_min_max: Dict[int, Dict[str, int]] = {}  # { byte_idx: {min, max, base} }

        # XInput Detection 15s Timer
        self.xinput_time_remaining: float = 15.0
        self.xinput_detected: bool = False
        self._xinput_timer = QTimer(self)
        self._xinput_timer.setInterval(50)  # 20Hz polling
        self._xinput_timer.timeout.connect(self._poll_xinput)

        self.hid_report_received.connect(self._on_hid_report_signal)

        self.setup_ui()
        self._setup_theme_sync()
        self._start_hid_listener()

        # Start Step 0 XInput detection immediately
        self._start_xinput_detection()

    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # Header Title
        self.title_label = QLabel("🎮 Hardware Calibration Wizard")
        self.title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        main_layout.addWidget(self.title_label)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 5)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setTextVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Stacked Pages
        self.stacked_widget = QStackedWidget()

        # Page 0: XInput Auto-Detection (15s Poll)
        self.page_xinput = self._create_page_xinput()
        self.stacked_widget.addWidget(self.page_xinput)

        # Page 1: Welcome & Layout Selection
        self.page_welcome = self._create_page_welcome()
        self.stacked_widget.addWidget(self.page_welcome)

        # Page 2: Rest Baseline Capture
        self.page_baseline = self._create_page_baseline()
        self.stacked_widget.addWidget(self.page_baseline)

        # Page 3: Button Calibration
        self.page_buttons = self._create_page_buttons()
        self.stacked_widget.addWidget(self.page_buttons)

        # Page 4: Stick Calibration
        self.page_sticks = self._create_page_sticks()
        self.stacked_widget.addWidget(self.page_sticks)

        # Page 5: Save & Finish Page
        self.page_finish = self._create_page_finish()
        self.stacked_widget.addWidget(self.page_finish)

        main_layout.addWidget(self.stacked_widget)

        # Navigation Footer Buttons
        nav_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        self.back_btn = QPushButton("Back")
        self.back_btn.clicked.connect(self._go_back)
        self.back_btn.setEnabled(False)

        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(self._go_next)

        nav_layout.addWidget(self.cancel_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.back_btn)
        nav_layout.addWidget(self.next_btn)

        main_layout.addLayout(nav_layout)

    def _create_page_xinput(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        title = QLabel("Step 1: XInput Mode Auto-Detection")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        desc = QLabel(
            "If your controller supports XInput (e.g., 8BitDo, GameSir, Xbox mode):\n"
            "Press A + B (or Cross + Circle) together, or switch your physical hardware mode toggle.\n"
            "The wizard is polling XInput constantly."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_xinput_countdown = QLabel("Time Remaining: 15.0s")
        self.lbl_xinput_countdown.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.lbl_xinput_countdown.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_xinput_status = QLabel("Status: Polling XInput C-API...")
        self.lbl_xinput_status.setFont(QFont("Segoe UI", 11))
        self.lbl_xinput_status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_box = QHBoxLayout()
        self.btn_skip_xinput = QPushButton("Skip / DInput Mode")
        self.btn_skip_xinput.clicked.connect(self._skip_xinput_detection)
        
        self.btn_finish_xinput = QPushButton("Finish XInput Setup")
        self.btn_finish_xinput.setVisible(False)
        self.btn_finish_xinput.clicked.connect(self._finish_xinput_mode)

        btn_box.addStretch()
        btn_box.addWidget(self.btn_skip_xinput)
        btn_box.addWidget(self.btn_finish_xinput)
        btn_box.addStretch()

        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addWidget(self.lbl_xinput_countdown)
        layout.addWidget(self.lbl_xinput_status)
        layout.addLayout(btn_box)
        layout.addStretch()
        return page

    def _create_page_welcome(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        info_card = QFrame()
        info_card.setObjectName("wizard_card")
        ic_layout = QFormLayout(info_card)
        ic_layout.addRow("Device Name:", QLabel(self.device_info.get("product_string") or "Generic Gamepad"))
        ic_layout.addRow("Vendor ID (VID):", QLabel(f"0x{self.device_info.get('vendor_id', 0):04X}"))
        ic_layout.addRow("Product ID (PID):", QLabel(f"0x{self.device_info.get('product_id', 0):04X}"))

        layout.addWidget(info_card)

        layout_box = QGroupBox("Select Physical Button Layout")
        lb_layout = QHBoxLayout(layout_box)
        self.combo_layout = QComboBox()
        self.combo_layout.addItems(["Xbox Layout (A, B, X, Y)", "PlayStation Layout (Cross, Circle, Square, Triangle)", "Nintendo Layout (B, A, Y, X)"])
        self.combo_layout.currentIndexChanged.connect(self._on_layout_changed)
        lb_layout.addWidget(self.combo_layout)

        layout.addWidget(layout_box)
        layout.addStretch()
        return page

    def _create_page_baseline(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        self.lbl_baseline = QLabel(
            "Place your controller on a flat surface.\n"
            "Leave all analog sticks, triggers, and buttons in their centered REST state.\n\n"
            "Click 'Capture Rest Baseline' to store rest values."
        )
        self.lbl_baseline.setFont(QFont("Segoe UI", 11))
        self.lbl_baseline.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_capture_base = QPushButton("Capture Rest Baseline")
        self.btn_capture_base.setFixedHeight(36)
        self.btn_capture_base.clicked.connect(self._capture_baseline)

        self.lbl_base_status = QLabel("Status: Waiting for capture...")
        self.lbl_base_status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.lbl_baseline)
        layout.addWidget(self.btn_capture_base, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_base_status)
        layout.addStretch()
        return page

    def _create_page_buttons(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        self.lbl_btn_prompt = QLabel("Press the requested button on your controller:")
        self.lbl_btn_prompt.setFont(QFont("Segoe UI", 11))
        self.lbl_btn_prompt.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_target_btn = QLabel("Press Action Button A (Bottom)")
        self.lbl_target_btn.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.lbl_target_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_btn_status = QLabel("Listening for HID button press...")
        self.lbl_btn_status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_skip_button = QPushButton("Skip Button")
        self.btn_skip_button.clicked.connect(self._skip_current_button)

        layout.addWidget(self.lbl_btn_prompt)
        layout.addWidget(self.lbl_target_btn)
        layout.addWidget(self.lbl_btn_status)
        layout.addWidget(self.btn_skip_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        return page

    def _create_page_sticks(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        self.lbl_stick_prompt = QLabel("Analog Stick & Trigger Calibration")
        self.lbl_stick_prompt.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.lbl_stick_prompt.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_target_axis = QLabel("Move Left Stick RIGHT")
        self.lbl_target_axis.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.lbl_target_axis.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_stick_status = QLabel("Rotate sticks in 360° circles to register range...")
        self.lbl_stick_status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_skip_axis = QPushButton("Skip Axis")
        self.btn_skip_axis.clicked.connect(self._skip_current_axis)

        layout.addWidget(self.lbl_stick_prompt)
        layout.addWidget(self.lbl_target_axis)
        layout.addWidget(self.lbl_stick_status)
        layout.addWidget(self.btn_skip_axis, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        return page

    def _create_page_finish(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        lbl = QLabel("Calibration Complete!")
        lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_summary = QLabel("")
        self.lbl_summary.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(lbl)
        layout.addWidget(self.lbl_summary)
        layout.addStretch()
        return page

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

            bg_glass = color_to_rgba_str(bg_color, alpha_override=0.92)
            border_glass = color_to_rgba_str(accent_1, alpha_override=0.35)

            self.setStyleSheet(f"""
                QDialog {{
                    background-color: {color_to_rgba_str(bg_color, alpha_override=0.95)};
                    color: #ffffff;
                }}
                QFrame#wizard_card {{
                    background-color: {bg_glass};
                    border: 1px solid {border_glass};
                    border-radius: 8px;
                    padding: 12px;
                }}
                QProgressBar {{
                    border: none;
                    background-color: {color_to_rgba_str(accent_1, alpha_override=0.2)};
                    border-radius: 6px;
                }}
                QProgressBar::chunk {{
                    background-color: {color_to_hex6(accent_1)};
                    border-radius: 6px;
                }}
                QPushButton {{
                    background-color: {color_to_rgba_str(accent_1, alpha_override=0.2)};
                    color: {color_to_hex6(accent_1)};
                    border: 1px solid {color_to_rgba_str(accent_1, alpha_override=0.5)};
                    border-radius: 6px;
                    padding: 6px 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {color_to_hex6(accent_1)};
                    color: #ffffff;
                }}
            """)
            self.lbl_target_btn.setStyleSheet(f"color: {color_to_hex6(accent_1)};")
            self.lbl_target_axis.setStyleSheet(f"color: {color_to_hex6(accent_1)};")
            self.lbl_xinput_countdown.setStyleSheet(f"color: {color_to_hex6(accent_2)};")
        except RuntimeError:
            pass

    # -------------------------------------------------------------------
    # HID LISTENER & SIGNAL HANDLING
    # -------------------------------------------------------------------
    def _start_hid_listener(self) -> None:
        path = self.device_info.get("path")
        if path:
            self.reader = HIDReader(device_path=path)
            self.reader.set_callback(lambda r: self.hid_report_received.emit(r))
            if self.reader.connect():
                threading.Thread(target=self.reader.start, daemon=True).start()

    @Slot(object)
    def _on_hid_report_signal(self, report: RawHIDReport) -> None:
        self.latest_report = report
        page_idx = self.stacked_widget.currentIndex()

        # Step 3: Button Calibration
        if page_idx == 3:
            self._process_button_report(report)

        # Step 4: Stick Calibration
        elif page_idx == 4:
            self._process_stick_report(report)

    # -------------------------------------------------------------------
    # STEP 0: XINPUT AUTO-DETECTION (15s COUNTDOWN + CONSTANT POLLING)
    # -------------------------------------------------------------------
    def _start_xinput_detection(self) -> None:
        self.xinput_time_remaining = 15.0
        self.xinput_detected = False
        self._xinput_timer.start()

    def _poll_xinput(self) -> None:
        if self.xinput_detected:
            return

        self.xinput_time_remaining -= 0.05
        if self.xinput_time_remaining <= 0:
            self.xinput_time_remaining = 0
            self._xinput_timer.stop()
            self.lbl_xinput_countdown.setText("Time Remaining: 0.0s")
            self.lbl_xinput_status.setText("⚠️ XInput not detected within 15 seconds. Proceeding to DInput calibration.")
            QTimer.singleShot(1500, self._skip_xinput_detection)
            return

        self.lbl_xinput_countdown.setText(f"Time Remaining: {self.xinput_time_remaining:.1f}s")

        # Check XInput Backend C-API
        xb = XInputBackend()
        if xb.initialize():
            state = XINPUT_STATE()
            if xb.XInputGetState(xb.connected_slot, ctypes.byref(state)) == 0:
                btns = state.Gamepad.wButtons
                # If buttons pressed or active slot connected
                if (btns & XINPUT_GAMEPAD_A) and (btns & XINPUT_GAMEPAD_B) or btns != 0 or xb.connected_slot >= 0:
                    self.xinput_detected = True
                    self._xinput_timer.stop()
                    self.lbl_xinput_countdown.setText("✅ XInput Mode Detected!")
                    self.lbl_xinput_countdown.setStyleSheet("color: #55FF55; font-weight: bold;")
                    self.lbl_xinput_status.setText("Controller successfully responded in XInput mode.")
                    self.btn_skip_xinput.setVisible(False)
                    self.btn_finish_xinput.setVisible(True)

    def _skip_xinput_detection(self) -> None:
        self._xinput_timer.stop()
        self._set_backend_mode("dinput")
        self.stacked_widget.setCurrentIndex(1)
        self.progress_bar.setValue(1)
        self.back_btn.setEnabled(True)

    def _finish_xinput_mode(self) -> None:
        self._xinput_timer.stop()
        self._set_backend_mode("xinput")
        self._save_profile_and_finish()

    def _set_backend_mode(self, mode: str) -> None:
        try:
            config = configparser.ConfigParser()
            if os.path.exists("config.ini"):
                config.read("config.ini")
            if not config.has_section("backend"):
                config.add_section("backend")
            config.set("backend", "mode", mode)
            with open("config.ini", "w") as f:
                config.write(f)
        except Exception as e:
            print(f"Error setting backend mode: {e}")

    # -------------------------------------------------------------------
    # STEP 1: WELCOME & LAYOUT SELECTION
    # -------------------------------------------------------------------
    def _on_layout_changed(self, idx: int) -> None:
        keys = ["xbox", "playstation", "nintendo"]
        self.layout_type = keys[idx] if idx < len(keys) else "xbox"
        self.profile_data["layout"] = self.layout_type
        self._update_button_target_label()

    def _update_button_target_label(self) -> None:
        targets = BUTTON_TARGET_MAPS.get(self.layout_type, BUTTON_TARGET_MAPS["xbox"])
        if self.button_target_idx < len(targets):
            key, label = targets[self.button_target_idx]
            self.lbl_target_btn.setText(f"Press {label}")
            self.lbl_btn_status.setText(f"Listening for '{key.upper()}' input...")

    # -------------------------------------------------------------------
    # STEP 2: REST BASELINE CAPTURE
    # -------------------------------------------------------------------
    def _capture_baseline(self) -> None:
        if self.latest_report and hasattr(self.latest_report, "payload"):
            r_id = self.latest_report.report_id
            self.baselines[r_id] = list(self.latest_report.payload)
            self.lbl_base_status.setText(f"✅ Rest baseline captured for Report ID {r_id} ({len(self.latest_report.payload)} bytes)!")
            self.lbl_base_status.setStyleSheet("color: #55FF55; font-weight: bold;")
        else:
            self.lbl_base_status.setText("⚠️ Default zero baseline registered. Move to next step.")

    # -------------------------------------------------------------------
    # STEP 3: BUTTON BYTE / BITMASK MAPPING
    # -------------------------------------------------------------------
    def _process_button_report(self, report: RawHIDReport) -> None:
        if not self.baselines:
            return

        r_id = report.report_id
        base = self.baselines.get(r_id)
        curr = report.payload
        if not base or len(base) != len(curr):
            return

        targets = BUTTON_TARGET_MAPS.get(self.layout_type, BUTTON_TARGET_MAPS["xbox"])
        if self.button_target_idx >= len(targets):
            return

        # 1. Require Button Release from Previous Mapping
        if getattr(self, "waiting_for_button_release", False):
            if curr == base:
                self.waiting_for_button_release = False
                self.lbl_btn_status.setText("Ready for next button...")
                self.lbl_btn_status.setStyleSheet("")
            return

        # 2. Mandatory Prompt Cooldown (Enforce 800ms reading time for prompt)
        if time.time() - getattr(self, "last_button_prompt_time", 0.0) < 0.8:
            return

        key, _ = targets[self.button_target_idx]

        for b_idx in range(len(curr)):
            # Track value history for noise filtering
            byte_key = (r_id, b_idx)
            if not hasattr(self, "byte_history"):
                self.byte_history = {}
            if byte_key not in self.byte_history:
                self.byte_history[byte_key] = set()
            self.byte_history[byte_key].add(curr[b_idx])

            # Filter out analog noise (if a byte takes > 3 values, it's an analog stick!)
            if len(self.byte_history[byte_key]) > 3:
                continue

            diff = curr[b_idx] ^ base[b_idx]
            if diff > 0:
                # Isolate single bit mask
                if (diff & (diff - 1)) == 0:
                    bitmask = diff

                    # Check if already mapped
                    is_already_mapped = False
                    for r_data in self.profile_data.get("reports", {}).values():
                        for input_cfg in r_data.get("inputs", {}).values():
                            if input_cfg.get("type") == "button" and input_cfg.get("byte") == b_idx and input_cfg.get("bitmask") == bitmask:
                                is_already_mapped = True
                                break

                    if is_already_mapped:
                        continue

                    rep_key = f"report_{r_id}"
                    if rep_key not in self.profile_data["reports"]:
                        self.profile_data["reports"][rep_key] = {"inputs": {}}

                    self.profile_data["reports"][rep_key]["inputs"][key] = {
                        "type": "button",
                        "byte": b_idx,
                        "bitmask": bitmask
                    }

                    self.waiting_for_button_release = True
                    self.lbl_btn_status.setText(f"✅ Mapped '{key.upper()}'! Please RELEASE button to continue...")
                    self.lbl_btn_status.setStyleSheet("color: #55FF55; font-weight: bold;")

                    self.button_target_idx += 1
                    if self.button_target_idx < len(targets):
                        self.last_button_prompt_time = time.time() + 0.8
                        QTimer.singleShot(800, self._update_button_target_label)
                    else:
                        self.lbl_target_btn.setText("✅ All buttons mapped!")
                        self.lbl_btn_status.setText("Click 'Next' to calibrate analog sticks.")
                    break

    def _skip_current_button(self) -> None:
        targets = BUTTON_TARGET_MAPS.get(self.layout_type, BUTTON_TARGET_MAPS["xbox"])
        self.waiting_for_button_release = False
        self.last_button_prompt_time = time.time()
        self.button_target_idx += 1
        if self.button_target_idx < len(targets):
            self._update_button_target_label()
        else:
            self.lbl_target_btn.setText("✅ Button mapping finished!")
            self.lbl_btn_status.setText("Click 'Next' to calibrate analog sticks.")

    # -------------------------------------------------------------------
    # STEP 4: STICK RANGE CALIBRATION
    # -------------------------------------------------------------------
    def _update_axis_target_label(self) -> None:
        if self.axis_target_idx < len(AXIS_TARGETS):
            key, label = AXIS_TARGETS[self.axis_target_idx]
            self.lbl_target_axis.setText(label)
            self.lbl_stick_status.setText(f"Listening for '{key.upper()}' movement...")

    def _process_stick_report(self, report: RawHIDReport) -> None:
        if not self.baselines:
            return

        r_id = report.report_id
        base = self.baselines.get(r_id)
        curr = report.payload
        if not base or len(base) != len(curr):
            return

        if self.axis_target_idx >= len(AXIS_TARGETS):
            return

        # 1. Require Axis Return to Center/Rest from Previous Target
        if getattr(self, "waiting_for_axis_release", False):
            max_dev = max(abs(curr[i] - base[i]) for i in range(len(curr)))
            if max_dev < 15:
                self.waiting_for_axis_release = False
                self.lbl_stick_status.setText("Ready for next axis movement...")
                self.lbl_stick_status.setStyleSheet("")
            return

        # 2. Mandatory Prompt Cooldown (Enforce 1.0s reading time for prompt)
        if time.time() - getattr(self, "last_axis_prompt_time", 0.0) < 1.0:
            return

        key, label = AXIS_TARGETS[self.axis_target_idx]

        for b_idx in range(len(curr)):
            c_val = curr[b_idx]
            b_val = base[b_idx]

            # Exclude bytes already mapped as buttons
            is_mapped_button = False
            for r_data in self.profile_data.get("reports", {}).values():
                for input_cfg in r_data.get("inputs", {}).values():
                    if input_cfg.get("type") == "button" and input_cfg.get("byte") == b_idx:
                        is_mapped_button = True
                        break
            if is_mapped_button:
                continue

            if b_idx not in self.axis_min_max:
                self.axis_min_max[b_idx] = {"min": b_val, "max": b_val, "base": b_val}

            self.axis_min_max[b_idx]["min"] = min(self.axis_min_max[b_idx]["min"], c_val)
            self.axis_min_max[b_idx]["max"] = max(self.axis_min_max[b_idx]["max"], c_val)

            delta = abs(c_val - b_val)
            if delta > 30:
                rep_key = f"report_{r_id}"
                if rep_key not in self.profile_data["reports"]:
                    self.profile_data["reports"][rep_key] = {"inputs": {}}

                mn = self.axis_min_max[b_idx]["min"]
                mx = self.axis_min_max[b_idx]["max"]

                self.profile_data["reports"][rep_key]["inputs"][key] = {
                    "type": "axis",
                    "byte": b_idx,
                    "min": mn,
                    "center": b_val,
                    "max": mx
                }

                self.waiting_for_axis_release = True
                self.lbl_stick_status.setText(f"✅ Mapped '{key.upper()}' to Report {r_id}, Byte {b_idx}! Return stick to center...")
                self.lbl_stick_status.setStyleSheet("color: #55FF55; font-weight: bold;")

                self.axis_target_idx += 1
                if self.axis_target_idx < len(AXIS_TARGETS):
                    self.last_axis_prompt_time = time.time() + 1.0
                    QTimer.singleShot(1000, self._update_axis_target_label)
                else:
                break

    def _skip_current_axis(self) -> None:
        self.axis_target_idx += 1
        if self.axis_target_idx < len(AXIS_TARGETS):
            self._update_axis_target_label()
        else:
            self.lbl_target_axis.setText("✅ Axis calibration finished!")
            self.lbl_stick_status.setText("Click 'Next' to finalize and save profile.")

    # -------------------------------------------------------------------
    # NAVIGATION HANDLERS
    # -------------------------------------------------------------------
    def _go_next(self) -> None:
        idx = self.stacked_widget.currentIndex()

        if idx == 0:
            self._xinput_timer.stop()

        if idx < 5:
            idx += 1
            self.stacked_widget.setCurrentIndex(idx)
            self.progress_bar.setValue(idx)
            self.back_btn.setEnabled(True)

            if idx == 3:
                self._update_button_target_label()
            elif idx == 4:
                self._update_axis_target_label()
            elif idx == 5:
                self.next_btn.setText("Save & Finish")
                vid = self.device_info.get("vendor_id", 0)
                pid = self.device_info.get("product_id", 0)
                self.lbl_summary.setText(f"Profile: profiles/{vid:04X}_{pid:04X}.json\nLayout: {self.layout_type.upper()}")
        else:
            self._save_profile_and_finish()

    def _go_back(self) -> None:
        idx = self.stacked_widget.currentIndex()
        if idx > 0:
            idx -= 1
            self.stacked_widget.setCurrentIndex(idx)
            self.progress_bar.setValue(idx)
            self.next_btn.setText("Next")
            if idx == 0:
                self.back_btn.setEnabled(False)
                self._start_xinput_detection()

    def _save_profile_and_finish(self) -> None:
        self._xinput_timer.stop()
        if self.reader:
            self.reader.stop()

        vid = self.device_info.get("vendor_id", 0)
        pid = self.device_info.get("product_id", 0)
        os.makedirs("profiles", exist_ok=True)
        profile_path = f"profiles/{vid:04X}_{pid:04X}.json".lower()

        try:
            with open(profile_path, "w", encoding="utf-8") as f:
                json.dump(self.profile_data, f, indent=2)
        except Exception as e:
            print(f"Error saving profile: {e}")

        self.calibration_complete.emit(profile_path)
        self.accept()

    def closeEvent(self, event) -> None:
        self._xinput_timer.stop()
        if self.reader:
            self.reader.stop()
        super().closeEvent(event)
