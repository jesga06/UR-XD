"""
Analog Trigger Pressure Visualizer Component for PySide6 UI.
Renders trigger actuation levels with primary-to-neon gradient fills,
percentage overlays, digital trigger thresholds, and monitor refresh rate sync.
Optimized with zero-allocation hot-loop and cached QPen/QBrush primitives.
"""

import sys
import time

from PySide6.QtWidgets import QWidget, QApplication, QVBoxLayout
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient, QGuiApplication, QFont
)
from PySide6.QtCore import Qt, Slot


class TriggerBar(QWidget):
    """
    High-performance QWidget level meter for displaying analog trigger pressure
    and digital step thresholds with display refresh rate synchronization.
    """
    NOISE_THRESHOLD = 0.001

    def __init__(self, title: str = "Left Trigger", parent=None):
        super().__init__(parent)
        self.title = title
        self._value: float = 0.0  # 0.0 to 1.0
        self._digital_mode: bool = False
        self._digital_threshold: float = 0.1  # Threshold overlay marker

        # Refresh rate & FPS throttling variables
        self._last_paint_time: float = 0.0
        self._target_refresh_rate: float = 60.0
        self._frame_delay_sec: float = 1.0 / 60.0

        # Pre-allocated fonts
        self._font_title = QFont()
        self._font_title.setBold(True)
        self._font_title.setPointSize(9)

        self._font_digital = QFont()
        self._font_digital.setBold(True)
        self._font_digital.setPointSize(7)

        self._font_pct = QFont()
        self._font_pct.setBold(True)
        self._font_pct.setPointSize(9)

        # Pre-allocated pens & brushes
        self._card_bg_brush = QBrush()
        self._border_pen = QPen()
        self._title_pen = QPen()
        self._digital_mode_pen = QPen()
        self._track_bg_brush = QBrush()
        self._digital_thresh_pen = QPen(Qt.PenStyle.DashLine)
        self._pct_pen = QPen()

        self._accent_1 = QColor("#a855f7")
        self._accent_2 = QColor("#00f5a0")

        self.setMinimumSize(180, 50)
        self.setMaximumHeight(65)
        self._setup_screen_refresh_sync()
        self._setup_theme_sync()

    def _setup_theme_sync(self) -> None:
        """Connects ThemeManager signal and initializes cached theme pens/brushes."""
        try:
            from gui_v2.services.theme_manager import ThemeManager
            tm = ThemeManager.get_instance()
            tm.theme_changed.connect(self._update_theme_cache)
            self._update_theme_cache(tm.get_all_tokens())
        except Exception:
            self._fallback_theme_cache()

    def _fallback_theme_cache(self) -> None:
        bg_color = QColor("#161024")
        accent_1 = QColor("#a855f7")
        accent_2 = QColor("#00f5a0")
        self._rebuild_primitives(bg_color, accent_1, accent_2)

    @Slot(dict)
    def _update_theme_cache(self, tokens: dict) -> None:
        """Cache all QPen and QBrush objects from theme tokens to eliminate hot-loop allocations."""
        try:
            from gui_v2.services.theme_manager import ThemeManager
            tm = ThemeManager.get_instance()
            bg_color = tm.get_color("background")
            accent_1 = tm.get_color("accent_1")
            accent_2 = tm.get_color("accent_2")
            self._rebuild_primitives(bg_color, accent_1, accent_2)
            self.update()
        except Exception:
            self._fallback_theme_cache()

    def _rebuild_primitives(self, bg_color: QColor, accent_1: QColor, accent_2: QColor) -> None:
        self._accent_1 = accent_1
        self._accent_2 = accent_2

        card_bg = QColor(bg_color.red(), bg_color.green(), bg_color.blue(), 215)
        self._card_bg_brush.setStyle(Qt.BrushStyle.SolidPattern)
        self._card_bg_brush.setColor(card_bg)

        self._border_pen.setColor(QColor(accent_1.red(), accent_1.green(), accent_1.blue(), 90))
        self._border_pen.setWidthF(1.5)

        self._title_pen.setColor(QColor(255, 255, 255, 220))
        self._digital_mode_pen.setColor(QColor("#f59e0b"))

        track_bg = QColor(bg_color.red() // 2, bg_color.green() // 2, bg_color.blue() // 2, 240)
        self._track_bg_brush.setStyle(Qt.BrushStyle.SolidPattern)
        self._track_bg_brush.setColor(track_bg)

        self._digital_thresh_pen.setColor(QColor("#f59e0b"))
        self._digital_thresh_pen.setWidth(2)

        self._pct_pen.setColor(QColor("#ffffff"))

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

    @Slot(float)
    def update_level(self, value: float) -> None:
        """Updates trigger pressure float value [0.0, 1.0] with smart repaint invalidation."""
        new_val = max(0.0, min(1.0, float(value)))
        if abs(self._value - new_val) < self.NOISE_THRESHOLD:
            return

        self._value = new_val
        now = time.perf_counter()
        if (now - self._last_paint_time) >= self._frame_delay_sec:
            self.update()

    @Slot(bool)
    def set_digital_mode(self, enabled: bool) -> None:
        """Toggles digital binary trigger mode visualization overlay."""
        self._digital_mode = bool(enabled)
        self.update()

    def paintEvent(self, event) -> None:
        """Custom QPainter rendering loop with cached primitives."""
        now = time.perf_counter()
        if self._last_paint_time > 0 and (now - self._last_paint_time) < (self._frame_delay_sec * 0.85):
            return
        self._last_paint_time = now

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()

        # 1. Glassmorphic Background Card
        painter.setBrush(self._card_bg_brush)
        painter.setPen(self._border_pen)
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 8, 8)

        # Title Overlay
        painter.setPen(self._title_pen)
        painter.setFont(self._font_title)
        painter.drawText(rect.adjusted(10, 4, -10, -4), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, self.title)

        # Digital Mode Badge
        if self._digital_mode:
            painter.setPen(self._digital_mode_pen)
            painter.setFont(self._font_digital)
            painter.drawText(rect.adjusted(10, 5, -10, -5), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop, "DIGITAL MODE")

        # 2. Inner Track Bar Area
        track_rect = rect.adjusted(10, 22, -10, -8)
        painter.setBrush(self._track_bg_brush)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(track_rect, 4, 4)

        # 3. Proportional Level Meter Fill (Gradient accent_1 -> accent_2)
        fill_width = int(track_rect.width() * self._value)
        if fill_width > 0:
            fill_rect = track_rect.adjusted(0, 0, -(track_rect.width() - fill_width), 0)
            gradient = QLinearGradient(fill_rect.topLeft(), fill_rect.topRight())
            gradient.setColorAt(0.0, self._accent_1)
            gradient.setColorAt(1.0, self._accent_2)

            painter.setBrush(gradient)
            painter.drawRoundedRect(fill_rect, 4, 4)

        # 4. Digital Mode Threshold Indicator Line
        if self._digital_mode:
            thresh_x = track_rect.left() + int(track_rect.width() * self._digital_threshold)
            painter.setPen(self._digital_thresh_pen)
            painter.drawLine(thresh_x, track_rect.top() - 2, thresh_x, track_rect.bottom() + 2)

        # 5. Percentage Overlay Readout
        pct_text = f"{self._value * 100.0:.1f}%"
        painter.setPen(self._pct_pen)
        painter.setFont(self._font_pct)
        painter.drawText(track_rect, Qt.AlignmentFlag.AlignCenter, pct_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("TriggerBar Test")
    window.resize(300, 150)
    layout = QVBoxLayout(window)

    trig_left = TriggerBar("Left Trigger (LT)")
    trig_right = TriggerBar("Right Trigger (RT)")
    trig_right.set_digital_mode(True)

    layout.addWidget(trig_left)
    layout.addWidget(trig_right)

    window.show()

    from PySide6.QtCore import QTimer
    val = [0.0]
    dir_up = [True]

    def tick():
        if dir_up[0]:
            val[0] += 0.02
            if val[0] >= 1.0:
                val[0] = 1.0
                dir_up[0] = False
        else:
            val[0] -= 0.02
            if val[0] <= 0.0:
                val[0] = 0.0
                dir_up[0] = True

        trig_left.update_level(val[0])
        trig_right.update_level(1.0 - val[0])

    timer = QTimer()
    timer.timeout.connect(tick)
    timer.start(16)

    sys.exit(app.exec())
