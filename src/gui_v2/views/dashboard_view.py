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
from gui_v2.widgets.stick_radar import StickRadarWidget
from gui_v2.widgets.trigger_bar import TriggerBarWidget
from gui_v2.widgets.button_matrix import ButtonMatrixWidget


class DashboardView(QWidget):
    """
    Primary live telemetry dashboard view for PySide6 interface.
    Receives high-frequency UDP telemetry signals and 1Hz/2Hz status/diagnostics signals.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_active_chord: str = ""
        self.setup_ui()

    def setup_ui(self) -> None:
        """
        Constructs the dashboard layout according to Phase 4 specifications.
        """
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # 1. Header Banner & Connection Status Card
        header_card = QFrame()
        header_card.setObjectName("glass_card")
        header_card.setStyleSheet("""
            QFrame#glass_card {
                background-color: rgba(22, 16, 36, 0.85);
                border: 1px solid rgba(168, 85, 247, 0.35);
                border-radius: 12px;
            }
        """)
        header_layout = QHBoxLayout(header_card)
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

        main_layout.addWidget(header_card)

        # 2. Dual Stick Radars Panel
        radars_layout = QHBoxLayout()
        radars_layout.setSpacing(12)

        # Left Stick Card
        left_card = QFrame()
        left_card.setObjectName("glass_card")
        left_card.setStyleSheet("""
            QFrame#glass_card {
                background-color: rgba(22, 16, 36, 0.85);
                border: 1px solid rgba(168, 85, 247, 0.35);
                border-radius: 12px;
            }
        """)
        left_card_layout = QVBoxLayout(left_card)
        left_card_layout.setContentsMargins(12, 10, 12, 10)

        self.left_radar = StickRadarWidget("LEFT STICK RADAR")
        self.left_readout = QLabel("Raw: (+0.00, +0.00) | Tuned: (+0.00)")
        self.left_readout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_readout.setStyleSheet("color: #a855f7; font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 11px; font-weight: bold;")

        left_card_layout.addWidget(self.left_radar)
        left_card_layout.addWidget(self.left_readout)

        # Right Stick Card
        right_card = QFrame()
        right_card.setObjectName("glass_card")
        right_card.setStyleSheet("""
            QFrame#glass_card {
                background-color: rgba(22, 16, 36, 0.85);
                border: 1px solid rgba(168, 85, 247, 0.35);
                border-radius: 12px;
            }
        """)
        right_card_layout = QVBoxLayout(right_card)
        right_card_layout.setContentsMargins(12, 10, 12, 10)

        self.right_radar = StickRadarWidget("RIGHT STICK RADAR")
        self.right_readout = QLabel("Raw: (+0.00, +0.00) | Tuned: (+0.00)")
        self.right_readout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.right_readout.setStyleSheet("color: #a855f7; font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 11px; font-weight: bold;")

        right_card_layout.addWidget(self.right_radar)
        right_card_layout.addWidget(self.right_readout)

        radars_layout.addWidget(left_card)
        radars_layout.addWidget(right_card)

        main_layout.addLayout(radars_layout)

        # 3. Analog Triggers Panel
        triggers_card = QFrame()
        triggers_card.setObjectName("glass_card")
        triggers_card.setStyleSheet("""
            QFrame#glass_card {
                background-color: rgba(22, 16, 36, 0.85);
                border: 1px solid rgba(168, 85, 247, 0.35);
                border-radius: 12px;
            }
        """)
        triggers_layout = QVBoxLayout(triggers_card)
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

        main_layout.addWidget(triggers_card)

        # 4. Controller Button Status Matrix Panel
        self.button_matrix = ButtonMatrixWidget()
        main_layout.addWidget(self.button_matrix)

        # 5. Active Hardware Chords Telemetry Card
        chords_card = QFrame()
        chords_card.setObjectName("glass_card")
        chords_card.setStyleSheet("""
            QFrame#glass_card {
                background-color: rgba(22, 16, 36, 0.85);
                border: 1px solid rgba(168, 85, 247, 0.35);
                border-radius: 12px;
            }
        """)
        chords_layout = QVBoxLayout(chords_card)
        chords_layout.setContentsMargins(12, 10, 12, 10)

        chords_header = QLabel("⚡ ACTIVE HARDWARE CHORDS TELEMETRY")
        chords_header.setStyleSheet("color: #a855f7; font-weight: bold; font-size: 10px;")
        chords_layout.addWidget(chords_header)

        self.chords_status_label = QLabel("Status: Idle")
        self.chords_status_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 12px;")
        chords_layout.addWidget(self.chords_status_label)

        main_layout.addWidget(chords_card)

        # 6. Telemetry Footer Bar
        self.footer_label = QLabel("TELEMETRY FOOTER: Polling Rate: -- Hz | Latency: <1.0 ms")
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.footer_label.setStyleSheet("color: rgba(255, 255, 255, 0.5); font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 10px; padding: 4px;")
        main_layout.addWidget(self.footer_label)

    @Slot(dict)
    def update_telemetry(self, state: Dict[str, Any]) -> None:
        """
        Receives ControllerState dictionary from UDPTelemetryWorker (~500Hz).
        Updates Stick Radars, Trigger Bars, Button Matrix highlights, and Chord status.
        Computationally light to avoid main thread latency.
        """
        if not state:
            return

        # 1. Update Joysticks
        lx = float(state.get("lx", 0.0))
        ly = float(state.get("ly", 0.0))
        rx = float(state.get("rx", 0.0))
        ry = float(state.get("ry", 0.0))

        self.left_radar.update_telemetry(lx, ly)
        self.right_radar.update_telemetry(rx, ry)

        l_mag = math.sqrt(lx * lx + ly * ly)
        r_mag = math.sqrt(rx * rx + ry * ry)

        self.left_readout.setText(f"Raw: ({lx:+.2f}, {ly:+.2f}) | Tuned: ({l_mag:+.2f})")
        self.right_readout.setText(f"Raw: ({rx:+.2f}, {ry:+.2f}) | Tuned: ({r_mag:+.2f})")

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
