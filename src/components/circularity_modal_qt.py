"""
Circularity Calibration Dialog for PySide6 (circularity_modal_qt.py)
Modal dialog replacing legacy circularity_modal.py with QPainter polar grid drawing,
360-degree point cloud heatmap visualization, color-coded error vector lines,
speed warnings, and wizard steps.
"""

import math
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QWidget
)
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QPolygonF
import math_utils


class CircularityCanvasWidget(QWidget):
    """QPainter canvas widget for real-time polar grid and color-coded error vector lines."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 320)
        self.bounds_data = [0.0] * 360
        self.raw_x = 0.0
        self.raw_y = 0.0

    def update_data(self, raw_x, raw_y, bounds_data):
        self.raw_x = raw_x
        self.raw_y = raw_y
        self.bounds_data = list(bounds_data)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        width = self.width()
        height = self.height()
        cx = width / 2.0
        cy = height / 2.0
        scale = min(width, height) * 0.42

        # Draw Background Card
        painter.setPen(QPen(QColor(168, 85, 247, 60), 1))
        painter.setBrush(QBrush(QColor(12, 9, 20, 240)))
        painter.drawRoundedRect(0, 0, width, height, 12, 12)

        # Draw Dashed Axes & Unit Reference Circle
        pen_grid = QPen(QColor(255, 255, 255, 30), 1, Qt.PenStyle.DashLine)
        painter.setPen(pen_grid)
        painter.drawLine(QPointF(cx, 10), QPointF(cx, height - 10))
        painter.drawLine(QPointF(10, cy), QPointF(width - 10, cy))
        painter.drawEllipse(QPointF(cx, cy), scale, scale)

        # Draw Color-Coded Error Vector Rays & Polygon Loop
        poly_pts = []
        for a in range(0, 360, 2):
            r = self.bounds_data[a]
            if r > 0:
                rad = math.radians(a)
                x = cx + r * math.cos(rad) * scale
                y = cy - r * math.sin(rad) * scale
                poly_pts.append(QPointF(x, y))

                # Color-coded error vectors (Green < 1%, Yellow < 5%, Red > 5%)
                err = abs(r - 1.0)
                if err < 0.01:
                    ray_color = QColor(0, 245, 160, 100)
                elif err < 0.05:
                    ray_color = QColor(250, 204, 21, 120)
                else:
                    ray_color = QColor(255, 82, 82, 160)

                painter.setPen(QPen(ray_color, 1))
                painter.drawLine(QPointF(cx, cy), QPointF(x, y))

        if len(poly_pts) > 2:
            painter.setPen(QPen(QColor(168, 85, 247), 2))
            painter.setBrush(QBrush(QColor(168, 85, 247, 30)))
            painter.drawPolygon(QPolygonF(poly_pts))

        # Draw Live Position Indicator Dot
        px = cx + (self.raw_x * scale)
        py = cy - (self.raw_y * scale)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(0, 245, 160)))
        painter.drawEllipse(QPointF(px, py), 6, 6)

        painter.end()


class CircularityCalibrationDialog(QDialog):
    """
    Step-by-step Circularity Calibration Wizard dialog for PySide6.
    """

    def __init__(self, parent, title="Stick", section="Stick_Left", on_finish=None):
        super().__init__(parent)
        self.parent_app = parent
        self.section = section
        self.is_left = ("left" in section.lower())
        self.on_finish = on_finish

        self.setWindowTitle(f"{title} - Circularity Calibration")
        self.setFixedSize(500, 580)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        self.calib_state = "REST"
        self.center_x = 0.0
        self.center_y = 0.0
        self.center_samples_x = []
        self.center_samples_y = []
        self.bounds_data = [0.0] * 360
        self.timer_ticks = 0
        self.last_theta = None
        self.accum_cw = 0.0
        self.accum_ccw = 0.0
        self.speed_warn_timer = 0

        self.setup_ui(title)

        # Setup 60Hz update timer
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(16)
        self.update_timer.timeout.connect(self.update_loop)
        self.update_timer.start()

    def setup_ui(self, title):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Title Label
        lbl_title = QLabel(f"🎯 Calibrating {title}")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #f3e8ff;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)

        # Instruction Step Label
        self.lbl_instruct = QLabel("Step 1: Leave the stick at rest without touching it.\nSampling center offset...")
        self.lbl_instruct.setStyleSheet("font-size: 13px; color: #a992cb;")
        self.lbl_instruct.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_instruct)

        # Warning Label
        self.lbl_warning = QLabel("")
        self.lbl_warning.setStyleSheet("font-size: 13px; font-weight: bold; color: #ff5252;")
        self.lbl_warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_warning)

        # Canvas Widget
        self.canvas = CircularityCanvasWidget(self)
        layout.addWidget(self.canvas, alignment=Qt.AlignmentFlag.AlignCenter)

        # Action Button
        self.btn_action = QPushButton("Wait...")
        self.btn_action.setObjectName("PrimaryBtn")
        self.btn_action.setEnabled(False)
        layout.addWidget(self.btn_action)

        # Results Label
        self.lbl_result = QLabel("")
        self.lbl_result.setStyleSheet("font-size: 13px; font-weight: bold; color: #00f5a0;")
        self.lbl_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_result)

        # Button Frame (hidden initially)
        self.btn_frame = QFrame()
        btn_layout = QHBoxLayout(self.btn_frame)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        self.btn_apply = QPushButton("Apply Changes")
        self.btn_apply.setObjectName("PrimaryBtn")
        self.btn_apply.clicked.connect(self.save_and_close)

        self.btn_discard = QPushButton("Discard")
        self.btn_discard.setObjectName("SecondaryBtn")
        self.btn_discard.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_apply)
        btn_layout.addWidget(self.btn_discard)
        self.btn_frame.hide()
        layout.addWidget(self.btn_frame)

    def get_raw_input(self):
        state = getattr(self.parent_app, 'current_state', None)
        if not state:
            return 0.0, 0.0
        return (state.lx, state.ly) if self.is_left else (state.rx, state.ry)

    def start_sweep(self):
        self.calib_state = "SWEEP"
        self.btn_action.setText("Sweep 3x CW, 3x CCW")
        self.btn_action.setEnabled(False)

    def update_loop(self):
        raw_x, raw_y = self.get_raw_input()

        if self.calib_state == "REST":
            self.center_samples_x.append(raw_x)
            self.center_samples_y.append(raw_y)
            self.timer_ticks += 1
            if self.timer_ticks > 60:  # ~1 second
                self.center_x = sum(self.center_samples_x) / len(self.center_samples_x)
                self.center_y = sum(self.center_samples_y) / len(self.center_samples_y)
                self.calib_state = "WAIT_SWEEP"
                self.lbl_instruct.setText(
                    "Step 2: Push stick fully outward and rotate 3x CW, then 3x CCW.\nNOTE: Do NOT press joystick during sweep."
                )
                self.btn_action.setText("Start Sweep")
                self.btn_action.setEnabled(True)
                self.btn_action.clicked.connect(self.start_sweep)

        elif self.calib_state == "SWEEP":
            dx = raw_x - self.center_x
            dy = raw_y - self.center_y
            r = math.sqrt(dx**2 + dy**2)
            if r > 0.1:
                theta = int(math.degrees(math.atan2(dy, dx))) % 360

                if self.last_theta is not None:
                    delta = (theta - self.last_theta + 180) % 360 - 180
                    if delta > 0:
                        self.accum_ccw += delta
                    elif delta < 0:
                        self.accum_cw += abs(delta)

                    # Check rotational speed (too fast or too slow warnings)
                    if abs(delta) > 35:
                        self.speed_warn_timer = 40
                        self.lbl_warning.setText("⚠️ Rotating Too Fast! Slow Down.")
                    elif abs(delta) < 2 and r > 0.8:
                        self.speed_warn_timer = 40
                        self.lbl_warning.setText("⚠️ Rotate Faster to Complete Sweep.")

                self.last_theta = theta

                for i in range(-2, 3):
                    idx = (theta + i) % 360
                    if r > self.bounds_data[idx]:
                        self.bounds_data[idx] = r

            if self.speed_warn_timer > 0:
                self.speed_warn_timer -= 1
                if self.speed_warn_timer == 0:
                    self.lbl_warning.setText("")

            if self.accum_cw >= 3 * 360 and self.accum_ccw >= 3 * 360:
                if not self.btn_action.isEnabled():
                    self.btn_action.setText("Finish Calibration")
                    self.btn_action.setEnabled(True)
                    self.btn_action.clicked.disconnect()
                    self.btn_action.clicked.connect(self.finish_sweep)
            else:
                cw_rem = max(0, 3 - int(self.accum_cw / 360))
                ccw_rem = max(0, 3 - int(self.accum_ccw / 360))
                self.btn_action.setText(f"Sweep {cw_rem}x CW, {ccw_rem}x CCW")

        self.canvas.update_data(raw_x, raw_y, self.bounds_data)

    def interpolate_bounds(self):
        non_zeros = [(i, r) for i, r in enumerate(self.bounds_data) if r > 0]
        if not non_zeros:
            return
        for i in range(360):
            if self.bounds_data[i] == 0:
                left_idx = i
                while self.bounds_data[left_idx] == 0:
                    left_idx = (left_idx - 1) % 360
                right_idx = i
                while self.bounds_data[right_idx] == 0:
                    right_idx = (right_idx + 1) % 360

                left_r = self.bounds_data[left_idx]
                right_r = self.bounds_data[right_idx]

                dl = (i - left_idx) % 360
                dr = (right_idx - i) % 360
                total = dl + dr
                if total > 0:
                    self.bounds_data[i] = left_r * (dr / total) + right_r * (dl / total)

    def finish_sweep(self):
        self.calib_state = "DONE"
        self.update_timer.stop()
        self.interpolate_bounds()
        self.canvas.update_data(self.center_x, self.center_y, self.bounds_data)

        error_pct = math_utils.calculate_circularity_error(self.bounds_data)
        self.lbl_instruct.setText("✨ Calibration Complete!")
        self.lbl_result.setText(
            f"Average Circularity Error: {error_pct:.2f}%\nCenter Offset: ({self.center_x:.3f}, {self.center_y:.3f})"
        )

        self.btn_action.hide()
        self.btn_frame.show()

    def save_and_close(self):
        config = getattr(self.parent_app, 'config', getattr(self.parent_app, 'daemon_config', None))
        if config:
            if not config.has_section(self.section):
                config.add_section(self.section)

            bounds_str = ",".join(f"{r:.4f}" for r in self.bounds_data)
            config.set(self.section, 'circularity_center_x', str(round(self.center_x, 4)))
            config.set(self.section, 'circularity_center_y', str(round(self.center_y, 4)))
            config.set(self.section, 'circularity_bounds', bounds_str)

            current_mode = config.get(self.section, 'circularity_mode', fallback='disabled')
            if current_mode == 'disabled':
                config.set(self.section, 'circularity_mode', 'before')

            if hasattr(self.parent_app, 'save_config'):
                self.parent_app.save_config()

        if self.on_finish:
            self.on_finish()
        self.accept()
