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
    QWidget, QApplication, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QStackedWidget
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

        # 1. Header Banner & Connection Status Card
        self.header_card = QFrame()
        self.header_card.setObjectName("glass_card")
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

        header_layout.addWidget(self.status_badge)
        header_layout.addWidget(self.device_label)
        header_layout.addStretch()

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

        # 5. Active Hardware Chords Telemetry Card
        self.chords_card = QFrame()
        self.chords_card.setObjectName("glass_card")
        chords_layout = QVBoxLayout(self.chords_card)
        chords_layout.setContentsMargins(12, 10, 12, 10)

        self.chords_header = QLabel("⚡ ACTIVE HARDWARE CHORDS TELEMETRY")
        chords_layout.addWidget(self.chords_header)

        self.chords_status_label = QLabel("Status: Idle")
        self.chords_status_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 12px;")
        chords_layout.addWidget(self.chords_status_label)

        main_layout.addWidget(self.chords_card)

        # 6. Telemetry Footer Bar
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

            bg_glass = color_to_rgba_str(bg_color, alpha_override=0.85)
            border_glass = color_to_rgba_str(accent_1, alpha_override=0.35)

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

    def _on_device_selected(self, device_info: dict) -> None:
        """Triggered when user selects a device card in State A."""
        self.overlay.trigger_transition("CONNECTING", f"Resolving profile for {device_info.get('product_string', 'Device')}...")
        self.decision_engine.process_device(device_info, is_xinput=False)

    def _on_profile_resolved(self, profile_path: str) -> None:
        """Profile decision engine resolved a profile."""
        self.transition_to_state(ConnectionState.CONNECTED)

    def _on_launch_wizard(self, device_info: dict) -> None:
        """Profile decision engine requested calibration wizard."""
        dlg = NativeCalibrationWizardDialog(device_info, self)
        dlg.calibration_complete.connect(self._on_profile_resolved)
        dlg.exec()

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

        status = str(status_data.get("status", "DISCONNECTED"))
        device = str(status_data.get("device", "Unknown Device"))

        if status.upper() in ("CONNECTED", "CONNECTED"):
            self.status_badge.setText("CONNECTED")
            self.status_badge.setStyleSheet("""
                background-color: #16a34a;
                color: #ffffff;
                font-weight: bold;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
            """)
            self.transition_to_state(ConnectionState.CONNECTED)
        elif status.upper() in ("CONNECTING", "WAITING"):
            self.status_badge.setText(status.upper())
            self.status_badge.setStyleSheet("""
                background-color: #eab308;
                color: #ffffff;
                font-weight: bold;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
            """)
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
            self.transition_to_state(ConnectionState.WAITING)

        self.device_label.setText(f"🎮 {device}")

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
