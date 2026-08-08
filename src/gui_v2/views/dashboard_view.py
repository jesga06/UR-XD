"""
Dashboard View Module for PySide6 UI (gui_v2).
Provides dual-state architecture:
- State A (WAITING): Disconnected / Waiting View displaying HID Device Picker.
- State B (CONNECTED): Standard Telemetry Dashboard with Dual Stick Radars, Trigger Bars, Button Matrix, and Hardware Chords.
- Integrated Transition Overlay Engine (opacity cross-fade with vector spinner and quotes).
"""

import sys
import os
import math
import logging
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QApplication, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QStackedWidget,
    QPushButton, QDialog, QSizePolicy
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Slot

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import math_utils
from backend_base import ConnectionState
from gui_v2.widgets.stick_radar import StickRadarWidget
from gui_v2.widgets.trigger_bar import TriggerBarWidget
from gui_v2.widgets.button_matrix import ButtonMatrixWidget
from gui_v2.widgets.device_picker_widget import DevicePickerWidget
from gui_v2.widgets.transition_overlay_widget import TransitionOverlayWidget
from gui_v2.services.auto_calibration_service import ProfileDecisionEngine
from gui_v2.dialogs.calibration_wizard_dialog import NativeCalibrationWizardDialog

logger = logging.getLogger("dashboard_view")


class DashboardView(QWidget):
    """
    Primary live telemetry dashboard view for PySide6 interface.
    Supports dual-state architecture:
      State A: WAITING (HID Device Picker View)
      State B: CONNECTED (Telemetry Dashboard View)
    """
    def __init__(self, controller_config=None, parent=None):
        super().__init__(parent)
        self.controller_config = controller_config
        self.last_active_chord: str = ""
        self._current_state: ConnectionState = ConnectionState.WAITING

        self.decision_engine = ProfileDecisionEngine(self)
        self.decision_engine.profile_resolved.connect(self._on_profile_resolved)
        self.decision_engine.launch_wizard.connect(self._on_launch_wizard)

        self.setup_ui()
        self._sync_config()
        self._setup_theme_sync()

    def setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Container Widget with Stacked Layout & Transition Overlay
        self.container = QWidget(self)
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        self.stacked_widget = QStackedWidget(self.container)

        # State A: WAITING View (Device Picker)
        self.state_a_view = DevicePickerWidget(self)
        self.state_a_view.device_selected.connect(self._on_device_selected)
        self.stacked_widget.addWidget(self.state_a_view)

        # State B: CONNECTED View (Telemetry Dashboard)
        self.state_b_view = self._create_telemetry_view()
        self.stacked_widget.addWidget(self.state_b_view)

        container_layout.addWidget(self.stacked_widget)
        main_layout.addWidget(self.container)

        # Transition Overlay Widget
        self.overlay = TransitionOverlayWidget(self)
        self.overlay.hide()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, 'overlay'):
            self.overlay.setGeometry(self.rect())

    def _create_telemetry_view(self) -> QWidget:
        view = QWidget()
        main_layout = QVBoxLayout(view)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # 1. Header Banner & Connection Status Card (Fixed vertical height per Issue #13)
        self.header_card = QFrame()
        self.header_card.setObjectName("glass_card")
        self.header_card.setMaximumHeight(65)
        self.header_card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        header_layout = QHBoxLayout(self.header_card)
        header_layout.setContentsMargins(14, 10, 14, 10)

        self.status_badge = QLabel("WAITING")
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge.setStyleSheet("""
            background-color: #eab308;
            color: #ffffff;
            font-weight: bold;
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 11px;
        """)

        self.device_label = QLabel("🎮 Waiting for Controller...")
        self.device_label.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: bold;")

        self.btn_selective_calib = QPushButton("🎯 Selective Calibration")
        self.btn_selective_calib.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_selective_calib.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.25);
                border-radius: 6px;
                color: #ffffff;
                padding: 5px 12px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #0ea5e9;
                color: #ffffff;
            }
        """)
        self.btn_selective_calib.clicked.connect(self._on_launch_selective_calibration)

        self.btn_full_wizard = QPushButton("⚙️ Full Wizard")
        self.btn_full_wizard.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_full_wizard.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.25);
                border-radius: 6px;
                color: #ffffff;
                padding: 5px 12px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #3b82f6;
                color: #ffffff;
            }
        """)
        self.btn_full_wizard.clicked.connect(self._on_recalibrate_full_wizard)

        header_layout.addWidget(self.status_badge)
        header_layout.addWidget(self.device_label)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_selective_calib)
        header_layout.addWidget(self.btn_full_wizard)

        main_layout.addWidget(self.header_card)

        # 2. Dual Stick Radars Panel
        radars_layout = QHBoxLayout()
        radars_layout.setSpacing(12)

        # Left Stick Card
        self.left_card = QFrame()
        self.left_card.setObjectName("glass_card")
        left_card_layout = QVBoxLayout(self.left_card)
        left_card_layout.setContentsMargins(12, 10, 12, 10)

        self.left_radar = StickRadarWidget("LEFT STICK RADAR")
        self.left_readout = QLabel("Raw: (+0.00, +0.00) | Tuned: (+0.00, +0.00)")
        self.left_readout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        left_card_layout.addWidget(self.left_radar)
        left_card_layout.addWidget(self.left_readout)

        # Right Stick Card
        self.right_card = QFrame()
        self.right_card.setObjectName("glass_card")
        right_card_layout = QVBoxLayout(self.right_card)
        right_card_layout.setContentsMargins(12, 10, 12, 10)

        self.right_radar = StickRadarWidget("RIGHT STICK RADAR")
        self.right_readout = QLabel("Raw: (+0.00, +0.00) | Tuned: (+0.00, +0.00)")
        self.right_readout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        right_card_layout.addWidget(self.right_radar)
        right_card_layout.addWidget(self.right_readout)

        radars_layout.addWidget(self.left_card)
        radars_layout.addWidget(self.right_card)

        main_layout.addLayout(radars_layout)

        # 3. Analog Triggers Panel
        self.triggers_card = QFrame()
        self.triggers_card.setObjectName("glass_card")
        triggers_layout = QVBoxLayout(self.triggers_card)
        triggers_layout.setContentsMargins(12, 10, 12, 10)

        trig_header = QLabel("ANALOG TRIGGERS")
        trig_header.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-weight: bold; font-size: 10px;")
        triggers_layout.addWidget(trig_header)

        trig_bars_layout = QHBoxLayout()
        trig_bars_layout.setSpacing(12)

        self.lt_bar = TriggerBarWidget("LEFT TRIGGER (LT)")
        self.rt_bar = TriggerBarWidget("RIGHT TRIGGER (RT)")

        trig_bars_layout.addWidget(self.lt_bar)
        trig_bars_layout.addWidget(self.rt_bar)

        triggers_layout.addLayout(trig_bars_layout)

        main_layout.addWidget(self.triggers_card)

        # 4. Controller Button Status Matrix Panel
        self.button_matrix = ButtonMatrixWidget()
        main_layout.addWidget(self.button_matrix)

        # 5. Telemetry Footer Bar
        self.footer_label = QLabel("TELEMETRY FOOTER: Polling Rate: -- Hz | Latency: <1.0 ms")
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.footer_label.setStyleSheet("color: rgba(255, 255, 255, 0.5); font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 10px; padding: 4px;")
        main_layout.addWidget(self.footer_label)

        return view

    def _setup_theme_sync(self) -> None:
        try:
            from gui_v2.services.theme_manager import ThemeManager
            tm = ThemeManager.get_instance()
            tm.theme_changed.connect(self.on_theme_changed)
            self.on_theme_changed(tm.tokens)
        except Exception:
            pass

    @Slot(dict)
    def on_theme_changed(self, tokens: dict):
        try:
            from gui_v2.services.theme_manager import ThemeManager, color_to_rgba_str, color_to_hex6
            tm = ThemeManager.get_instance()
            bg_color = tm.get_color("background")
            accent_1 = tm.get_color("accent_1")
            accent_2 = tm.get_color("accent_2")
            outline = tm.get_color("outline")

            bg_glass = color_to_rgba_str(bg_color, alpha_override=0.85)
            border_glass = color_to_rgba_str(outline, alpha_override=0.35)

            card_style = f"""
                QFrame#glass_card {{
                    background-color: {bg_glass};
                    border: 1px solid {border_glass};
                    border-radius: 12px;
                }}
            """
            for card in [getattr(self, 'header_card', None), getattr(self, 'left_card', None),
                         getattr(self, 'right_card', None), getattr(self, 'triggers_card', None),
                         getattr(self, 'chords_card', None)]:
                if card:
                    card.setStyleSheet(card_style)

            if hasattr(self, 'left_readout'):
                self.left_readout.setStyleSheet(f"color: {color_to_hex6(accent_2)}; font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 11px; font-weight: bold;")
            if hasattr(self, 'right_readout'):
                self.right_readout.setStyleSheet(f"color: {color_to_hex6(accent_2)}; font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 11px; font-weight: bold;")
            if hasattr(self, 'chords_header'):
                self.chords_header.setStyleSheet(f"color: {color_to_hex6(accent_1)}; font-weight: bold; font-size: 10px;")
        except RuntimeError:
            pass

    def set_config(self, controller_config) -> None:
        self.controller_config = controller_config
        self._sync_config()

    def _sync_config(self) -> None:
        if self.controller_config:
            if hasattr(self, 'button_matrix'):
                self.button_matrix.load_profile_schema(self.controller_config)
            ls_dz = float(self.controller_config.get("analog_left", "deadzone", fallback="0.08"))
            rs_dz = float(self.controller_config.get("analog_right", "deadzone", fallback="0.08"))
            if hasattr(self, 'left_radar') and hasattr(self.left_radar, 'set_deadzone'):
                self.left_radar.set_deadzone(ls_dz)
            if hasattr(self, 'right_radar') and hasattr(self.right_radar, 'set_deadzone'):
                self.right_radar.set_deadzone(rs_dz)

    def get_active_device_info(self) -> Optional[dict]:
        """
        Dynamically resolves active controller device info from active state
        or live USB HID enumeration without hardcoding any constants.
        """
        if hasattr(self, "_current_device_info") and self._current_device_info:
            return self._current_device_info

        if hasattr(self, "decision_engine") and getattr(self.decision_engine, "active_device_info", None):
            return self.decision_engine.active_device_info

        # Live USB HID Enumeration
        try:
            from hid_reader import HIDReader
            devices = HIDReader.get_all_devices()
            # Prioritize Gamepad (0x05) / Joystick (0x04) usage pages
            for dev in devices:
                up = dev.get("usage_page", 0)
                u = dev.get("usage", 0)
                if up == 1 and u in (4, 5):
                    self._current_device_info = dev
                    return dev
            # Fallback to any enumerated HID device with product string
            for dev in devices:
                if dev.get("product_string"):
                    self._current_device_info = dev
                    return dev
            if devices:
                self._current_device_info = devices[0]
                return devices[0]
        except Exception as e:
            logger.warning(f"Live HID enumeration failed: {e}")

        return None

    def _on_device_selected(self, device_info: dict) -> None:
        """Triggered when user selects a device card in State A."""
        self._current_device_info = device_info
        if hasattr(self, "decision_engine"):
            self.decision_engine.active_device_info = device_info
        self.overlay.hide()
        self.decision_engine.process_device(device_info, is_xinput=False, force_calibrate=True)

    def _on_profile_resolved(self, profile_path: str) -> None:
        """Profile decision engine resolved a profile."""
        self.overlay.hide()
        self.transition_to_state(ConnectionState.CONNECTED)

    def _on_launch_wizard(self, device_info: dict) -> None:
        """Profile decision engine requested calibration wizard."""
        self._current_device_info = device_info
        if hasattr(self, "decision_engine"):
            self.decision_engine.active_device_info = device_info
        self.overlay.hide()
        dlg = NativeCalibrationWizardDialog(device_info, self)
        dlg.calibration_complete.connect(self._on_profile_resolved)
        dlg.exec()

    def _on_launch_selective_calibration(self) -> None:
        """Launch Selective Calibration Dialog and start partial wizard."""
        device_info = self.get_active_device_info()
        if not device_info:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No Device Detected", "No USB HID controller device was found. Please ensure your controller is connected.")
            return

        vid = device_info.get("vendor_id", 0)
        pid = device_info.get("product_id", 0)
        profile_path = f"profiles/{vid:04X}_{pid:04X}.json".lower()
        existing_profile = {}
        if os.path.exists(profile_path):
            try:
                import json
                with open(profile_path, "r", encoding="utf-8") as f:
                    existing_profile = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read existing profile: {e}")

        from gui_v2.dialogs.selective_calibration_dialog import SelectiveCalibrationDialog
        dlg_select = SelectiveCalibrationDialog(device_info, existing_profile, self)
        if dlg_select.exec() == QDialog.DialogCode.Accepted:
            selected_inputs = dlg_select.selected_inputs
            new_extra = dlg_select.new_extra_buttons

            self.overlay.hide()
            wiz = NativeCalibrationWizardDialog(
                device_info,
                parent=self,
                selected_inputs=selected_inputs,
                new_extra_buttons=new_extra,
                existing_profile=existing_profile
            )
            wiz.calibration_complete.connect(self._on_profile_resolved)
            wiz.exec()

    def _on_recalibrate_full_wizard(self) -> None:
        """Launch Full Calibration Wizard on connected device."""
        device_info = self.get_active_device_info()
        if not device_info:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No Device Detected", "No USB HID controller device was found. Please ensure your controller is connected.")
            return
        self._on_launch_wizard(device_info)

    def transition_to_state(self, state: ConnectionState) -> None:
        """Swaps between State A (WAITING) and State B (CONNECTED) view."""
        if self._current_state != state:
            self._current_state = state
            if state == ConnectionState.CONNECTED:
                self.stacked_widget.setCurrentWidget(self.state_b_view)
            else:
                self.stacked_widget.setCurrentWidget(self.state_a_view)

    @Slot(dict)
    def update_telemetry(self, state: Dict[str, Any]) -> None:
        if not state:
            return

        # Ensure we are displaying State B if receiving active telemetry
        if self._current_state != ConnectionState.CONNECTED:
            self.transition_to_state(ConnectionState.CONNECTED)

        lx = float(state.get("lx", 0.0))
        ly = float(state.get("ly", 0.0))
        rx = float(state.get("rx", 0.0))
        ry = float(state.get("ry", 0.0))

        if self.controller_config:
            cfg_ls = getattr(self.controller_config, 'data', {}).get("analog_left", {})
            ls_dz = float(cfg_ls.get("deadzone", 0.00))
            ls_adz = float(cfg_ls.get("anti_deadzone", 0.00))
            ls_rdz = float(cfg_ls.get("rest_deadzone", 0.00))
            ls_curve = str(cfg_ls.get("curve", "linear"))
            ls_factor = float(cfg_ls.get("exp_factor", 1.00))
            ls_sens = float(cfg_ls.get("sensitivity", 1.00))
            ls_custom = str(cfg_ls.get("custom_eq", cfg_ls.get("custom_curve", "")))
            ls_warp = float(cfg_ls.get("warp_threshold", cfg_ls.get("warped_stick_threshold", 0.00)))
            ls_circ_mode = str(cfg_ls.get("circularity_mode", "disabled")).lower()
            ls_cx = float(cfg_ls.get("circularity_center_x", 0.0))
            ls_cy = float(cfg_ls.get("circularity_center_y", 0.0))
            ls_bounds_str = str(cfg_ls.get("circularity_bounds", ""))
            ls_bounds = [float(x) for x in ls_bounds_str.split(",")] if ls_bounds_str and len(ls_bounds_str.split(",")) == 360 else None

            out_lx, out_ly = math_utils.apply_warped_stick_correction(lx, ly, ls_warp)
            if ls_circ_mode == "before":
                out_lx, out_ly = math_utils.apply_circularity_correction(out_lx, out_ly, ls_cx, ls_cy, ls_bounds)
                out_lx, out_ly = math_utils.process_analog_stick(out_lx, out_ly, ls_dz, ls_adz, ls_curve, ls_factor, ls_rdz, ls_sens, ls_custom)
            elif ls_circ_mode == "after":
                out_lx, out_ly = math_utils.process_analog_stick(out_lx, out_ly, ls_dz, ls_adz, ls_curve, ls_factor, ls_rdz, ls_sens, ls_custom)
                out_lx, out_ly = math_utils.apply_circularity_correction(out_lx, out_ly, ls_cx, ls_cy, ls_bounds)
            else:
                out_lx, out_ly = math_utils.process_analog_stick(out_lx, out_ly, ls_dz, ls_adz, ls_curve, ls_factor, ls_rdz, ls_sens, ls_custom)
        else:
            out_lx, out_ly = lx, ly

        if self.controller_config:
            cfg_rs = getattr(self.controller_config, 'data', {}).get("analog_right", {})
            rs_dz = float(cfg_rs.get("deadzone", 0.00))
            rs_adz = float(cfg_rs.get("anti_deadzone", 0.00))
            rs_rdz = float(cfg_rs.get("rest_deadzone", 0.00))
            rs_curve = str(cfg_rs.get("curve", "linear"))
            rs_factor = float(cfg_rs.get("exp_factor", 1.00))
            rs_sens = float(cfg_rs.get("sensitivity", 1.00))
            rs_custom = str(cfg_rs.get("custom_eq", cfg_rs.get("custom_curve", "")))
            rs_warp = float(cfg_rs.get("warp_threshold", cfg_rs.get("warped_stick_threshold", 0.00)))
            rs_circ_mode = str(cfg_rs.get("circularity_mode", "disabled")).lower()
            rs_cx = float(cfg_rs.get("circularity_center_x", 0.0))
            rs_cy = float(cfg_rs.get("circularity_center_y", 0.0))
            rs_bounds_str = str(cfg_rs.get("circularity_bounds", ""))
            rs_bounds = [float(x) for x in rs_bounds_str.split(",")] if rs_bounds_str and len(rs_bounds_str.split(",")) == 360 else None

            out_rx, out_ry = math_utils.apply_warped_stick_correction(rx, ry, rs_warp)
            if rs_circ_mode == "before":
                out_rx, out_ry = math_utils.apply_circularity_correction(out_rx, out_ry, rs_cx, rs_cy, rs_bounds)
                out_rx, out_ry = math_utils.process_analog_stick(out_rx, out_ry, rs_dz, rs_adz, rs_curve, rs_factor, rs_rdz, rs_sens, rs_custom)
            elif rs_circ_mode == "after":
                out_rx, out_ry = math_utils.process_analog_stick(out_rx, out_ry, rs_dz, rs_adz, rs_curve, rs_factor, rs_rdz, rs_sens, rs_custom)
                out_rx, out_ry = math_utils.apply_circularity_correction(out_rx, out_ry, rs_cx, rs_cy, rs_bounds)
            else:
                out_rx, out_ry = math_utils.process_analog_stick(out_rx, out_ry, rs_dz, rs_adz, rs_curve, rs_factor, rs_rdz, rs_sens, rs_custom)
        else:
            out_rx, out_ry = rx, ry

        self.left_radar.update_telemetry(out_lx, out_ly)
        self.right_radar.update_telemetry(out_rx, out_ry)

        l_str = f"Raw: ({lx:+.2f}, {ly:+.2f}) | Tuned: ({out_lx:+.2f}, {out_ly:+.2f})"
        if self.left_readout.text() != l_str:
            self.left_readout.setText(l_str)

        r_str = f"Raw: ({rx:+.2f}, {ry:+.2f}) | Tuned: ({out_rx:+.2f}, {out_ry:+.2f})"
        if self.right_readout.text() != r_str:
            self.right_readout.setText(r_str)

        lt = float(state.get("lt", 0.0))
        rt = float(state.get("rt", 0.0))
        self.lt_bar.update_level(lt)
        self.rt_bar.update_level(rt)

        self.button_matrix.update_button_states(state)

        active_chord = state.get("active_chord", state.get("hardware_chord", ""))
        if active_chord != self.last_active_chord:
            self.last_active_chord = str(active_chord)
            if active_chord:
                self.chords_status_label.setText(f"Status: Active Chord [{active_chord}]")
            else:
                self.chords_status_label.setText("Status: Idle")

    @Slot(dict)
    def update_status(self, status_data: Dict[str, Any]) -> None:
        if not status_data:
            return

        status = str(status_data.get("status", "DISCONNECTED")).upper()
        device = str(status_data.get("device", "Unknown Device"))

        if status == "CONNECTED":
            self.status_badge.setText("CONNECTED")
            self.status_badge.setStyleSheet("""
                background-color: #16a34a;
                color: #ffffff;
                font-weight: bold;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
            """)
            self.device_label.setText(f"🎮 {device}")
            self.transition_to_state(ConnectionState.CONNECTED)
        elif status == "CONNECTING":
            self.status_badge.setText("CONNECTING")
            self.status_badge.setStyleSheet("""
                background-color: #eab308;
                color: #ffffff;
                font-weight: bold;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
            """)
            self.device_label.setText(f"🎮 Connecting to {device}...")
        elif status == "WAITING":
            self.status_badge.setText("WAITING")
            self.status_badge.setStyleSheet("""
                background-color: #eab308;
                color: #ffffff;
                font-weight: bold;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
            """)
            self.device_label.setText("🎮 Waiting for Controller...")
            self.transition_to_state(ConnectionState.WAITING)
        else:
            self.status_badge.setText("DISCONNECTED")
            self.status_badge.setStyleSheet("""
                background-color: #dc2626;
                color: #ffffff;
                font-weight: bold;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
            """)
            self.device_label.setText("🎮 No Controller Connected")
            self.transition_to_state(ConnectionState.WAITING)

        if self.controller_config and hasattr(self, 'button_matrix'):
            try:
                self.controller_config.load()
            except Exception:
                pass
            self.button_matrix.load_profile_schema(self.controller_config)

    @Slot(dict)
    def update_diagnostics(self, diag_data: Dict[str, Any]) -> None:
        if not diag_data:
            return

        hz = float(diag_data.get("polling_rate_hz", 0.0))
        avg_ms = float(diag_data.get("avg_process_ms", 0.0))
        max_ms = float(diag_data.get("max_process_ms", 0.0))

        self.footer_label.setText(
            f"TELEMETRY FOOTER: Polling Rate: {hz:.1f} Hz | Latency: {avg_ms:.2f} ms (max: {max_ms:.2f} ms)"
        )
