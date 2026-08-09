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
from gui_v2.services.theme_manager import ThemeManager, color_to_rgba_str, color_to_hex6

# ---------------------------------------------------------------------------
# Pre-computed Trigonometric Lookup Tables (360 degrees)
# ---------------------------------------------------------------------------
_COS_TABLE: List[float] = [math.cos(math.radians(deg)) for deg in range(360)]
_SIN_TABLE: List[float] = [math.sin(math.radians(deg)) for deg in range(360)]


# ---------------------------------------------------------------------------
# Dynamic QSS Generators
# ---------------------------------------------------------------------------
def get_accent_btn_qss(tm: ThemeManager) -> str:
    acc1 = tm.get_color("accent_1")
    bg = color_to_rgba_str(acc1, 0.2)
    border = color_to_rgba_str(acc1, 0.5)
    hover_bg = color_to_rgba_str(acc1, 0.4)
    pressed_bg = color_to_rgba_str(acc1, 0.7)
    acc_hex = color_to_hex6(acc1)
    return f"""
QPushButton {{
    background-color: {bg};
    border: 1px solid {border};
    border-radius: 6px;
    color: #ffffff;
    padding: 6px 14px;
    font-size: 11px;
    font-weight: bold;
}}
QPushButton:hover {{
    background-color: {hover_bg};
    border: 1px solid {acc_hex};
}}
QPushButton:pressed {{ background-color: {pressed_bg}; }}
QPushButton:disabled {{
    background-color: rgba(60, 60, 60, 0.2);
    border: 1px solid rgba(80, 80, 80, 0.3);
    color: #666666;
}}
"""


def get_save_btn_qss(tm: ThemeManager) -> str:
    acc2 = tm.get_color("accent_2")
    bg = color_to_rgba_str(acc2, 0.2)
    border = color_to_rgba_str(acc2, 0.5)
    hover_bg = color_to_rgba_str(acc2, 0.4)
    pressed_bg = color_to_rgba_str(acc2, 0.7)
    return f"""
QPushButton {{
    background-color: {bg};
    border: 1px solid {border};
    border-radius: 6px;
    color: #ffffff;
    padding: 6px 14px;
    font-size: 11px;
    font-weight: bold;
}}
QPushButton:hover {{ background-color: {hover_bg}; }}
QPushButton:pressed {{ background-color: {pressed_bg}; }}
QPushButton:disabled {{
    background-color: rgba(60, 60, 60, 0.2);
    border: 1px solid rgba(80, 80, 80, 0.3);
    color: #666666;
}}
"""


def get_cancel_btn_qss() -> str:
    return """
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
      - 360-degree max radius bounds polygon (theme accent_2)
      - Center offset marker (amber dot)
      - Live stick coordinate marker (theme accent_1 dot)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(280, 280)
        self.bounds_data: List[float] = [0.0] * 360
        self.center_x: float = 0.0
        self.center_y: float = 0.0
        self.live_x: float = 0.0
        self.live_y: float = 0.0
        self._last_paint_time: float = 0.0
        self._frame_delay_sec: float = 1.0 / 60.0

    def update_data(self, bounds: List[float], cx: float, cy: float, lx: float, ly: float, is_sweeping: bool = False) -> None:
        self.bounds_data = bounds
        self.center_x = cx
        self.center_y = cy
        self.live_x = lx
        self.live_y = ly
        self.is_sweeping = is_sweeping

        import time
        now = time.perf_counter()
        if (now - self._last_paint_time) >= self._frame_delay_sec:
            self.update()

    def paintEvent(self, event) -> None:
        import time
        now = time.perf_counter()
        if self._last_paint_time > 0 and (now - self._last_paint_time) < (self._frame_delay_sec * 0.85):
            return
        self._last_paint_time = now

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = self.rect()
        w = rect.width()
        h = rect.height()

        tm = ThemeManager.get_instance()
        bg_col = tm.get_color("graph_bg")
        axis_col = tm.get_color("graph_axis")
        acc1_col = tm.get_color("accent_1")
        acc2_col = tm.get_color("accent_2")

        # Canvas background (theme graph_bg token)
        painter.fillRect(rect, QColor(bg_col.red(), bg_col.green(), bg_col.blue(), 230))

        cx = w / 2.0
        cy = h / 2.0
        max_r = (min(w, h) / 2.0) - 20.0

        if max_r <= 0:
            painter.end()
            return

        # 1. Draw Concentric Grid Circles (graph_axis token)
        painter.setPen(QPen(axis_col, 1, Qt.DashLine))
        for r_step in (0.25, 0.50, 0.75, 1.00):
            r_px = max_r * r_step
            painter.drawEllipse(QPointF(cx, cy), r_px, r_px)

        # 2. Draw Crosshair Axes (graph_axis token)
        painter.setPen(QPen(axis_col, 1.5))
        painter.drawLine(QPointF(cx - max_r - 5, cy), QPointF(cx + max_r + 5, cy))
        painter.drawLine(QPointF(cx, cy - max_r - 5), QPointF(cx, cy + max_r + 5))

        # 3. Draw 360-degree Bounds Polygon (Accent #2) — rendered when not actively sweeping
        if not getattr(self, 'is_sweeping', False) and self.bounds_data and any(r > 0.05 for r in self.bounds_data):
            poly = QPolygonF()
            for deg in range(360):
                r_val = min(1.3, max(0.0, self.bounds_data[deg]))
                px = cx + (r_val * max_r * _COS_TABLE[deg])
                py = cy - (r_val * max_r * _SIN_TABLE[deg])  # Y inverted for screen
                poly.append(QPointF(px, py))

            painter.setPen(QPen(QColor(acc2_col.red(), acc2_col.green(), acc2_col.blue(), 220), 2.0))
            painter.setBrush(QBrush(QColor(acc2_col.red(), acc2_col.green(), acc2_col.blue(), 35)))
            painter.drawPolygon(poly)

        # 4. Draw Center Offset Marker (Amber Dot)
        if abs(self.center_x) > 0.0001 or abs(self.center_y) > 0.0001:
            ocx = cx + (self.center_x * max_r)
            ocy = cy - (self.center_y * max_r)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(245, 158, 11)))
            painter.drawEllipse(QPointF(ocx, ocy), 5.0, 5.0)

        # 5. Draw Live Stick Position Dot (Accent #1)
        lx_px = cx + (self.live_x * max_r)
        ly_px = cy - (self.live_y * max_r)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(acc1_col.red(), acc1_col.green(), acc1_col.blue())))
        painter.drawEllipse(QPointF(lx_px, ly_px), 7.2, 7.2)

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

        # Calibration State Variables
        self.calib_state: str = "REST"  # REST -> WAIT_SWEEP -> SWEEP -> DONE
        self.bounds_data: List[float] = [0.0] * 360
        self.center_x: float = 0.0
        self.center_y: float = 0.0
        self._rest_samples: List[Tuple[float, float]] = []
        self._last_status_text: str = ""

        self.live_x: float = 0.0
        self.live_y: float = 0.0
        self._sampled_count: int = 0

        self.setup_ui()

        # Connect to dynamic ThemeManager signals
        tm = ThemeManager.get_instance()
        tm.theme_changed.connect(self.apply_theme)
        self.apply_theme()

        # 60Hz Update Timer
        self.timer = QTimer(self)
        self.timer.setInterval(16)  # ~60Hz
        self.timer.timeout.connect(self.update_loop)
        self.timer.start()

    def _set_status(self, text: str) -> None:
        """Sets status label text only if string changed to eliminate layout re-evaluations."""
        if text != self._last_status_text:
            self.status_label.setText(text)
            self._last_status_text = text

    def apply_theme(self) -> None:
        """Applies dynamic QSS tokens from ThemeManager."""
        tm = ThemeManager.get_instance()
        win_bg = tm.get_color("window_bg")
        acc1 = tm.get_color("accent_1")
        acc2 = tm.get_color("accent_2")
        bg = tm.get_color("background")

        win_bg_rgba = color_to_rgba_str(win_bg, 1.0)
        acc1_hex = color_to_hex6(acc1)
        acc2_hex = color_to_hex6(acc2)
        bg_rgba = color_to_rgba_str(bg, 0.9)
        border_rgba = color_to_rgba_str(acc1, 0.35)

        self.setStyleSheet(f"""
        QDialog {{ background-color: {win_bg_rgba}; color: #ffffff; }}
        QGroupBox {{
            background-color: {bg_rgba};
            border: 1px solid {border_rgba};
            border-radius: 8px;
            margin-top: 10px;
            color: #ffffff;
            font-weight: bold;
            font-size: 11px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 6px;
            color: #ffffff;
        }}
        """)

        if hasattr(self, "header_label"):
            self.header_label.setStyleSheet(f"color: {acc1_hex}; font-weight: bold; font-size: 13px;")
        if hasattr(self, "center_label"):
            self.center_label.setStyleSheet("color: #f59e0b; font-family: 'JetBrains Mono', monospace; font-size: 11px;")
        if hasattr(self, "error_label"):
            self.error_label.setStyleSheet(f"color: {acc2_hex}; font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: bold;")
        if hasattr(self, "btn_sweep"):
            self.btn_sweep.setStyleSheet(get_accent_btn_qss(tm))
        if hasattr(self, "btn_save"):
            self.btn_save.setStyleSheet(get_save_btn_qss(tm))
        if hasattr(self, "btn_cancel"):
            self.btn_cancel.setStyleSheet(get_cancel_btn_qss())
        if hasattr(self, "canvas"):
            self.canvas.update()

    def setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        # Header Title Label
        title_text = f"🎯 CIRCULARITY SWEEP — {self.section_name.replace('_', ' ').upper()}"
        self.header_label = QLabel(title_text)
        root.addWidget(self.header_label)

        # Polar Radar Canvas Widget
        self.canvas = CircularityPolarCanvas(self)
        root.addWidget(self.canvas)

        # Status & Readout Group
        status_grp = QGroupBox("CALIBRATION TELEMETRY & STATUS")
        status_layout = QVBoxLayout(status_grp)
        status_layout.setContentsMargins(10, 8, 10, 8)
        status_layout.setSpacing(4)

        self.status_label = QLabel("Status: Measuring resting center offset… Keep stick centered.")
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)

        self.center_label = QLabel("Center Offset: X: +0.0000 | Y: +0.0000")
        status_layout.addWidget(self.center_label)

        self.error_label = QLabel("Average Circularity Error: -- % (Uncalibrated)")
        status_layout.addWidget(self.error_label)

        root.addWidget(status_grp)

        # Action Buttons Row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.btn_sweep = QPushButton("Start Sweep")
        self.btn_sweep.setFocusPolicy(Qt.NoFocus)
        self.btn_sweep.setEnabled(False)
        self.btn_sweep.clicked.connect(self.start_sweep)

        self.btn_save = QPushButton("Apply & Save")
        self.btn_save.setFocusPolicy(Qt.NoFocus)
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.save_and_close)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setFocusPolicy(Qt.NoFocus)
        self.btn_cancel.clicked.connect(self.reject)

        btn_row.addWidget(self.btn_sweep)
        btn_row.addWidget(self.btn_save)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_cancel)

        root.addLayout(btn_row)

    @Slot(dict)
    def update_telemetry(self, state_dict: dict) -> None:
        """
        Receives live telemetry signals from UDPTelemetryWorker (up to 1000Hz).
        Updates internal live_x and live_y coordinates and records sweep samples.
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

        if self.calib_state == "SWEEP":
            self._record_sweep_sample(self.live_x, self.live_y)

    def _record_sweep_sample(self, lx: float, ly: float) -> None:
        """High-frequency (up to 1000Hz) sweep sample ingestion for 360 degree polar bounds."""
        dx = lx - self.center_x
        dy = ly - self.center_y
        r = math.sqrt(dx * dx + dy * dy)
        if r < 0.05:
            return  # Ignore near-center noise

        deg = int(math.degrees(math.atan2(dy, dx)) % 360)
        was_unsampled = (self.bounds_data[deg] <= 0.1)

        if r > self.bounds_data[deg]:
            self.bounds_data[deg] = r

        if was_unsampled and self.bounds_data[deg] > 0.1:
            self._sampled_count += 1

        pct = (self._sampled_count / 360.0) * 100.0
        self._set_status(f"Status: Sweeping outer boundary… Coverage: {pct:.1f}% ({self._sampled_count}/360 deg)")

        if self._sampled_count >= 350:
            self.finish_sweep()

    def update_loop(self) -> None:
        """
        Main 60Hz state machine rendering and status update loop.
        """
        lx = self.live_x
        ly = self.live_y

        if self.calib_state == "REST":
            self._rest_samples.append((lx, ly))
            count = len(self._rest_samples)
            self._set_status(f"Status: Sampling resting center ({count}/60)… Keep stick centered.")
            if count >= 60:
                self.center_x = sum(s[0] for s in self._rest_samples) / float(count)
                self.center_y = sum(s[1] for s in self._rest_samples) / float(count)
                self.center_label.setText(f"Center Offset: X: {self.center_x:+.4f} | Y: {self.center_y:+.4f}")
                self.calib_state = "WAIT_SWEEP"
                self._set_status("Status: Center offset captured! Click 'Start Sweep' and rotate stick 3 times CW & CCW.")
                self.btn_sweep.setEnabled(True)

        elif self.calib_state == "WAIT_SWEEP":
            pass

        elif self.calib_state == "SWEEP":
            if self._sampled_count >= 350 or sum(1 for r in self.bounds_data if r > 0.1) >= 350:
                self.finish_sweep()

        elif self.calib_state == "DONE":
            pass

        # Update Polar Canvas (skips polygon draw during active SWEEP for 60 FPS performance)
        is_sweeping_active = (self.calib_state == "SWEEP")
        self.canvas.update_data(self.bounds_data, self.center_x, self.center_y, lx, ly, is_sweeping=is_sweeping_active)

    def start_sweep(self) -> None:
        """Transitions state machine from WAIT_SWEEP to SWEEP."""
        self.calib_state = "SWEEP"
        self._sampled_count = 0
        self.btn_sweep.setText("Finish Sweep")
        try:
            self.btn_sweep.clicked.disconnect()
        except Exception:
            pass
        self.btn_sweep.clicked.connect(self.finish_sweep)
        self._set_status("Status: Rotate stick smoothly around the outer edge (3 times CW & CCW)…")

    def finish_sweep(self) -> None:
        """Completes sweep phase, interpolates degree gaps, and evaluates error grade."""
        self.interpolate_bounds()
        self.calib_state = "DONE"

        error_pct = math_utils.calculate_circularity_error(self.bounds_data)
        if error_pct < 3.0:
            grade = "Literally Bonkers."
        elif error_pct < 7.0:
            grade = "Ideal"
        elif error_pct < 12:
            grade = "Acceptable"
        else:
            grade = "Suboptimal"

        self._set_status("Status: Calibration Complete! Polar bounds stored for 360 degrees.")
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
