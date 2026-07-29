"""
Circularity Calibration Modal for PySide6 UI (gui_v2).

Executes a 60Hz rotational polar sweep calibration state machine:
  REST -> WAIT_SWEEP -> SWEEP -> DONE

Computes resting center offset (x, y) and 360-degree max radius bounds data.
Renders real-time polar canvas with concentric circles, live stick position,
center offset marker, and bounds polygon.
"""

import sys
import os
import math
import configparser
from typing import List, Tuple, Optional, Callable, Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGroupBox, QWidget, QApplication
)
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPolygonF
from PySide6.QtCore import Qt, Slot, QTimer, QPointF

# Add root src directory to path so imports resolve cleanly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import math_utils


# ---------------------------------------------------------------------------
# QSS Styling Tokens
# ---------------------------------------------------------------------------
_MODAL_STYLE = "QDialog { background-color: #0f0a1e; color: #ffffff; }"

_CARD_STYLE = """
QGroupBox {
    background-color: rgba(22, 16, 36, 0.85);
    border: 1px solid rgba(168, 85, 247, 0.35);
    border-radius: 10px;
    margin-top: 10px;
    color: #ffffff;
    font-weight: bold;
    font-size: 11px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #a855f7;
}
"""

_BTN_ACCENT = """
QPushButton {
    background-color: rgba(168, 85, 247, 0.2);
    border: 1px solid rgba(168, 85, 247, 0.5);
    border-radius: 6px;
    color: #ffffff;
    padding: 6px 14px;
    font-size: 11px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: rgba(168, 85, 247, 0.4);
    border: 1px solid #a855f7;
}
QPushButton:pressed { background-color: #7500ab; }
QPushButton:disabled {
    background-color: rgba(60, 60, 60, 0.2);
    border: 1px solid rgba(80, 80, 80, 0.3);
    color: #666666;
}
"""

_BTN_SAVE = """
QPushButton {
    background-color: rgba(34, 197, 94, 0.2);
    border: 1px solid rgba(34, 197, 94, 0.5);
    border-radius: 6px;
    color: #ffffff;
    padding: 6px 14px;
    font-size: 11px;
    font-weight: bold;
}
QPushButton:hover { background-color: rgba(34, 197, 94, 0.4); }
QPushButton:pressed { background-color: #14532d; }
QPushButton:disabled {
    background-color: rgba(60, 60, 60, 0.2);
    border: 1px solid rgba(80, 80, 80, 0.3);
    color: #666666;
}
"""

_BTN_CANCEL = """
QPushButton {
    background-color: rgba(100, 100, 100, 0.2);
    border: 1px solid rgba(150, 150, 150, 0.4);
    border-radius: 6px;
    color: #aaaaaa;
    padding: 6px 14px;
    font-size: 11px;
}
QPushButton:hover { background-color: rgba(150, 150, 150, 0.3); }
"""


# ---------------------------------------------------------------------------
# CircularityPolarCanvas
# ---------------------------------------------------------------------------
class CircularityPolarCanvas(QWidget):
    """
    Hardware-accelerated polar coordinate radar canvas rendering:
      - Concentric grid rings (0.25, 0.5, 0.75, 1.0)
      - Crosshair X/Y axes
      - 360-degree max radius bounds polygon (neon green)
      - Center offset marker (amber dot)
      - Live stick coordinate marker (neon purple dot)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(280, 280)
        self.bounds_data: List[float] = [0.0] * 360
        self.center_x: float = 0.0
        self.center_y: float = 0.0
        self.live_x: float = 0.0
        self.live_y: float = 0.0

    def update_data(self, bounds: List[float], cx: float, cy: float, lx: float, ly: float) -> None:
        self.bounds_data = bounds
        self.center_x = cx
        self.center_y = cy
        self.live_x = lx
        self.live_y = ly
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = self.rect()
        w = rect.width()
        h = rect.height()

        # Canvas background
        painter.fillRect(rect, QColor(22, 16, 36, 215))

        cx = w / 2.0
        cy = h / 2.0
        max_r = (min(w, h) / 2.0) - 20.0

        if max_r <= 0:
            painter.end()
            return

        # 1. Draw Concentric Grid Circles
        painter.setPen(QPen(QColor(168, 85, 247, 60), 1, Qt.DashLine))
        for r_step in (0.25, 0.50, 0.75, 1.00):
            r_px = max_r * r_step
            painter.drawEllipse(QPointF(cx, cy), r_px, r_px)

        # 2. Draw Crosshair Axes
        painter.setPen(QPen(QColor(168, 85, 247, 90), 1.5))
        painter.drawLine(QPointF(cx - max_r - 5, cy), QPointF(cx + max_r + 5, cy))
        painter.drawLine(QPointF(cx, cy - max_r - 5), QPointF(cx, cy + max_r + 5))

        # 3. Draw 360-degree Bounds Polygon
        if self.bounds_data and any(r > 0.05 for r in self.bounds_data):
            poly = QPolygonF()
            for deg in range(360):
                rad = math.radians(deg)
                r_val = min(1.3, max(0.0, self.bounds_data[deg]))
                px = cx + (r_val * max_r * math.cos(rad))
                py = cy - (r_val * max_r * math.sin(rad))  # Y inverted for screen
                poly.append(QPointF(px, py))

            painter.setPen(QPen(QColor(0, 245, 160, 220), 2.0))
            painter.setBrush(QBrush(QColor(0, 245, 160, 35)))
            painter.drawPolygon(poly)

        # 4. Draw Center Offset Marker (Amber Dot)
        if abs(self.center_x) > 0.0001 or abs(self.center_y) > 0.0001:
            ocx = cx + (self.center_x * max_r)
            ocy = cy - (self.center_y * max_r)
            painter.setPen(QPen(QColor(245, 158, 11), 1.5))
            painter.setBrush(QBrush(QColor(245, 158, 11)))
            painter.drawEllipse(QPointF(ocx, ocy), 4.0, 4.0)

        # 5. Draw Live Stick Position Dot (Neon Purple / White)
        lx_px = cx + (self.live_x * max_r)
        ly_px = cy - (self.live_y * max_r)
        painter.setPen(QPen(QColor(255, 255, 255), 2.0))
        painter.setBrush(QBrush(QColor(168, 85, 247)))
        painter.drawEllipse(QPointF(lx_px, ly_px), 6.0, 6.0)

        painter.end()


# ---------------------------------------------------------------------------
# CircularityCalibrationModal
# ---------------------------------------------------------------------------
class CircularityCalibrationModal(QDialog):
    """
    Subclass of QDialog implementing 60Hz live rotational stick calibration sweep.

    State Machine:
      - REST: Collects 60 resting center samples -> calculates center_x / center_y.
      - WAIT_SWEEP: Prompts user to start rotation sweep.
      - SWEEP: Collects maximum polar radius per degree (0..359).
      - DONE: Interpolates angular gaps, computes error %, and displays qualitative grade.
    """
    def __init__(
        self,
        parent=None,
        section_name: str = "Stick_Left",
        config_manager: Any = None,
        on_finish_callback: Optional[Callable] = None
    ):
        super().__init__(parent)
        self.section_name: str = section_name
        self.config = config_manager
        self.on_finish = on_finish_callback

        self.setWindowTitle(f"Circularity Calibration — {section_name.replace('_', ' ').title()}")
        self.setMinimumSize(420, 520)
        self.setModal(True)
        self.setStyleSheet(_MODAL_STYLE)

        # Calibration State Variables
        self.calib_state: str = "REST"  # REST -> WAIT_SWEEP -> SWEEP -> DONE
        self.bounds_data: List[float] = [0.0] * 360
        self.center_x: float = 0.0
        self.center_y: float = 0.0
        self._rest_samples: List[Tuple[float, float]] = []

        self.live_x: float = 0.0
        self.live_y: float = 0.0

        self.setup_ui()

        # 60Hz Update Timer
        self.timer = QTimer(self)
        self.timer.setInterval(16)  # ~60Hz
        self.timer.timeout.connect(self.update_loop)
        self.timer.start()

    def setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        # Header Title Label
        title_text = f"🎯 CIRCULARITY SWEEP — {self.section_name.replace('_', ' ').upper()}"
        self.header_label = QLabel(title_text)
        self.header_label.setStyleSheet("color: #a855f7; font-weight: bold; font-size: 13px;")
        root.addWidget(self.header_label)

        # Polar Radar Canvas Widget
        self.canvas = CircularityPolarCanvas(self)
        root.addWidget(self.canvas)

        # Status & Readout Group
        status_grp = QGroupBox("CALIBRATION TELEMETRY & STATUS")
        status_grp.setStyleSheet(_CARD_STYLE)
        status_layout = QVBoxLayout(status_grp)
        status_layout.setContentsMargins(10, 8, 10, 8)
        status_layout.setSpacing(4)

        self.status_label = QLabel("Status: Measuring resting center offset… Keep stick centered.")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #ffffff; font-size: 11px; font-weight: bold;")
        status_layout.addWidget(self.status_label)

        self.center_label = QLabel("Center Offset: X: +0.0000 | Y: +0.0000")
        self.center_label.setStyleSheet("color: #f59e0b; font-family: 'JetBrains Mono', monospace; font-size: 11px;")
        status_layout.addWidget(self.center_label)

        self.error_label = QLabel("Average Circularity Error: -- % (Uncalibrated)")
        self.error_label.setStyleSheet("color: #00f5a0; font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: bold;")
        status_layout.addWidget(self.error_label)

        root.addWidget(status_grp)

        # Action Buttons Row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.btn_sweep = QPushButton("Start Sweep")
        self.btn_sweep.setFocusPolicy(Qt.NoFocus)
        self.btn_sweep.setStyleSheet(_BTN_ACCENT)
        self.btn_sweep.setEnabled(False)
        self.btn_sweep.clicked.connect(self.start_sweep)

        self.btn_save = QPushButton("Apply & Save")
        self.btn_save.setFocusPolicy(Qt.NoFocus)
        self.btn_save.setStyleSheet(_BTN_SAVE)
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.save_and_close)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setFocusPolicy(Qt.NoFocus)
        self.btn_cancel.setStyleSheet(_BTN_CANCEL)
        self.btn_cancel.clicked.connect(self.reject)

        btn_row.addWidget(self.btn_sweep)
        btn_row.addWidget(self.btn_save)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_cancel)

        root.addLayout(btn_row)

    @Slot(dict)
    def update_telemetry(self, state_dict: dict) -> None:
        """
        Receives live telemetry signals from UDPTelemetryWorker (~500Hz).
        Updates internal live_x and live_y coordinates.
        """
        if not isinstance(state_dict, dict):
            return

        is_right = "right" in self.section_name.lower()
        if is_right:
            self.live_x = float(state_dict.get("rx", 0.0))
            self.live_y = float(state_dict.get("ry", 0.0))
        else:
            self.live_x = float(state_dict.get("lx", 0.0))
            self.live_y = float(state_dict.get("ly", 0.0))

    def update_loop(self) -> None:
        """
        Main 60Hz state machine update and rendering loop.
        """
        lx = self.live_x
        ly = self.live_y

        if self.calib_state == "REST":
            self._rest_samples.append((lx, ly))
            count = len(self._rest_samples)
            self.status_label.setText(f"Status: Sampling resting center ({count}/60)… Keep stick centered.")
            if count >= 60:
                self.center_x = sum(s[0] for s in self._rest_samples) / float(count)
                self.center_y = sum(s[1] for s in self._rest_samples) / float(count)
                self.center_label.setText(f"Center Offset: X: {self.center_x:+.4f} | Y: {self.center_y:+.4f}")
                self.calib_state = "WAIT_SWEEP"
                self.status_label.setText("Status: Center offset captured! Click 'Start Sweep' and rotate stick 3 times CW & CCW.")
                self.btn_sweep.setEnabled(True)

        elif self.calib_state == "WAIT_SWEEP":
            pass

        elif self.calib_state == "SWEEP":
            dx = lx - self.center_x
            dy = ly - self.center_y
            r = math.sqrt(dx * dx + dy * dy)
            deg = int(math.degrees(math.atan2(dy, dx)) % 360)

            # Record max polar radius for this degree
            self.bounds_data[deg] = max(self.bounds_data[deg], r)

            sampled_count = sum(1 for radius in self.bounds_data if radius > 0.3)
            pct = (sampled_count / 360.0) * 100.0
            self.status_label.setText(f"Status: Sweeping outer boundary… Coverage: {pct:.1f}% ({sampled_count}/360 deg)")

            if sampled_count >= 350:
                self.finish_sweep()

        elif self.calib_state == "DONE":
            pass

        # Update Polar Canvas
        self.canvas.update_data(self.bounds_data, self.center_x, self.center_y, lx, ly)

    def start_sweep(self) -> None:
        """Transitions state machine from WAIT_SWEEP to SWEEP."""
        self.calib_state = "SWEEP"
        self.btn_sweep.setText("Finish Sweep")
        self.btn_sweep.disconnect()
        self.btn_sweep.clicked.connect(self.finish_sweep)
        self.status_label.setText("Status: Rotate stick smoothly around the outer edge (3 times CW & CCW)…")

    def finish_sweep(self) -> None:
        """Completes sweep phase, interpolates degree gaps, and evaluates error grade."""
        self.interpolate_bounds()
        self.calib_state = "DONE"

        error_pct = math_utils.calculate_circularity_error(self.bounds_data)
        if error_pct < 5.0:
            grade = "Excellent"
        elif error_pct < 10.0:
            grade = "Good"
        else:
            grade = "Poor"

        self.status_label.setText(f"Status: Calibration Complete! Polar bounds stored for 360 degrees.")
        self.error_label.setText(f"Average Circularity Error: {error_pct:.2f}% ({grade})")

        self.btn_sweep.setEnabled(False)
        self.btn_save.setEnabled(True)

    def interpolate_bounds(self) -> None:
        """Fills un-sampled angular gaps in bounds_data array via linear interpolation."""
        if not self.bounds_data or not any(r > 0.1 for r in self.bounds_data):
            self.bounds_data = [1.0] * 360
            return

        sampled_indices = [i for i, r in enumerate(self.bounds_data) if r > 0.1]
        if not sampled_indices:
            self.bounds_data = [1.0] * 360
            return

        num_sampled = len(sampled_indices)
        for idx_i in range(num_sampled):
            i = sampled_indices[idx_i]
            j = sampled_indices[(idx_i + 1) % num_sampled]

            r_i = self.bounds_data[i]
            r_j = self.bounds_data[j]

            # Calculate gap length wrapping around 360 degrees
            gap_len = (j - i) % 360
            if gap_len <= 1:
                continue

            for step in range(1, gap_len):
                k = (i + step) % 360
                t = step / float(gap_len)
                self.bounds_data[k] = r_i + t * (r_j - r_i)

    def save_and_close(self) -> None:
        """Saves circularity_bounds, center_x, and center_y to config and closes modal."""
        bounds_str = ",".join(f"{r:.4f}" for r in self.bounds_data)
        cx_str = f"{self.center_x:.4f}"
        cy_str = f"{self.center_y:.4f}"

        is_right = "right" in self.section_name.lower()
        target_section = "analog_right" if is_right else "analog_left"
        ini_section = "Stick_Right" if is_right else "Stick_Left"

        # 1. Update ControllerConfig JSON instance if provided
        if self.config and hasattr(self.config, "data") and isinstance(self.config.data, dict):
            if target_section not in self.config.data:
                self.config.data[target_section] = {}
            self.config.data[target_section]["circularity_bounds"] = bounds_str
            self.config.data[target_section]["circularity_center_x"] = cx_str
            self.config.data[target_section]["circularity_center_y"] = cy_str
            self.config.data[target_section]["circularity_mode"] = "before"
            try:
                self.config.save()
            except Exception:
                pass

        # 2. Update config.ini if file exists
        config_ini_path = "config.ini"
        if os.path.exists(config_ini_path):
            try:
                parser = configparser.ConfigParser()
                parser.read(config_ini_path, encoding="utf-8")
                if not parser.has_section(ini_section):
                    parser.add_section(ini_section)
                parser.set(ini_section, "circularity_bounds", bounds_str)
                parser.set(ini_section, "circularity_center_x", cx_str)
                parser.set(ini_section, "circularity_center_y", cy_str)
                parser.set(ini_section, "circularity_mode", "before")
                with open(config_ini_path, "w", encoding="utf-8") as f:
                    parser.write(f)
            except Exception:
                pass

        # Callback if registered
        if self.on_finish:
            try:
                self.on_finish(self.bounds_data, self.center_x, self.center_y)
            except Exception:
                pass

        self.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    modal = CircularityCalibrationModal(section_name="Stick_Left")
    modal.show()
    sys.exit(app.exec())
