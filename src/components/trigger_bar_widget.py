"""
Trigger Pull Visualizer Widget for PySide6 (trigger_bar_widget.py)
Renders side-by-side vertical progress bars for raw trigger input and modified tuned output.
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QFont


class TriggerPullWidget(QWidget):
    """
    Vertical side-by-side dual trigger progress bar widget.
    Renders raw trigger input (Green) and tuned output (Purple/Primary).
    """

    def __init__(self, title="Trigger Pull", parent=None):
        super().__init__(parent)
        self.title = title
        self.raw_val = 0.0
        self.mod_val = 0.0
        self.setMinimumSize(90, 180)
        self.setMaximumWidth(120)

        # Colors
        self.color_bg = QColor(12, 9, 20, 230)
        self.color_border = QColor(168, 85, 247, 80)
        self.color_raw = QColor(74, 222, 128)   # Green for raw input
        self.color_mod = QColor(168, 85, 247)   # Purple for tuned output

    def set_theme_colors(self, primary_hex="#7500ab", glow_hex="#a855f7", accent_green_hex="#00f5a0"):
        """Dynamically update theme colors from ThemeManager."""
        self.color_border = QColor(glow_hex)
        self.color_border.setAlpha(80)
        self.color_mod = QColor(glow_hex)
        self.color_raw = QColor(accent_green_hex)
        self.update()

    def set_values(self, raw_val: float, mod_val: float):
        """Set normalized trigger values (0.0 to 1.0) and update canvas."""
        self.raw_val = max(0.0, min(1.0, float(raw_val)))
        self.mod_val = max(0.0, min(1.0, float(mod_val)))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        w = self.width()
        h = self.height()

        margin = 10
        bar_w = (w - (3 * margin)) / 2.0
        max_bar_h = h - (2 * margin) - 20

        # Outer Background Box
        bg_rect = QRectF(margin / 2.0, margin / 2.0, w - margin, h - margin)
        painter.setPen(QPen(self.color_border, 1.5))
        painter.setBrush(QBrush(self.color_bg))
        painter.drawRoundedRect(bg_rect, 8, 8)

        top_y = margin + 10
        bottom_y = top_y + max_bar_h

        # 1. Raw Bar Container & Fill (Left Bar)
        raw_x = margin + 4
        raw_bg_rect = QRectF(raw_x, top_y, bar_w, max_bar_h)
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        painter.setBrush(QBrush(QColor(255, 255, 255, 10)))
        painter.drawRoundedRect(raw_bg_rect, 4, 4)

        if self.raw_val > 0:
            fill_h = max_bar_h * self.raw_val
            raw_fill_rect = QRectF(raw_x, bottom_y - fill_h, bar_w, fill_h)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(self.color_raw))
            painter.drawRoundedRect(raw_fill_rect, 4, 4)

        # 2. Mod Bar Container & Fill (Right Bar)
        mod_x = raw_x + bar_w + 6
        mod_bg_rect = QRectF(mod_x, top_y, bar_w, max_bar_h)
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        painter.setBrush(QBrush(QColor(255, 255, 255, 10)))
        painter.drawRoundedRect(mod_bg_rect, 4, 4)

        if self.mod_val > 0:
            fill_h = max_bar_h * self.mod_val
            mod_fill_rect = QRectF(mod_x, bottom_y - fill_h, bar_w, fill_h)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(self.color_mod))
            painter.drawRoundedRect(mod_fill_rect, 4, 4)

        # Labels
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        painter.setPen(QPen(QColor(200, 200, 200)))
        painter.drawText(QRectF(raw_x, bottom_y + 2, bar_w, 15), Qt.AlignmentFlag.AlignCenter, f"{int(self.raw_val * 100)}%")
        painter.drawText(QRectF(mod_x, bottom_y + 2, bar_w, 15), Qt.AlignmentFlag.AlignCenter, f"{int(self.mod_val * 100)}%")

        painter.end()
