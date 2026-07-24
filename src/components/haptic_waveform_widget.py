"""
Haptic Waveform Widget for PySide6 (haptic_waveform_widget.py)
Interactive vibration waveform preview canvas for Shift Layer haptic feedback sequences.
Renders motor intensity pulses over time (LM Left Heavy, RM Right Soft, BOTH).
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath


class HapticWaveformWidget(QWidget):
    """
    QPainter visual waveform preview canvas for haptic vibration pattern timelines.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(280, 100)
        # Timeline blocks: [(motor, intensity_pct, duration_ms)]
        self.blocks = [
            ("LM", 80, 150),
            ("RM", 50, 100),
            ("BOTH", 100, 200)
        ]

    def set_blocks(self, blocks):
        """Update timeline blocks list and redraw waveform."""
        self.blocks = list(blocks)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        width = self.width()
        height = self.height()

        # Base Container Frame
        painter.setPen(QPen(QColor(168, 85, 247, 60), 1))
        painter.setBrush(QBrush(QColor(12, 9, 20, 240)))
        painter.drawRoundedRect(0, 0, width, height, 8, 8)

        if not self.blocks:
            painter.setPen(QColor(169, 146, 203, 120))
            painter.drawText(0, 0, width, height, Qt.AlignmentFlag.AlignCenter, "No Vibration Pattern Defined")
            painter.end()
            return

        total_duration = sum(b[2] for b in self.blocks) or 1
        margin = 12
        usable_w = width - (2 * margin)
        baseline = height - margin

        curr_x = margin
        for motor, pct, dur in self.blocks:
            w_block = (dur / float(total_duration)) * usable_w
            h_block = (pct / 100.0) * (height - (2 * margin))

            # Color by motor type
            if motor == "LM":
                color_fill = QColor(117, 0, 171, 140)
                color_stroke = QColor(168, 85, 247)
            elif motor == "RM":
                color_fill = QColor(2, 132, 199, 140)
                color_stroke = QColor(56, 189, 248)
            else:
                color_fill = QColor(0, 245, 160, 140)
                color_stroke = QColor(0, 245, 160)

            painter.setPen(QPen(color_stroke, 1.5))
            painter.setBrush(QBrush(color_fill))
            painter.drawRoundedRect(curr_x, baseline - h_block, w_block, h_block, 4, 4)

            curr_x += w_block

        painter.end()
