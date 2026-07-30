"""
Hardware-Accelerated Analog Stick Radar Canvas for PySide6 UI.
Provides high-FPS monitor-synchronized visualization of analog stick telemetry,
deadzones, unit boundaries, and 360-degree circularity distortion polygons.
"""

import sys
import time
import math
from typing import List

from PySide6.QtWidgets import QWidget, QApplication, QVBoxLayout
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPolygonF, QGuiApplication
)
from PySide6.QtCore import Qt, QPointF, Slot


class StickRadar(QWidget):
    """
    High-performance QWidget canvas for displaying analog joystick vectors
    and circularity distortion maps with monitor refresh rate synchronization.
    """
    def __init__(self, title: str = "Left Stick", parent=None):
        super().__init__(parent)
        self.title = title
        self._x: float = 0.0
        self._y: float = 0.0
        self._deadzone: float = 0.08
        self._circularity_bounds: List[float] = []

        # Refresh rate & FPS throttling variables
        self._last_paint_time: float = 0.0
        self._target_refresh_rate: float = 60.0
        self._frame_delay_sec: float = 1.0 / 60.0

        self.setMinimumSize(180, 180)
        self._setup_screen_refresh_sync()

    def _setup_screen_refresh_sync(self) -> None:
        """
        Queries screen refresh rate and connects to signals for dynamic rescaling.
        """
        screen = QGuiApplication.primaryScreen()
        if screen:
            self._update_refresh_rate(screen.refreshRate())
            screen.refreshRateChanged.connect(self._update_refresh_rate)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self.window() and self.window().windowHandle():
            screen = self.window().windowHandle().screen()
            if screen:
                self._update_refresh_rate(screen.refreshRate())
                screen.refreshRateChanged.connect(self._update_refresh_rate)

    @Slot(float)
    def _update_refresh_rate(self, rate: float) -> None:
        """
        Calculates frame delay based on active display refresh rate.
        """
        self._target_refresh_rate = max(30.0, rate)
        # Compute frame delay in seconds: max(1ms, 1000ms / rate) -> convert to sec
        frame_delay_ms = max(1.0, 1000.0 / self._target_refresh_rate)
        self._frame_delay_sec = frame_delay_ms / 1000.0

    @Slot(float, float)
    def update_telemetry(self, x: float, y: float) -> None:
        """
        Updates normalized joystick coordinates [-1.0, 1.0] and triggers repaint
        if throttling guard permits.
        """
        self._x = max(-1.0, min(1.0, float(x)))
        self._y = max(-1.0, min(1.0, float(y)))

        now = time.perf_counter()
        if (now - self._last_paint_time) >= self._frame_delay_sec:
            self.update()

    @Slot(list)
    def set_circularity_bounds(self, bounds: List[float]) -> None:
        """
        Updates the 360-degree circularity boundary radii list.
        """
        self._circularity_bounds = [float(b) for b in bounds]
        self.update()

    @Slot(float)
    def set_deadzone(self, dz: float) -> None:
        """
        Updates the visual inner deadzone radius [0.0, 1.0].
        """
        self._deadzone = max(0.0, min(1.0, float(dz)))
        self.update()

    def paintEvent(self, event) -> None:
        """
        Custom QPainter rendering loop with hardware throttling guard.
        """
        now = time.perf_counter()
        # Throttling guard: if called faster than display refresh, skip paint
        if self._last_paint_time > 0 and (now - self._last_paint_time) < (self._frame_delay_sec * 0.85):
            return
        self._last_paint_time = now

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        w, h = rect.width(), rect.height()
        margin = 15
        side = min(w, h) - (margin * 2)
        cx, cy = w / 2.0, h / 2.0 + 8.0 # Shift down slightly for header
        radius = side / 2.0

        # 1. Glassmorphic Card Outer Frame (#161024 background, rgba(168,85,247,0.35) border)
        painter.setBrush(QColor("#161024"))
        border_pen = QPen(QColor(168, 85, 247, 90), 1.5)
        painter.setPen(border_pen)
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 12, 12)

        # Title Overlay
        painter.setPen(QColor(255, 255, 255, 220))
        font = painter.font()
        font.setBold(True)
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(rect.adjusted(10, 6, -10, -6), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, self.title)

        # Coordinates readout overlay
        coords_str = f"X: {self._x:+.2f}  Y: {self._y:+.2f}"
        painter.setPen(QColor(168, 85, 247, 200))
        font_sub = painter.font()
        font_sub.setPointSize(8)
        font_sub.setBold(False)
        painter.setFont(font_sub)
        painter.drawText(rect.adjusted(10, 6, -10, -6), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop, coords_str)

        # 2. Axis Crosshairs
        grid_pen = QPen(QColor(168, 85, 247, 50), 1, Qt.PenStyle.DashLine)
        painter.setPen(grid_pen)
        painter.drawLine(int(cx - radius), int(cy), int(cx + radius), int(cy))
        painter.drawLine(int(cx), int(cy - radius), int(cx), int(cy + radius))

        # 3. Outer Unit Circle (1.0 Magnitude Boundary)
        outer_pen = QPen(QColor(168, 85, 247, 120), 1.5, Qt.PenStyle.SolidLine)
        painter.setPen(outer_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        # 4. Circularity Distortion Polygon
        if self._circularity_bounds and len(self._circularity_bounds) >= 3:
            poly = QPolygonF()
            n = len(self._circularity_bounds)
            for i, bound_r in enumerate(self._circularity_bounds):
                angle = (2.0 * math.pi * i) / n
                px = cx + bound_r * radius * math.cos(angle)
                py = cy - bound_r * radius * math.sin(angle)
                poly.append(QPointF(px, py))

            poly_pen = QPen(QColor(117, 0, 171, 200), 1.5, Qt.PenStyle.SolidLine)
            poly_brush = QBrush(QColor(168, 85, 247, 45))
            painter.setPen(poly_pen)
            painter.setBrush(poly_brush)
            painter.drawPolygon(poly)

        # 5. Inner Deadzone Circle Boundary
        if self._deadzone > 0.0:
            dz_radius = radius * self._deadzone
            dz_pen = QPen(QColor(239, 68, 68, 140), 1.2, Qt.PenStyle.DashLine)
            painter.setPen(dz_pen)
            painter.setBrush(QColor(239, 68, 68, 25))
            painter.drawEllipse(QPointF(cx, cy), dz_radius, dz_radius)

        # 6. Real-time Telemetry Vector Line & Position Dot
        dot_x = cx + self._x * radius
        dot_y = cy - self._y * radius # Invert Y so positive is up on GUI

        # Dotted trailing vector line
        if abs(self._x) > 0.001 or abs(self._y) > 0.001:
            line_pen = QPen(QColor(168, 85, 247, 200), 1.5, Qt.PenStyle.DotLine)
            painter.setPen(line_pen)
            painter.drawLine(QPointF(cx, cy), QPointF(dot_x, dot_y))

        # Position Dot (No outline pen, neon purple brush, radius 6.0)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#a855f7"))
        painter.drawEllipse(QPointF(dot_x, dot_y), 6.0, 6.0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("StickRadar Test")
    window.resize(300, 300)
    layout = QVBoxLayout(window)

    radar = StickRadar("Left Stick (Test)")
    radar.set_deadzone(0.12)
    radar.set_circularity_bounds([1.0, 0.95, 1.05, 0.98, 1.02, 0.9, 1.0, 0.96])
    layout.addWidget(radar)

    window.show()

    # Simulate 60Hz telemetry updates
    from PySide6.QtCore import QTimer
    angle = [0.0]

    def tick():
        angle[0] += 0.05
        radar.update_telemetry(math.cos(angle[0]) * 0.8, math.sin(angle[0]) * 0.8)

    timer = QTimer()
    timer.timeout.connect(tick)
    timer.start(16)

    sys.exit(app.exec())
