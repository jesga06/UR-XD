"""
Native GUI Calibration Wizard Dialog (calibration_wizard_dialog.py)
PySide6 native multi-step calibration wizard dialog powered by CalibrationEngine.
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
    QStackedWidget, QWidget, QComboBox, QFrame, QGroupBox, QFormLayout, QLineEdit
)
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt, QTimer, Signal, Slot

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from hid_reader import HIDReader, RawHIDReport
from backend_xinput import XInputBackend, XINPUT_STATE, XINPUT_GAMEPAD_A, XINPUT_GAMEPAD_B
from gui_v2.services.theme_manager import ThemeManager, color_to_rgba_str, color_to_hex6
from gui_v2.services.calibration_engine import CalibrationEngine
from gui_v2.widgets.stick_radar import StickRadarWidget


class NativeCalibrationWizardDialog(QDialog):
    """
    Multi-step PySide6 GUI Calibration Wizard Dialog powered by CalibrationEngine.
    Step 0: XInput Auto-Detect (15s Countdown + Skip Button)
    Step 1: Welcome & Layout Selection + Extra Buttons Entry
    Step 2: Rest State Baseline Capture
    Step 3: Interactive Button & D-Pad Hat Switch Calibration
    Step 4: Analog Stick Range, Inversion, Radar Verification & Trigger Sampling
    Step 5: Save & Finish
    """
    calibration_complete = Signal(str)  # Emits path to saved profile JSON
    hid_report_received = Signal(object)  # Thread-safe signal for incoming RawHIDReport

    def __init__(self, device_info: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.device_info = device_info
        self.setWindowTitle("Controller Calibration Wizard")
        self.setMinimumSize(720, 600)

        self.layout_type: str = "xbox"
        self.reader: Optional[HIDReader] = None
        self.latest_report: Optional[RawHIDReport] = None
        self.report_payloads: Dict[str, List[int]] = {}
        self.current_verify_stick: str = "left"

        # Instantiate CalibrationEngine
        self.engine = CalibrationEngine(device_info=self.device_info, layout_type=self.layout_type)
        self.engine.prompt_changed.connect(self._on_engine_prompt_changed)
        self.engine.status_updated.connect(self._on_engine_status_updated)
        self.engine.calibration_finished.connect(self._on_engine_finished)
        self.engine.stick_position_updated.connect(self._on_stick_position_updated)

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
        lb_layout = QVBoxLayout(layout_box)
        self.combo_layout = QComboBox()
        self.combo_layout.addItems(["Xbox Layout (A, B, X, Y)", "PlayStation Layout (Cross, Circle, Square, Triangle)", "Nintendo Layout (B, A, Y, X)"])
        self.combo_layout.currentIndexChanged.connect(self._on_layout_changed)
        lb_layout.addWidget(self.combo_layout)

        # Extra Buttons Input Field
        extra_box = QGroupBox("Physical Extra Buttons / Paddles (Optional)")
        eb_layout = QFormLayout(extra_box)
        self.ent_extra_buttons = QLineEdit()
        self.ent_extra_buttons.setPlaceholderText("e.g. m1, m2, l4, r4, c, z")
        eb_layout.addRow("Extra Buttons:", self.ent_extra_buttons)
        lb_layout.addWidget(extra_box)

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

        btn_action_box = QHBoxLayout()
        self.btn_undo_button = QPushButton("↩ Undo Last Step")
        self.btn_undo_button.clicked.connect(self.engine.undo_step)
        
        self.btn_skip_button = QPushButton("Skip Step")
        self.btn_skip_button.clicked.connect(self.engine.skip_step)

        btn_action_box.addStretch()
        btn_action_box.addWidget(self.btn_undo_button)
        btn_action_box.addWidget(self.btn_skip_button)
        btn_action_box.addStretch()

        layout.addWidget(self.lbl_btn_prompt)
        layout.addWidget(self.lbl_target_btn)
        layout.addWidget(self.lbl_btn_status)
        layout.addLayout(btn_action_box)
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

        # Embedded Stick Radar for verification steps
        self.stick_radar_container = QWidget()
        radar_box = QHBoxLayout(self.stick_radar_container)
        radar_box.setContentsMargins(0, 0, 0, 0)
        self.stick_radar = StickRadarWidget(title="Stick Telemetry Test")
        self.stick_radar.setFixedSize(180, 180)
        radar_box.addStretch()
        radar_box.addWidget(self.stick_radar)
        radar_box.addStretch()
        self.stick_radar_container.setVisible(False)

        axis_action_box = QHBoxLayout()
        self.btn_undo_axis = QPushButton("↩ Undo Last Step")
        self.btn_undo_axis.clicked.connect(self.engine.undo_step)

        self.btn_skip_axis = QPushButton("Skip Step")
        self.btn_skip_axis.clicked.connect(self.engine.skip_step)

        self.btn_redo_stick = QPushButton("↩ Re-do Left Stick")
        self.btn_redo_stick.setVisible(False)
        self.btn_redo_stick.clicked.connect(self._on_redo_stick_clicked)

        self.btn_confirm_stick = QPushButton("Confirm & Continue")
        self.btn_confirm_stick.setVisible(False)
        self.btn_confirm_stick.clicked.connect(self.engine.confirm_stick)

        axis_action_box.addStretch()
        axis_action_box.addWidget(self.btn_undo_axis)
        axis_action_box.addWidget(self.btn_skip_axis)
        axis_action_box.addWidget(self.btn_redo_stick)
        axis_action_box.addWidget(self.btn_confirm_stick)
        axis_action_box.addStretch()

        layout.addWidget(self.lbl_stick_prompt)
        layout.addWidget(self.lbl_target_axis)
        layout.addWidget(self.lbl_stick_status)
        layout.addWidget(self.stick_radar_container)
        layout.addLayout(axis_action_box)
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
                    background-color: {color_to_hex6(bg_color)};
                    color: #ffffff;
                }}
                QGroupBox {{
                    border: 1px solid {border_glass};
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 10px;
                    font-weight: bold;
                    color: #ffffff;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }}
                QPushButton {{
                    background-color: {color_to_rgba_str(accent_1, alpha_override=0.2)};
                    color: #ffffff;
                    border: 1px solid {border_glass};
                    border-radius: 6px;
                    padding: 6px 14px;
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
    # ENGINE SIGNAL SLOTS
    # -------------------------------------------------------------------
    @Slot(str, str, str, int, int)
    def _on_engine_prompt_changed(self, key: str, cat: str, prompt: str, step_idx: int, total_steps: int) -> None:
        try:
            tm = ThemeManager.get_instance()
            accent_1_hex = color_to_hex6(tm.get_color("accent_1"))
        except Exception:
            accent_1_hex = "#00f0ff"

        is_release = "RELEASE" in prompt.upper()
        prompt_color = "#FFAA00" if is_release else accent_1_hex

        if cat in ("buttons", "stick_clicks"):
            self.lbl_target_btn.setText(prompt)
            self.lbl_target_btn.setStyleSheet(f"color: {prompt_color}; font-size: 18px; font-weight: bold;")
            self.stacked_widget.setCurrentIndex(3)
        elif cat in ("axes", "triggers"):
            self.stick_radar_container.setVisible(False)
            self.btn_redo_stick.setVisible(False)
            self.btn_confirm_stick.setVisible(False)
            self.btn_undo_axis.setVisible(True)
            self.btn_skip_axis.setVisible(True)
            self.lbl_target_axis.setText(prompt)
            self.lbl_target_axis.setStyleSheet(f"color: {prompt_color}; font-size: 18px; font-weight: bold;")
            self.stacked_widget.setCurrentIndex(4)
        elif cat == "verify_stick":
            self.current_verify_stick = "left" if key == "verify_ls" else "right"
            stick_title = f"Verify {self.current_verify_stick.capitalize()} Stick Telemetry"
            self.lbl_target_axis.setText(stick_title)
            self.lbl_target_axis.setStyleSheet("color: #00f0ff; font-size: 18px; font-weight: bold;")
            self.lbl_stick_status.setText("Rotate the stick to verify 360° range and centering on radar below.")
            self.lbl_stick_status.setStyleSheet("color: #55FF55; font-weight: bold;")
            self.stick_radar.title = f"{self.current_verify_stick.capitalize()} Stick"
            self.stick_radar_container.setVisible(True)
            self.btn_redo_stick.setText(f"↩ Re-do {self.current_verify_stick.capitalize()} Stick")
            self.btn_redo_stick.setVisible(True)
            self.btn_confirm_stick.setVisible(True)
            self.btn_undo_axis.setVisible(False)
            self.btn_skip_axis.setVisible(False)
            self.stacked_widget.setCurrentIndex(4)
        elif cat == "hat":
            display_text = prompt if is_release else "Press D-Pad UP (Hat Switch)"
            self.lbl_target_btn.setText(display_text)
            self.lbl_target_btn.setStyleSheet(f"color: {prompt_color}; font-size: 18px; font-weight: bold;")
            self.stacked_widget.setCurrentIndex(3)

    @Slot(str, float, float)
    def _on_stick_position_updated(self, stick_name: str, norm_x: float, norm_y: float) -> None:
        if self.stacked_widget.currentIndex() == 4 and hasattr(self, 'stick_radar'):
            self.stick_radar.update_telemetry(norm_x, norm_y)

    def _on_redo_stick_clicked(self) -> None:
        self.engine.redo_stick(self.current_verify_stick)

    @Slot(str, str)
    def _on_engine_status_updated(self, msg: str, color_hex: str) -> None:
        self.lbl_btn_status.setText(msg)
        self.lbl_btn_status.setStyleSheet(f"color: {color_hex}; font-weight: bold;")
        self.lbl_stick_status.setText(msg)
        self.lbl_stick_status.setStyleSheet(f"color: {color_hex}; font-weight: bold;")

    @Slot(dict)
    def _on_engine_finished(self, profile_data: dict) -> None:
        self.stacked_widget.setCurrentIndex(5)
        self.progress_bar.setValue(5)
        self.next_btn.setText("Save & Finish")
        vid = self.device_info.get("vendor_id", 0)
        pid = self.device_info.get("product_id", 0)
        self.lbl_summary.setText(f"Profile: profiles/{vid:04X}_{pid:04X}.json\nLayout: {self.layout_type.upper()}")

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
        full_id = f"0_{report.report_id}"
        self.report_payloads[full_id] = list(report.payload)

        page_idx = self.stacked_widget.currentIndex()
        if page_idx in (3, 4):
            self.engine.process_report(0, report.report_id, list(report.payload))

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

        xb = XInputBackend()
        if xb.initialize():
            state = XINPUT_STATE()
            if xb.XInputGetState(xb.connected_slot, ctypes.byref(state)) == 0:
                btns = state.Gamepad.wButtons
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
    # STEP 1 & 2: WELCOME & REST BASELINE
    # -------------------------------------------------------------------
    def _on_layout_changed(self, idx: int) -> None:
        keys = ["xbox", "playstation", "nintendo"]
        self.layout_type = keys[idx] if idx < len(keys) else "xbox"

    def _capture_baseline(self) -> None:
        if self.report_payloads:
            self.engine.capture_rest_baseline(self.report_payloads)
            self.lbl_base_status.setText(f"✅ Rest baseline captured for {len(self.report_payloads)} HID interface(s)!")
            self.lbl_base_status.setStyleSheet("color: #55FF55; font-weight: bold;")
        else:
            self.lbl_base_status.setText("⚠️ Default zero baseline registered. Move to next step.")

    # -------------------------------------------------------------------
    # NAVIGATION HANDLERS
    # -------------------------------------------------------------------
    def _go_next(self) -> None:
        idx = self.stacked_widget.currentIndex()

        if idx == 0:
            self._xinput_timer.stop()
        elif idx == 1:
            raw_extra = self.ent_extra_buttons.text().strip().lower()
            extra_names = [x.strip() for x in raw_extra.split(",") if x.strip()] if raw_extra else []
            self.engine.reconfigure(self.layout_type, extra_names)
        elif idx == 2:
            self.engine.start()

        if idx < 5:
            idx += 1
            self.stacked_widget.setCurrentIndex(idx)
            self.progress_bar.setValue(idx)
            self.back_btn.setEnabled(True)
            if idx == 5:
                self.next_btn.setText("Save & Finish")
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
                json.dump(self.engine.profile, f, indent=2)
        except Exception as e:
            print(f"Error saving profile: {e}")

        try:
            config = configparser.ConfigParser()
            if os.path.exists("config.ini"):
                config.read("config.ini")
            if not config.has_section("controller"):
                config.add_section("controller")
            config.set("controller", "last_profile", profile_path)
            with open("config.ini", "w") as f:
                config.write(f)
        except Exception as e:
            print(f"Error updating config.ini last_profile: {e}")

        p = self.parent()
        if p and hasattr(p, "remapping_view") and hasattr(p.remapping_view, "reload_extra_buttons_grid"):
            p.remapping_view.reload_extra_buttons_grid()

        self.calibration_complete.emit(profile_path)
        self.accept()

    def closeEvent(self, event) -> None:
        self._xinput_timer.stop()
        if self.reader:
            self.reader.stop()
        super().closeEvent(event)
