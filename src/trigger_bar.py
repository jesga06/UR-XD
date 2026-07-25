"""
Analog Trigger Pressure Visualizer Component for PySide6 UI.
Renders trigger actuation levels with primary-to-neon gradient fills,
percentage overlays, digital trigger thresholds, and monitor refresh rate sync.
"""

import sys
import time

from PySide6.QtWidgets import QWidget, QApplication, QVBoxLayout
from PySide6.QtGui import (
    QPainter, QColor, QPen, QLinearGradient, QGuiApplication
)
from PySide6.QtCore import Qt, Slot


class TriggerBar(QWidget):
    """
    High-performance QWidget level meter for displaying analog trigger pressure
    and digital step thresholds with display refresh rate synchronization.
    """
    def __init__(self, title: str = "Left Trigger", parent=None):
        super().__init__(parent)
        self.title = title
        self._value: float = 0.0 # 0.0 to 1.0
        self._digital_mode: bool = False
        self._digital_threshold: float = 0.1 # Threshold overlay marker

        # Refresh rate & FPS throttling variables
        self._last_paint_time: float = 0.0
        self._target_refresh_rate: float = 60.0
        self._frame_delay_sec: float = 1.0 / 60.0

        self.setMinimumSize(180, 50)
        self.setMaximumHeight(65)
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
        frame_delay_ms = max(1.0, 1000.0 / self._target_refresh_rate)
        self._frame_delay_sec = frame_delay_ms / 1000.0

    @Slot(float)
    def update_level(self, value: float) -> None:
        """
        Updates trigger pressure float value [0.0, 1.0] and triggers repaint.
        """
        self._value = max(0.0, min(1.0, float(value)))
        now = time.perf_counter()
        if (now - self._last_paint_time) >= self._frame_delay_sec:
            self.update()

    @Slot(bool)
    def set_digital_mode(self, enabled: bool) -> None:
        """
        Toggles digital binary trigger mode visualization overlay.
        """
        self._digital_mode = bool(enabled)
        self.update()

    def paintEvent(self, event) -> None:
        """
        Custom QPainter rendering loop with hardware throttling guard.
        """
        now = time.perf_counter()
        if self._last_paint_time > 0 and (now - self._last_paint_time) < (self._frame_delay_sec * 0.85):
            return
        self._last_paint_time = now

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()

        # 1. Glassmorphic Background Card (#161024 background, rgba(168,85,247,0.35) border)
        painter.setBrush(QColor("#161024"))
        painter.setPen(QPen(QColor(168, 85, 247, 90), 1.5))
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 8, 8)

        # Title Overlay
        painter.setPen(QColor(255, 255, 255, 220))
        font = painter.font()
        font.setBold(True)
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(rect.adjusted(10, 4, -10, -4), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, self.title)

        # Digital Mode Badge
        if self._digital_mode:
            painter.setPen(QColor("#f59e0b"))
            font_small = painter.font()
            font_small.setPointSize(7)
            font_small.setBold(True)
            painter.setFont(font_small)
            painter.drawText(rect.adjusted(10, 5, -10, -5), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop, "DIGITAL MODE")

        # 2. Inner Track Bar Area
        track_rect = rect.adjusted(10, 22, -10, -8)
        painter.setBrush(QColor(10, 6, 18))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(track_rect, 4, 4)

        # 3. Proportional Level Meter Fill (Gradient #7500ab -> #a855f7)
        fill_width = int(track_rect.width() * self._value)
        if fill_width > 0:
            fill_rect = track_rect.adjusted(0, 0, -(track_rect.width() - fill_width), 0)
            gradient = QLinearGradient(fill_rect.topLeft(), fill_rect.topRight())
            gradient.setColorAt(0.0, QColor("#7500ab"))
            gradient.setColorAt(1.0, QColor("#a855f7"))

            painter.setBrush(gradient)
            painter.drawRoundedRect(fill_rect, 4, 4)

        # 4. Digital Mode Threshold Indicator Line
        if self._digital_mode:
            thresh_x = track_rect.left() + int(track_rect.width() * self._digital_threshold)
            painter.setPen(QPen(QColor("#f59e0b"), 2, Qt.PenStyle.DashLine))
            painter.drawLine(thresh_x, track_rect.top() - 2, thresh_x, track_rect.bottom() + 2)

        # 5. Percentage Overlay Readout
        pct_text = f"{self._value * 100.0:.1f}%"
        painter.setPen(QColor("#ffffff"))
        font_pct = painter.font()
        font_pct.setBold(True)
        font_pct.setPointSize(9)
        painter.setFont(font_pct)
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

    # Simulate trigger pressure sweep
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
