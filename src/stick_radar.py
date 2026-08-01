"""
Hardware-Accelerated Analog Stick Radar Canvas for PySide6 UI.
Provides high-FPS monitor-synchronized visualization of analog stick telemetry,
deadzones, unit boundaries, and 360-degree circularity distortion polygons
with zero-allocation hot-loops and cached rendering primitives.
"""

import sys
import time
import math
from typing import List

from PySide6.QtWidgets import QWidget, QApplication, QVBoxLayout
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPolygonF, QGuiApplication, QFont
)
from PySide6.QtCore import Qt, QPointF, Slot


class StickRadar(QWidget):
    """
    High-performance QWidget canvas for displaying analog joystick vectors
    and circularity distortion maps with monitor refresh rate synchronization.
    """
    NOISE_THRESHOLD = 0.0005

    def __init__(self, title: str = "Left Stick", parent=None):
        super().__init__(parent)
        self.title = title
        self._x: float = 0.0
        self._y: float = 0.0
        self._out_x: float = 0.0
        self._out_y: float = 0.0
        self._deadzone: float = 0.08
        self._circularity_bounds: List[float] = []

        # Cached geometry calculations
        self._cached_poly = QPolygonF()
        self._poly_dirty = True

        # Throttling & refresh rate variables
        self._last_paint_time: float = 0.0
        self._target_refresh_rate: float = 60.0
        self._frame_delay_sec: float = 1.0 / 60.0

        # Pre-allocated fonts
        self._font_title = QFont()
        self._font_title.setBold(True)
        self._font_title.setPointSize(9)

        self._font_coords = QFont()
        self._font_coords.setBold(False)
        self._font_coords.setPointSize(8)

        # Pre-allocated rendering primitives (Cached Theme Pens & Brushes)
        self._card_bg_brush = QBrush()
        self._border_pen = QPen()
        self._grid_pen = QPen(Qt.PenStyle.DashLine)
        self._outer_pen = QPen(Qt.PenStyle.SolidLine)
        self._poly_pen = QPen(Qt.PenStyle.SolidLine)
        self._poly_brush = QBrush()
        self._dz_pen = QPen(Qt.PenStyle.DashLine)
        self._dz_brush = QBrush()
        self._raw_line_pen = QPen(Qt.PenStyle.DotLine)
        self._raw_dot_brush = QBrush()
        self._out_line_pen = QPen(Qt.PenStyle.SolidLine)
        self._out_dot_brush = QBrush()
        self._title_pen = QPen()
        self._coords_pen = QPen()

        self.setMinimumSize(180, 180)
        self._setup_screen_refresh_sync()
        self._setup_theme_sync()

    def _setup_theme_sync(self) -> None:
        """Connects ThemeManager signal and initializes cached theme pens/brushes."""
        try:
            from gui_v2.services.theme_manager import ThemeManager
            tm = ThemeManager.get_instance()
            tm.staging_changed.connect(self._update_theme_cache)
            tm.theme_changed.connect(self._update_theme_cache)
            self._update_theme_cache(tm.get_all_tokens())
        except Exception:
            self._fallback_theme_cache()

    def _fallback_theme_cache(self) -> None:
        graph_bg = QColor("#0C0914")
        graph_axis = QColor("#A855F7")
        accent_1 = QColor("#A855F7")
        accent_2 = QColor("#00F5A0")
        outline = QColor("#A855F7")
        self._rebuild_primitives(graph_bg, graph_axis, accent_1, accent_2, outline)

    @Slot(dict)
    def _update_theme_cache(self, tokens: dict) -> None:
        """Cache all QPen and QBrush objects from theme tokens to eliminate hot-loop allocations."""
        try:
            from gui_v2.services.theme_manager import ThemeManager
            tm = ThemeManager.get_instance()
            graph_bg = tm.get_color("graph_bg")
            graph_axis = tm.get_color("graph_axis")
            accent_1 = tm.get_color("accent_1")
            accent_2 = tm.get_color("accent_2")
            outline = tm.get_color("outline")
            self._rebuild_primitives(graph_bg, graph_axis, accent_1, accent_2, outline)
            self.update()
        except Exception:
            self._fallback_theme_cache()

    def _rebuild_primitives(
        self, graph_bg: QColor, graph_axis: QColor,
        accent_1: QColor, accent_2: QColor, outline: QColor
    ) -> None:
        card_bg = QColor(graph_bg.red(), graph_bg.green(), graph_bg.blue(), 230)
        self._card_bg_brush.setStyle(Qt.BrushStyle.SolidPattern)
        self._card_bg_brush.setColor(card_bg)

        self._border_pen.setColor(QColor(outline.red(), outline.green(), outline.blue(), 120))
        self._border_pen.setWidthF(1.5)

        self._title_pen.setColor(QColor(255, 255, 255, 220))
        self._coords_pen.setColor(QColor(accent_1.red(), accent_1.green(), accent_1.blue(), 200))

        self._grid_pen.setColor(graph_axis)
        self._grid_pen.setWidthF(1.0)

        self._outer_pen.setColor(graph_axis)
        self._outer_pen.setWidthF(1.5)

        self._poly_pen.setColor(QColor(accent_1.red(), accent_1.green(), accent_1.blue(), 200))
        self._poly_pen.setWidthF(1.5)
        self._poly_brush.setStyle(Qt.BrushStyle.SolidPattern)
        self._poly_brush.setColor(QColor(accent_1.red(), accent_1.green(), accent_1.blue(), 45))

        self._dz_pen.setColor(QColor(239, 68, 68, 140))
        self._dz_pen.setWidthF(1.2)
        self._dz_brush.setStyle(Qt.BrushStyle.SolidPattern)
        self._dz_brush.setColor(QColor(239, 68, 68, 25))

        self._raw_line_pen.setColor(QColor(accent_1.red(), accent_1.green(), accent_1.blue(), 180))
        self._raw_line_pen.setWidthF(1.5)

        self._raw_dot_brush.setStyle(Qt.BrushStyle.SolidPattern)
        self._raw_dot_brush.setColor(accent_1)

        self._out_line_pen.setColor(QColor(accent_2.red(), accent_2.green(), accent_2.blue(), 180))
        self._out_line_pen.setWidthF(1.5)

        self._out_dot_brush.setStyle(Qt.BrushStyle.SolidPattern)
        self._out_dot_brush.setColor(accent_2)

    def _setup_screen_refresh_sync(self) -> None:
        """Queries screen refresh rate and connects to signals for dynamic rescaling."""
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
        """Calculates frame delay based on active display refresh rate."""
        self._target_refresh_rate = max(30.0, rate)
        frame_delay_ms = max(1.0, 1000.0 / self._target_refresh_rate)
        self._frame_delay_sec = frame_delay_ms / 1000.0

    @Slot(float, float)
    def update_telemetry(self, x: float, y: float) -> None:
        """Updates normalized joystick coordinates [-1.0, 1.0] with smart repaint invalidation."""
        nx = max(-1.0, min(1.0, float(x)))
        ny = max(-1.0, min(1.0, float(y)))

        # Smart repaint threshold guard
        if abs(self._x - nx) < self.NOISE_THRESHOLD and abs(self._y - ny) < self.NOISE_THRESHOLD:
            return

        self._x = nx
        self._y = ny

        now = time.perf_counter()
        if (now - self._last_paint_time) >= self._frame_delay_sec:
            self.update()

    @Slot(float, float)
    def update_output_telemetry(self, out_x: float, out_y: float) -> None:
        """Updates tuned/virtual output coordinates."""
        nox = max(-1.0, min(1.0, float(out_x)))
        noy = max(-1.0, min(1.0, float(out_y)))

        if abs(self._out_x - nox) < self.NOISE_THRESHOLD and abs(self._out_y - noy) < self.NOISE_THRESHOLD:
            return

        self._out_x = nox
        self._out_y = noy

        now = time.perf_counter()
        if (now - self._last_paint_time) >= self._frame_delay_sec:
            self.update()

    @Slot(list)
    def set_circularity_bounds(self, bounds: List[float]) -> None:
        """Updates the 360-degree circularity boundary radii list."""
        self._circularity_bounds = [float(b) for b in bounds]
        self._poly_dirty = True
        self.update()

    @Slot(float)
    def set_deadzone(self, dz: float) -> None:
        """Updates the visual inner deadzone radius [0.0, 1.0]."""
        new_dz = max(0.0, min(1.0, float(dz)))
        if abs(self._deadzone - new_dz) >= self.NOISE_THRESHOLD:
            self._deadzone = new_dz
            self.update()

    def paintEvent(self, event) -> None:
        """Zero-allocation custom QPainter rendering loop."""
        now = time.perf_counter()
        if self._last_paint_time > 0 and (now - self._last_paint_time) < (self._frame_delay_sec * 0.85):
            return
        self._last_paint_time = now

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        w, h = rect.width(), rect.height()
        margin = 15
        side = min(w, h) - (margin * 2)
        cx, cy = w / 2.0, h / 2.0 + 8.0
        radius = side / 2.0

        # 1. Glassmorphic Card Outer Frame
        painter.setBrush(self._card_bg_brush)
        painter.setPen(self._border_pen)
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 12, 12)

        # Title Overlay
        painter.setPen(self._title_pen)
        painter.setFont(self._font_title)
        painter.drawText(rect.adjusted(10, 6, -10, -6), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, self.title)

        # Coordinates readout overlay
        coords_str = f"X: {self._x:+.2f}  Y: {self._y:+.2f}"
        painter.setPen(self._coords_pen)
        painter.setFont(self._font_coords)
        painter.drawText(rect.adjusted(10, 6, -10, -6), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop, coords_str)

        # 2. Axis Crosshairs
        painter.setPen(self._grid_pen)
        painter.drawLine(int(cx - radius), int(cy), int(cx + radius), int(cy))
        painter.drawLine(int(cx), int(cy - radius), int(cx), int(cy + radius))

        # 3. Outer Unit Circle
        painter.setPen(self._outer_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        # 4. Circularity Distortion Polygon (Rebuilt only when dirty)
        if self._circularity_bounds and len(self._circularity_bounds) >= 3:
            if self._poly_dirty:
                self._cached_poly.clear()
                n = len(self._circularity_bounds)
                for i, bound_r in enumerate(self._circularity_bounds):
                    angle = (2.0 * math.pi * i) / n
                    px = cx + bound_r * radius * math.cos(angle)
                    py = cy - bound_r * radius * math.sin(angle)
                    self._cached_poly.append(QPointF(px, py))
                self._poly_dirty = False

            painter.setPen(self._poly_pen)
            painter.setBrush(self._poly_brush)
            painter.drawPolygon(self._cached_poly)

        # 5. Inner Deadzone Circle Boundary
        if self._deadzone > 0.0:
            dz_radius = radius * self._deadzone
            painter.setPen(self._dz_pen)
            painter.setBrush(self._dz_brush)
            painter.drawEllipse(QPointF(cx, cy), dz_radius, dz_radius)

        # 6. Real-time Telemetry Vector Line & Position Dot
        dot_x = cx + self._x * radius
        dot_y = cy - self._y * radius

        if abs(self._x) > 0.001 or abs(self._y) > 0.001:
            painter.setPen(self._raw_line_pen)
            painter.drawLine(QPointF(cx, cy), QPointF(dot_x, dot_y))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._raw_dot_brush)
        painter.drawEllipse(QPointF(dot_x, dot_y), 6.0, 6.0)

        # Output Dot (Tuned)
        if abs(self._out_x) > 0.001 or abs(self._out_y) > 0.001:
            out_dot_x = cx + self._out_x * radius
            out_dot_y = cy - self._out_y * radius
            painter.setPen(self._out_line_pen)
            painter.drawLine(QPointF(cx, cy), QPointF(out_dot_x, out_dot_y))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self._out_dot_brush)
            painter.drawEllipse(QPointF(out_dot_x, out_dot_y), 5.0, 5.0)


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

    from PySide6.QtCore import QTimer
    angle = [0.0]

    def tick():
        angle[0] += 0.05
        radar.update_telemetry(math.cos(angle[0]) * 0.8, math.sin(angle[0]) * 0.8)

    timer = QTimer()
    timer.timeout.connect(tick)
    timer.start(16)

    sys.exit(app.exec())
