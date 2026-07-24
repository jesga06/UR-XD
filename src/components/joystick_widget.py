"""
Joystick Visualizer Widget for PySide6 (joystick_widget.py)
High-performance 240Hz sub-pixel vector radar widget using QPainter.
Renders squared outer boundary with inner circular radar crosshairs,
dynamic growing inner deadzone ring, and dual position dots for raw input vs modified output.
"""

import math
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QRadialGradient, QBrush


class JoystickVisualizerWidget(QWidget):
    """
    Sub-pixel antialiased QPainter radar widget for real-time analog stick monitoring.
    Features squared outer boundary box, inner circular radar crosshairs,
    growing inner deadzone ring, and dual raw vs modified position dots.
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
        self.color_bg = QColor(12, 9, 20, 230)
        self.color_border = QColor(168, 85, 247, 100)
        self.color_grid = QColor(255, 255, 255, 30)
        self.color_deadzone = QColor(168, 85, 247, 70)
        self.color_raw_dot = QColor(251, 146, 60, 180)  # Orange for raw input
        self.color_mod_dot = QColor(0, 245, 160)       # Green for tuned output
        self.color_trail = QColor(168, 85, 247, 180)
        self.circularity_mode = "disabled"
        self.show_circularity_bounds = True

    def set_circularity_mode(self, mode: str):
        """Set circularity compensation mode ('disabled', 'before', 'after')."""
        self.circularity_mode = mode.lower()
        self.update()

    def set_stick_position(self, x: float, y: float, raw_x: float = None, raw_y: float = None):
        """Set normalized stick position (-1.0 to 1.0) and update canvas."""
        self.norm_x = max(-1.0, min(1.0, float(x)))
        self.norm_y = max(-1.0, min(1.0, float(y)))
        self.raw_x = max(-1.0, min(1.0, float(raw_x if raw_x is not None else x)))
        self.raw_y = max(-1.0, min(1.0, float(raw_y if raw_y is not None else y)))
        self.update()

    def set_deadzone(self, deadzone_pct: float):
        """Set deadzone percentage [0, 100] to scale inner deadzone ring overlay."""
        self.deadzone_pct = deadzone_pct
        self.update()

    def set_theme_colors(self, primary_hex="#7500ab", glow_hex="#a855f7", accent_green_hex="#00f5a0"):
        """Dynamically update theme colors from ThemeManager."""
        self.color_border = QColor(glow_hex)
        self.color_border.setAlpha(80)
        self.color_mod_dot = QColor(accent_green_hex)
        self.color_trail = QColor(glow_hex)
        self.update()

    def paintEvent(self, event):
        """High-performance vector paint event with squared boundary and dual raw/mod dots."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        width = self.width()
        height = self.height()
        size = min(width, height) - 20

        cx = width / 2.0
        cy = height / 2.0
        radius = size / 2.0

        # 1. Draw Squared Glass Container Outer Box
        box_rect = QRectF(cx - radius, cy - radius, size, size)
        painter.setPen(QPen(self.color_border, 1.5))
        painter.setBrush(QBrush(self.color_bg))
        painter.drawRoundedRect(box_rect, 12, 12)

        # 2. Draw Inner Circular Radar Ring & Crosshairs with White Circularity Bounds Circle (if enabled)
        if getattr(self, 'circularity_mode', 'disabled') != 'disabled' and getattr(self, 'show_circularity_bounds', True):
            painter.setPen(QPen(QColor(255, 255, 255, 220), 2, Qt.PenStyle.SolidLine))
            painter.drawEllipse(QPointF(cx, cy), radius, radius)
        else:
            painter.setPen(QPen(QColor(255, 255, 255, 40), 1, Qt.PenStyle.DashLine))
            painter.drawEllipse(QPointF(cx, cy), radius, radius)

        pen_grid = QPen(self.color_grid, 1, Qt.PenStyle.DashLine)
        painter.setPen(pen_grid)
        painter.drawLine(QPointF(cx - radius, cy), QPointF(cx + radius, cy))
        painter.drawLine(QPointF(cx, cy - radius), QPointF(cx, cy + radius))
        painter.drawEllipse(QPointF(cx, cy), radius * 0.5, radius * 0.5)

        # 3. Draw Dynamic Growing Inner Deadzone Circle Overlay
        dz_radius = radius * (self.deadzone_pct / 100.0)
        if dz_radius > 0:
            painter.setPen(QPen(QColor(168, 85, 247, 160), 1.5, Qt.PenStyle.DashLine))
            painter.setBrush(QBrush(self.color_deadzone))
            painter.drawEllipse(QPointF(cx, cy), dz_radius, dz_radius)

        # 4. Draw Raw Input Dot (Orange Outline)
        raw_dot_x = cx + (self.raw_x * radius)
        raw_dot_y = cy - (self.raw_y * radius)
        if (self.raw_x != 0.0 or self.raw_y != 0.0) and (self.raw_x != self.norm_x or self.raw_y != self.norm_y):
            painter.setPen(QPen(self.color_raw_dot, 1.5))
            painter.setBrush(QBrush(QColor(251, 146, 60, 60)))
            painter.drawEllipse(QPointF(raw_dot_x, raw_dot_y), 6, 6)

        # 5. Draw Vector Line from Center to Modified Output Dot
        mod_dot_x = cx + (self.norm_x * radius)
        mod_dot_y = cy - (self.norm_y * radius)

        pen_trail = QPen(self.color_trail, 2)
        painter.setPen(pen_trail)
        painter.drawLine(QPointF(cx, cy), QPointF(mod_dot_x, mod_dot_y))

        # 6. Draw Glowing Modified Output Dot (Green Core)
        radial_grad = QRadialGradient(QPointF(mod_dot_x, mod_dot_y), 10)
        radial_grad.setColorAt(0, self.color_mod_dot)
        radial_grad.setColorAt(0.6, self.color_mod_dot)
        radial_grad.setColorAt(1.0, QColor(0, 245, 160, 0))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(radial_grad))
        painter.drawEllipse(QPointF(mod_dot_x, mod_dot_y), 10, 10)

        # Inner Solid White Core
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(QPointF(mod_dot_x, mod_dot_y), 3.5, 3.5)

        painter.end()
