"""
Dashboard View Module for PySide6 UI (gui_v2).
Provides live telemetry monitoring, dual stick radars, trigger actuation meters,
button matrix status, active hardware chords telemetry, and IPC diagnostic footer.
"""

import sys
import os
import math
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QApplication, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Slot

# Import widget wrappers from gui_v2.widgets
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import math_utils
from gui_v2.widgets.stick_radar import StickRadarWidget
from gui_v2.widgets.trigger_bar import TriggerBarWidget
from gui_v2.widgets.button_matrix import ButtonMatrixWidget


class DashboardView(QWidget):
    """
    Primary live telemetry dashboard view for PySide6 interface.
    Receives high-frequency UDP telemetry signals and 1Hz/2Hz status/diagnostics signals.
    """
    def __init__(self, controller_config=None, parent=None):
        super().__init__(parent)
        self.controller_config = controller_config
        self.last_active_chord: str = ""
        self.setup_ui()
        self._sync_config()
        self._setup_theme_sync()

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
            
            accent_1_hex6 = color_to_hex6(accent_1)
            accent_2_hex6 = color_to_hex6(accent_2)
            
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
                self.left_readout.setStyleSheet(f"color: {accent_2_hex6}; font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 11px; font-weight: bold;")
            if hasattr(self, 'right_readout'):
                self.right_readout.setStyleSheet(f"color: {accent_2_hex6}; font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 11px; font-weight: bold;")
            if hasattr(self, 'chords_header'):
                self.chords_header.setStyleSheet(f"color: {accent_1_hex6}; font-weight: bold; font-size: 10px;")
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

    def setup_ui(self) -> None:
        """
        Constructs the dashboard layout according to Phase 4 specifications.
        """
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # 1. Header Banner & Connection Status Card
        self.header_card = QFrame()
        self.header_card.setObjectName("glass_card")
        header_layout = QHBoxLayout(self.header_card)
        header_layout.setContentsMargins(14, 10, 14, 10)

        # Status Pill Badge
        self.status_badge = QLabel("DISCONNECTED")
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge.setStyleSheet("""
            background-color: #dc2626;
            color: #ffffff;
            font-weight: bold;
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 11px;
        """)

        # Device Name Label
        self.device_label = QLabel("🎮 No Controller Detected")
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

    @Slot(dict)
    def update_telemetry(self, state: Dict[str, Any]) -> None:
        """
        Receives ControllerState dictionary from UDPTelemetryWorker (~500Hz).
        Updates Stick Radars with modified tuned output, Trigger Bars, Button Matrix highlights, and Chord status.
        """
        if not state:
            return

        # 1. Raw Hardware Inputs
        lx = float(state.get("lx", 0.0))
        ly = float(state.get("ly", 0.0))
        rx = float(state.get("rx", 0.0))
        ry = float(state.get("ry", 0.0))

        # 2. Process Left Stick Output
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

        # 3. Process Right Stick Output
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

        # Send MODIFIED tuned outputs to dashboard stick radars
        self.left_radar.update_telemetry(out_lx, out_ly)
        self.right_radar.update_telemetry(out_rx, out_ry)

        l_str = f"Raw: ({lx:+.2f}, {ly:+.2f}) | Tuned: ({out_lx:+.2f}, {out_ly:+.2f})"
        if self.left_readout.text() != l_str:
            self.left_readout.setText(l_str)

        r_str = f"Raw: ({rx:+.2f}, {ry:+.2f}) | Tuned: ({out_rx:+.2f}, {out_ry:+.2f})"
        if self.right_readout.text() != r_str:
            self.right_readout.setText(r_str)


        # 2. Update Triggers
        lt = float(state.get("lt", 0.0))
        rt = float(state.get("rt", 0.0))
        self.lt_bar.update_level(lt)
        self.rt_bar.update_level(rt)

        # 3. Update Button Matrix
        self.button_matrix.update_button_states(state)

        # 4. Update Hardware Chords Status Label if present
        active_chord = state.get("active_chord", state.get("hardware_chord", ""))
        if active_chord != self.last_active_chord:
            self.last_active_chord = str(active_chord)
            if active_chord:
                self.chords_status_label.setText(f"Status: Active Chord [{active_chord}]")
            else:
                self.chords_status_label.setText("Status: Idle")

    @Slot(dict)
    def update_status(self, status_data: Dict[str, Any]) -> None:
        """
        Receives status.json payload (1Hz) from FilePollerWorker.
        Updates connection badge color, device name, and status text.
        """
        if not status_data:
            return

        status = str(status_data.get("status", "Disconnected"))
        device = str(status_data.get("device", "Unknown Device"))

        if status.lower() == "connected":
            self.status_badge.setText("CONNECTED")
            self.status_badge.setStyleSheet("""
                background-color: #16a34a;
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

        self.device_label.setText(f"🎮 {device}")

        if self.controller_config and hasattr(self, 'button_matrix'):
            try:
                self.controller_config.load()
            except Exception:
                pass
            self.button_matrix.load_profile_schema(self.controller_config)

    @Slot(dict)
    def update_diagnostics(self, diag_data: Dict[str, Any]) -> None:
        """
        Receives diagnostics.json payload (2Hz) from FilePollerWorker.
        Updates bottom footer stats (Polling Rate Hz, Latency ms).
        """
        if not diag_data:
            return

        hz = float(diag_data.get("polling_rate_hz", 0.0))
        avg_ms = float(diag_data.get("avg_process_ms", 0.0))
        max_ms = float(diag_data.get("max_process_ms", 0.0))

        self.footer_label.setText(
            f"TELEMETRY FOOTER: Polling Rate: {hz:.1f} Hz | Latency: {avg_ms:.2f} ms (max: {max_ms:.2f} ms)"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("DashboardView Standalone Test")
    window.resize(900, 700)
    layout = QVBoxLayout(window)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)

    dash = DashboardView()
    scroll.setWidget(dash)
    layout.addWidget(scroll)

    window.show()

    # Simulate IPC signal emissions
    from PySide6.QtCore import QTimer

    # 1. Status update
    dash.update_status({"status": "Connected", "device": "8BitDo Ultimate 2C (DInput Mode)"})

    # 2. Diagnostics update
    dash.update_diagnostics({"polling_rate_hz": 250.0, "avg_process_ms": 0.22, "max_process_ms": 0.38})

    # 3. Telemetry loop simulation
    step = [0]

    def tick_telemetry():
        step[0] += 1
        s = step[0]
        state = {
            "lx": math.sin(s * 0.05) * 0.7,
            "ly": math.cos(s * 0.05) * 0.7,
            "rx": math.cos(s * 0.03) * 0.5,
            "ry": math.sin(s * 0.03) * 0.5,
            "lt": (math.sin(s * 0.1) + 1.0) / 2.0,
            "rt": (math.cos(s * 0.1) + 1.0) / 2.0,
            "a": 1 if s % 20 < 10 else 0,
            "b": 1 if s % 30 < 15 else 0,
            "extra_inputs": {
                "m1": 1 if s % 40 < 20 else 0,
                "m2": 1 if s % 50 < 25 else 0
            }
        }
        dash.update_telemetry(state)

    timer = QTimer()
    timer.timeout.connect(tick_telemetry)
    timer.start(16)

    sys.exit(app.exec())
