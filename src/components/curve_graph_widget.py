"""
Curve Graph Widget for PySide6 (curve_graph_widget.py)
Interactive QPainter response curve editor with draggable control points,
curve preset previews (Linear, Aggressive, Smooth, S-Curve, Custom),
LaTeX math formula export, and JSON control points export.
"""

import math
import json
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QPointF, Signal
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath


class CurveGraphWidget(QWidget):
    """
    Interactive QPainter response curve editor with draggable control points.
    """

    points_changed = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(280, 220)
        self.curve_preset = "Linear"
        # Control points normalized from (0.0, 0.0) to (1.0, 1.0)
        self.control_points = [
            QPointF(0.0, 0.0),
            QPointF(0.25, 0.25),
            QPointF(0.5, 0.5),
            QPointF(0.75, 0.75),
            QPointF(1.0, 1.0)
        ]
        self.active_point_idx = None
        self.color_line = QColor(168, 85, 247)
        self.color_dot = QColor(0, 245, 160)

    def set_preset(self, preset_name: str):
        """Update control points based on curve preset."""
        self.curve_preset = preset_name
        if preset_name == "Linear":
            self.control_points = [
                QPointF(0.0, 0.0), QPointF(0.25, 0.25), QPointF(0.5, 0.5), QPointF(0.75, 0.75), QPointF(1.0, 1.0)
            ]
        elif preset_name == "Aggressive":
            self.control_points = [
                QPointF(0.0, 0.0), QPointF(0.25, 0.45), QPointF(0.5, 0.75), QPointF(0.75, 0.90), QPointF(1.0, 1.0)
            ]
        elif preset_name == "Smooth":
            self.control_points = [
                QPointF(0.0, 0.0), QPointF(0.25, 0.10), QPointF(0.5, 0.35), QPointF(0.75, 0.70), QPointF(1.0, 1.0)
            ]
        elif preset_name == "S-Curve":
            self.control_points = [
                QPointF(0.0, 0.0), QPointF(0.25, 0.12), QPointF(0.5, 0.5), QPointF(0.75, 0.88), QPointF(1.0, 1.0)
            ]
        self.update()

    def get_points_data(self):
        return [(pt.x(), pt.y()) for pt in self.control_points]

    def export_latex(self) -> str:
        """Export curve representation as LaTeX formula string."""
        if self.curve_preset == "Linear":
            return r"f(x) = x"
        elif self.curve_preset == "Aggressive":
            return r"f(x) = x^{0.5}"
        elif self.curve_preset == "Smooth":
            return r"f(x) = x^2"
        elif self.curve_preset == "S-Curve":
            return r"f(x) = \frac{1}{1 + e^{-10(x - 0.5)}}"
        pts_str = ", ".join(f"({p.x():.2f}, {p.y():.2f})" for p in self.control_points)
        return rf"f(x) \text{{ (Custom Points: }} {pts_str} \text{{)}}"

    def export_json(self) -> str:
        """Export control points as JSON string."""
        return json.dumps(self.get_points_data(), indent=2)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        width = self.width()
        height = self.height()
        margin = 30
        w = width - (2 * margin)
        h = height - (2 * margin)

        # Draw Graph Container Card
        painter.setPen(QPen(QColor(168, 85, 247, 60), 1))
        painter.setBrush(QBrush(QColor(12, 9, 20, 240)))
        painter.drawRoundedRect(0, 0, width, height, 8, 8)

        # Draw Grid Lines & Diagonal Reference
        pen_grid = QPen(QColor(255, 255, 255, 25), 1, Qt.PenStyle.DashLine)
        painter.setPen(pen_grid)
        for i in range(1, 4):
            gx = margin + (w * (i / 4.0))
            gy = margin + (h * (i / 4.0))
            painter.drawLine(QPointF(gx, margin), QPointF(gx, height - margin))
            painter.drawLine(QPointF(margin, gy), QPointF(width - margin, gy))

        # Linear Reference Line
        painter.setPen(QPen(QColor(255, 255, 255, 40), 1, Qt.PenStyle.DotLine))
        painter.drawLine(QPointF(margin, height - margin), QPointF(width - margin, margin))

        # Draw Curve Path
        path = QPainterPath()
        start_x = margin + (self.control_points[0].x() * w)
        start_y = (height - margin) - (self.control_points[0].y() * h)
        path.moveTo(start_x, start_y)

        for pt in self.control_points[1:]:
            px = margin + (pt.x() * w)
            py = (height - margin) - (pt.y() * h)
            path.lineTo(px, py)

        painter.setPen(QPen(self.color_line, 2.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

        # Draw Interactive Control Points
        for idx, pt in enumerate(self.control_points):
            px = margin + (pt.x() * w)
            py = (height - margin) - (pt.y() * h)

            if idx == self.active_point_idx:
                painter.setPen(QPen(QColor(255, 255, 255), 2))
                painter.setBrush(QBrush(self.color_dot))
                painter.drawEllipse(QPointF(px, py), 7, 7)
            else:
                painter.setPen(QPen(self.color_line, 1.5))
                painter.setBrush(QBrush(QColor(12, 9, 20)))
                painter.drawEllipse(QPointF(px, py), 5, 5)

        painter.end()

    def mousePressEvent(self, event):
        margin = 30
        w = self.width() - (2 * margin)
        h = self.height() - (2 * margin)
        pos = event.position()

        for idx, pt in enumerate(self.control_points):
            px = margin + (pt.x() * w)
            py = (self.height() - margin) - (pt.y() * h)
            dist = math.hypot(pos.x() - px, pos.y() - py)
            if dist <= 12:
                self.active_point_idx = idx
                self.update()
                break

    def mouseMoveEvent(self, event):
        if self.active_point_idx is not None:
            margin = 30
            w = self.width() - (2 * margin)
            h = self.height() - (2 * margin)
            pos = event.position()

            norm_x = max(0.0, min(1.0, (pos.x() - margin) / w))
            norm_y = max(0.0, min(1.0, ((self.height() - margin) - pos.y()) / h))

            # Clamp endpoints (0,0) and (1,1)
            if self.active_point_idx == 0:
                norm_x = 0.0
            elif self.active_point_idx == len(self.control_points) - 1:
                norm_x = 1.0

            self.control_points[self.active_point_idx] = QPointF(norm_x, norm_y)
            self.curve_preset = "Custom"
            self.update()
            self.points_changed.emit(self.get_points_data())

    def mouseReleaseEvent(self, event):
        self.active_point_idx = None
        self.update()
