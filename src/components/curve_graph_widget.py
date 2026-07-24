"""
Curve Graph Widget for PySide6 (curve_graph_widget.py)
Interactive QPainter response curve editor with draggable control points,
monotonic point clamping, right-click point addition/deletion,
real-time input/output tracer dot rendering, support for all curve types
(Linear, Relaxed, Aggressive, Cubic, Sigmoid, Bezier, Dotted, Custom),
LaTeX Desmos math formula export, and JSON control points export.
"""

import math
import json
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QPointF, Signal
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath
import curves


class CurveGraphWidget(QWidget):
    """
    Interactive QPainter response curve editor with monotonic clamping,
    right-click point edit callbacks, live tracer dots, and Desmos export.
    """

    points_changed = Signal(list)

    def __init__(self, title="Response Curve", parent=None):
        super().__init__(parent)
        self.title = title
        self.setMinimumSize(280, 220)
        self.curve_preset = "linear"
        self.power = 2.0
        self.custom_eq = ""
        self.raw_val = 0.0
        self.mod_val = 0.0

        # Control points for interactive/dotted curve normalized [0.0, 1.0]
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

    def set_live_input_output(self, raw_val: float, mod_val: float):
        """Update live input/output values from controller state to render active tracer dot."""
        self.raw_val = max(0.0, min(1.0, abs(raw_val)))
        self.mod_val = max(0.0, min(1.0, abs(mod_val)))
        self.update()

    def set_curve_params(self, curve_type: str, power: float = 2.0, custom_eq: str = ""):
        """Set curve type, sensitivity factor, and custom math equation."""
        self.curve_preset = curve_type.lower()
        self.power = power
        self.custom_eq = custom_eq

        if self.curve_preset == "linear":
            self.control_points = [QPointF(0.0, 0.0), QPointF(0.25, 0.25), QPointF(0.5, 0.5), QPointF(0.75, 0.75), QPointF(1.0, 1.0)]
        elif self.curve_preset in ["relaxed", "exponential"]:
            self.control_points = [QPointF(x / 4.0, (x / 4.0) ** power) for x in range(5)]
        elif self.curve_preset == "aggressive":
            self.control_points = [QPointF(x / 4.0, 1.0 - (1.0 - (x / 4.0)) ** power) for x in range(5)]
        elif self.curve_preset == "cubic":
            self.control_points = [QPointF(x / 4.0, (x / 4.0) ** 3) for x in range(5)]
        self.update()

    def export_latex(self) -> str:
        """Generate LaTeX Desmos formula list with full piecewise string formatting."""
        formulas = curves.export_to_desmos(self.curve_preset, self.power, 0.05, 0.0, 0.0)
        if formulas:
            return "\n".join(formulas)

        if self.curve_preset in ["dotted", "custom"]:
            pts = [(round(pt.x(), 3), round(pt.y(), 3)) for pt in self.control_points]
            lines = []
            for i in range(len(pts) - 1):
                p1, p2 = pts[i], pts[i + 1]
                dx = p2[0] - p1[0]
                if dx != 0:
                    m = (p2[1] - p1[1]) / dx
                    lines.append(f"{p1[1]:.3f}+{m:.3f}*(x-{p1[0]:.3f}) \\{{{p1[0]:.3f}\\le x\\le {p2[0]:.3f}\\}}")
            return "\n".join(lines) if lines else "f(x) = x"

        return f"f(x) = {self.curve_preset}(x)"

    def export_json(self) -> str:
        """Export control points as JSON string."""
        pts = [(pt.x(), pt.y()) for pt in self.control_points]
        return json.dumps(pts, indent=2)

    def set_theme_colors(self, primary_hex="#7500ab", glow_hex="#a855f7", accent_green_hex="#00f5a0"):
        """Dynamically update theme colors from ThemeManager."""
        self.color_line = QColor(glow_hex)
        self.color_dot = QColor(accent_green_hex)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        width = self.width()
        height = self.height()
        margin = 30
        w = width - (2 * margin)
        h = height - (2 * margin)

        # Draw Graph Card Background
        painter.setPen(QPen(QColor(self.color_line.red(), self.color_line.green(), self.color_line.blue(), 60), 1))
        painter.setBrush(QBrush(QColor(12, 9, 20, 240)))
        painter.drawRoundedRect(0, 0, width, height, 8, 8)

        # Title Header
        painter.setPen(self.color_line)
        painter.drawText(margin, 20, self.title.upper())

        # Grid Lines & Diagonal Reference
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

        # Evaluate and Draw Full Curve Path (100 steps)
        path = QPainterPath()
        start_y = curves.evaluate_curve(0.0, self.curve_preset, self.power, self.custom_eq)
        path.moveTo(margin, (height - margin) - (start_y * h))

        for step in range(1, 101):
            x_norm = step / 100.0
            y_norm = curves.evaluate_curve(x_norm, self.curve_preset, self.power, self.custom_eq)
            px = margin + (x_norm * w)
            py = (height - margin) - (y_norm * h)
            path.lineTo(px, py)

        painter.setPen(QPen(self.color_line, 2.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

        # Draw Draggable Control Points (if Dotted / Custom)
        if self.curve_preset in ["dotted", "dotted custom", "custom"]:
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

        # Draw Live Input / Output Tracer Dot
        tracer_x = margin + (self.raw_val * w)
        tracer_y = (height - margin) - (self.mod_val * h)
        painter.setPen(QPen(QColor(255, 255, 255), 1.5))
        painter.setBrush(QBrush(self.color_dot))
        painter.drawEllipse(QPointF(tracer_x, tracer_y), 6, 6)

        painter.end()

    def mousePressEvent(self, event):
        if self.curve_preset not in ["dotted", "dotted custom", "custom"]:
            return
            return
        margin = 30
        w = self.width() - (2 * margin)
        h = self.height() - (2 * margin)
        pos = event.position()

        # Handle Right Click to Insert or Delete Control Point
        if event.button() == Qt.MouseButton.RightButton:
            norm_x = max(0.0, min(1.0, (pos.x() - margin) / w))
            norm_y = max(0.0, min(1.0, ((self.height() - margin) - pos.y()) / h))

            # Check if clicked close to an existing point to delete
            for idx, pt in enumerate(self.control_points):
                px = margin + (pt.x() * w)
                py = (self.height() - margin) - (pt.y() * h)
                if math.hypot(pos.x() - px, pos.y() - py) <= 12 and 0 < idx < len(self.control_points) - 1:
                    self.control_points.pop(idx)
                    pts_list = [(p.x(), p.y()) for p in self.control_points]
                    self.custom_eq = json.dumps(pts_list)
                    self.update()
                    self.points_changed.emit(pts_list)
                    return

            # Otherwise insert a new point in monotonic order
            new_pt = QPointF(norm_x, norm_y)
            self.control_points.append(new_pt)
            self.control_points.sort(key=lambda p: p.x())
            pts_list = [(p.x(), p.y()) for p in self.control_points]
            self.custom_eq = json.dumps(pts_list)
            self.update()
            self.points_changed.emit(pts_list)
            return

        # Left Click to select point for dragging
        for idx, pt in enumerate(self.control_points):
            px = margin + (pt.x() * w)
            py = (self.height() - margin) - (pt.y() * h)
            dist = math.hypot(pos.x() - px, pos.y() - py)
            if dist <= 12:
                self.active_point_idx = idx
                self.update()
                break

    def mouseMoveEvent(self, event):
        if self.active_point_idx is not None and self.curve_preset in ["dotted", "custom"]:
            margin = 30
            w = self.width() - (2 * margin)
            h = self.height() - (2 * margin)
            pos = event.position()

            norm_x = max(0.0, min(1.0, (pos.x() - margin) / w))
            norm_y = max(0.0, min(1.0, ((self.height() - margin) - pos.y()) / h))

            # Monotonic Clamping: Ensure point X_i stays strictly between X_{i-1} and X_{i+1}
            idx = self.active_point_idx
            if idx == 0:
                norm_x = 0.0
            elif idx == len(self.control_points) - 1:
                norm_x = 1.0
            else:
                prev_x = self.control_points[idx - 1].x()
                next_x = self.control_points[idx + 1].x()
                norm_x = max(prev_x + 0.01, min(next_x - 0.01, norm_x))

            self.control_points[self.active_point_idx] = QPointF(norm_x, norm_y)
            pts_list = [(pt.x(), pt.y()) for pt in self.control_points]
            self.custom_eq = json.dumps(pts_list)
            self.update()
            self.points_changed.emit(pts_list)

    def mouseReleaseEvent(self, event):
        self.active_point_idx = None
        self.update()
