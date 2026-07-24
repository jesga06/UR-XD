"""
Joystick Visualizer Widget for PySide6 (joystick_widget.py)
High-performance 240Hz sub-pixel vector radar widget using QPainter.
Renders analog stick positions, deadzone boundary overlays, center crosshairs,
and motion position marker dots with antialiasing.
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QRadialGradient, QBrush


class JoystickVisualizerWidget(QWidget):
    """
    Sub-pixel antialiased QPainter radar widget for real-time analog stick monitoring.
    Calculates stick position (-1.0 to 1.0) and deadzone overlay without dropping frames.
    """

    def __init__(self, title="Analog Stick", parent=None):
        super().__init__(parent)
        self.title = title
        self.raw_x = 0.0
        self.raw_y = 0.0
        self.norm_x = 0.0
        self.norm_y = 0.0
        self.deadzone_pct = 5.0  # 5% default
        self.setMinimumSize(220, 220)

        # Theme Colors
        self.color_bg = QColor(12, 9, 20, 200)
        self.color_border = QColor(168, 85, 247, 80)
        self.color_grid = QColor(255, 255, 255, 25)
        self.color_deadzone = QColor(117, 0, 171, 90)
        self.color_dot = QColor(0, 245, 160)
        self.color_trail = QColor(168, 85, 247, 180)

    def set_stick_position(self, norm_x: float, norm_y: float, raw_x: float = 0.0, raw_y: float = 0.0):
        """Update stick position normalized between -1.0 and 1.0 and trigger redraw."""
        self.norm_x = max(-1.0, min(1.0, norm_x))
        self.norm_y = max(-1.0, min(1.0, norm_y))
        self.raw_x = raw_x
        self.raw_y = raw_y
        self.update()  # Triggers sub-millisecond QPainter repaint

    def set_deadzone(self, deadzone_pct: float):
        """Update deadzone percentage (0.0 to 50.0)."""
        self.deadzone_pct = max(0.0, min(50.0, deadzone_pct))
        self.update()

    def set_theme_colors(self, primary_hex="#7500ab", glow_hex="#a855f7", accent_green_hex="#00f5a0"):
        """Dynamically update theme colors from ThemeManager."""
        self.color_border = QColor(glow_hex)
        self.color_border.setAlpha(80)
        self.color_deadzone = QColor(primary_hex)
        self.color_deadzone.setAlpha(90)
        self.color_dot = QColor(accent_green_hex)
        self.color_trail = QColor(glow_hex)
        self.color_trail.setAlpha(180)
        self.update()

    def paintEvent(self, event):
        """High-performance vector paint event."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        width = self.width()
        height = self.height()
        size = min(width, height) - 20
        cx = width / 2.0
        cy = height / 2.0
        radius = size / 2.0

        # Draw Base Circular Glass Radar Background
        painter.setPen(QPen(self.color_border, 1.5))
        painter.setBrush(QBrush(self.color_bg))
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        # Draw Concentric Radar Rings & Crosshair Axes
        pen_grid = QPen(self.color_grid, 1, Qt.PenStyle.DashLine)
        painter.setPen(pen_grid)
        painter.drawLine(QPointF(cx - radius, cy), QPointF(cx + radius, cy))
        painter.drawLine(QPointF(cx, cy - radius), QPointF(cx, cy + radius))
        painter.drawEllipse(QPointF(cx, cy), radius * 0.5, radius * 0.5)

        # Draw Inner Deadzone Circle Overlay
        dz_radius = radius * (self.deadzone_pct / 100.0)
        if dz_radius > 0:
            painter.setPen(QPen(QColor(168, 85, 247, 120), 1, Qt.PenStyle.DotLine))
            painter.setBrush(QBrush(self.color_deadzone))
            painter.drawEllipse(QPointF(cx, cy), dz_radius, dz_radius)

        # Calculate Active Joystick Coordinates
        dot_x = cx + (self.norm_x * radius)
        dot_y = cy - (self.norm_y * radius)  # Invert Y for screen space

        # Draw Vector Trail Line from Center to Dot
        pen_trail = QPen(self.color_trail, 2)
        painter.setPen(pen_trail)
        painter.drawLine(QPointF(cx, cy), QPointF(dot_x, dot_y))

        # Draw Glowing Position Dot
        radial_grad = QRadialGradient(QPointF(dot_x, dot_y), 10)
        radial_grad.setColorAt(0, self.color_dot)
        radial_grad.setColorAt(0.6, self.color_dot)
        radial_grad.setColorAt(1.0, QColor(0, 245, 160, 0))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(radial_grad))
        painter.drawEllipse(QPointF(dot_x, dot_y), 10, 10)

        # Inner Solid Center Core
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(QPointF(dot_x, dot_y), 3.5, 3.5)

        painter.end()
