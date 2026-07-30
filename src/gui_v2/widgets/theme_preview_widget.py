"""
Live Interactive Theme Preview Panel for PySide6 UI (gui_v2).
Provides real-time visual feedback for active color tokens (accent_1, accent_2, background),
hosting a Mock Response Curve Graph, Mock Radar Canvas, Sample Remapping Widgets, and Sample Controls.
"""

import sys
import os
import math
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame,
    QLineEdit, QPushButton, QCheckBox, QSlider, QGroupBox
)
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPainterPath, QFont
)
from PySide6.QtCore import Qt, QPointF, Slot

# Import ThemeManager
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from gui_v2.services.theme_manager import ThemeManager, color_to_rgba_str


class MockResponseCurveCanvas(QWidget):
    """
    Custom painted canvas displaying a mock response curve.
    Axes and grid use background/muted borders, output line uses accent_2,
    and input dot is rendered at (0.5, 0.5) using accent_1.
    """
    def __init__(self, theme_mgr: Optional[ThemeManager] = None, parent=None):
        super().__init__(parent)
        self.theme_mgr = theme_mgr or ThemeManager.get_instance()
        self.setMinimumSize(220, 160)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        w, h = rect.width(), rect.height()

        bg_color = self.theme_mgr.get_color("background")
        accent_1 = self.theme_mgr.get_color("accent_1")
        accent_2 = self.theme_mgr.get_color("accent_2")

        # 1. Background Card
        painter.setBrush(QColor(bg_color.red(), bg_color.green(), bg_color.blue(), 215))
        painter.setPen(QPen(QColor(accent_1.red(), accent_1.green(), accent_1.blue(), 75), 1))
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 8, 8)

        # Title Overlay
        painter.setPen(QColor(255, 255, 255, 220))
        font = painter.font()
        font.setBold(True)
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(rect.adjusted(10, 8, -10, -8), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, "MOCK RESPONSE CURVE GRAPH")

        # 2. Graph Canvas Boundary inside rect
        margin_left = 35
        margin_right = 15
        margin_top = 30
        margin_bottom = 25

        gx = margin_left
        gy = margin_top
        gw = w - margin_left - margin_right
        gh = h - margin_top - margin_bottom

        # Background grid & axes
        grid_pen = QPen(QColor(accent_1.red(), accent_1.green(), accent_1.blue(), 45), 1, Qt.PenStyle.DashLine)
        painter.setPen(grid_pen)

        # Grid lines (2x2)
        painter.drawLine(int(gx + gw * 0.5), gy, int(gx + gw * 0.5), gy + gh)
        painter.drawLine(gx, int(gy + gh * 0.5), gx + gw, int(gy + gh * 0.5))

        # Main Axes
        axis_pen = QPen(QColor(255, 255, 255, 120), 1)
        painter.setPen(axis_pen)
        painter.drawLine(gx, gy + gh, gx + gw, gy + gh)  # X axis
        painter.drawLine(gx, gy, gx, gy + gh)            # Y axis

        # Axis Labels
        font_sm = painter.font()
        font_sm.setPointSize(7)
        font_sm.setBold(False)
        painter.setFont(font_sm)
        painter.setPen(QColor(255, 255, 255, 160))
        painter.drawText(gx - 25, gy + 10, "1.0")
        painter.drawText(gx - 25, gy + gh, "0.0")
        painter.drawText(gx, gy + gh + 15, "0.0")
        painter.drawText(gx + gw - 15, gy + gh + 15, "1.0")

        # 3. Curved Response Line (S-curve / Exponential curve using accent_2)
        path = QPainterPath()
        p0 = QPointF(gx, gy + gh)
        c1 = QPointF(gx + gw * 0.4, gy + gh * 0.9)
        c2 = QPointF(gx + gw * 0.6, gy + gh * 0.1)
        p1 = QPointF(gx + gw, gy)

        path.moveTo(p0)
        path.cubicTo(c1, c2, p1)

        curve_pen = QPen(accent_2, 2.5, Qt.PenStyle.SolidLine)
        painter.setPen(curve_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

        # 4. Input Dot in the middle of curve (X = 0.5, Y = 0.5) using accent_1
        dot_x = gx + gw * 0.5
        dot_y = gy + gh * 0.5

        # Glowing halo
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(accent_1.red(), accent_1.green(), accent_1.blue(), 75)))
        painter.drawEllipse(QPointF(dot_x, dot_y), 9.0, 9.0)

        # Core dot
        painter.setBrush(QBrush(accent_1))
        painter.drawEllipse(QPointF(dot_x, dot_y), 5.0, 5.0)

        # Dot label
        painter.setPen(accent_1)
        painter.drawText(int(dot_x + 8), int(dot_y - 4), "Input (0.5, 0.5)")


class MockStickRadarCanvas(QWidget):
    """
    Custom painted canvas displaying a mock stick radar.
    Crosshairs & circularity rings use background/muted borders.
    Input Point (accent_1) and Output Point (accent_2) are rendered in distinct non-overlapping locations.
    """
    def __init__(self, theme_mgr: Optional[ThemeManager] = None, parent=None):
        super().__init__(parent)
        self.theme_mgr = theme_mgr or ThemeManager.get_instance()
        self.setMinimumSize(220, 160)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        w, h = rect.width(), rect.height()

        bg_color = self.theme_mgr.get_color("background")
        accent_1 = self.theme_mgr.get_color("accent_1")
        accent_2 = self.theme_mgr.get_color("accent_2")

        # 1. Background Card
        painter.setBrush(QColor(bg_color.red(), bg_color.green(), bg_color.blue(), 215))
        painter.setPen(QPen(QColor(accent_1.red(), accent_1.green(), accent_1.blue(), 75), 1))
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 8, 8)

        # Title Overlay
        painter.setPen(QColor(255, 255, 255, 220))
        font = painter.font()
        font.setBold(True)
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(rect.adjusted(10, 8, -10, -8), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, "MOCK RADAR CANVAS (Input vs Output)")

        # Center and Radius
        cx = w / 2.0
        cy = h / 2.0 + 8.0
        radius = min(w, h) / 2.8

        # 2. Axis Crosshairs
        grid_pen = QPen(QColor(accent_1.red(), accent_1.green(), accent_1.blue(), 50), 1, Qt.PenStyle.DashLine)
        painter.setPen(grid_pen)
        painter.drawLine(int(cx - radius * 1.2), int(cy), int(cx + radius * 1.2), int(cy))
        painter.drawLine(int(cx), int(cy - radius * 1.2), int(cx), int(cy + radius * 1.2))

        # 3. Outer Circularity Ring (Unit Boundary)
        ring_pen = QPen(QColor(255, 255, 255, 90), 1.2, Qt.PenStyle.SolidLine)
        painter.setPen(ring_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        # Inner deadzone ring
        dz_pen = QPen(QColor(239, 68, 68, 120), 1, Qt.PenStyle.DashLine)
        painter.setPen(dz_pen)
        painter.drawEllipse(QPointF(cx, cy), radius * 0.25, radius * 0.25)

        # 4. DISTINCT NON-OVERLAPPING POINT LOCATIONS
        # Input Vector: Top-Left quadrant (-0.45, 0.55) -> accent_1
        in_x = cx + (-0.45) * radius
        in_y = cy - (0.55) * radius

        # Output Vector: Bottom-Right quadrant (0.65, -0.35) -> accent_2
        out_x = cx + (0.65) * radius
        out_y = cy - (-0.35) * radius

        # Draw Dotted trailing vector lines
        line_pen_in = QPen(QColor(accent_1.red(), accent_1.green(), accent_1.blue(), 180), 1.5, Qt.PenStyle.DotLine)
        painter.setPen(line_pen_in)
        painter.drawLine(QPointF(cx, cy), QPointF(in_x, in_y))

        line_pen_out = QPen(QColor(accent_2.red(), accent_2.green(), accent_2.blue(), 180), 1.5, Qt.PenStyle.DotLine)
        painter.setPen(line_pen_out)
        painter.drawLine(QPointF(cx, cy), QPointF(out_x, out_y))

        # Render Input Point ● (accent_1)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(accent_1.red(), accent_1.green(), accent_1.blue(), 90)))
        painter.drawEllipse(QPointF(in_x, in_y), 9.0, 9.0)
        painter.setBrush(QBrush(accent_1))
        painter.drawEllipse(QPointF(in_x, in_y), 5.5, 5.5)

        # Input Text Label
        font_sm = painter.font()
        font_sm.setPointSize(7)
        font_sm.setBold(True)
        painter.setFont(font_sm)
        painter.setPen(accent_1)
        painter.drawText(int(in_x - 45), int(in_y - 8), "● Input Vector")

        # Render Output Point ★ / * (accent_2)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(accent_2.red(), accent_2.green(), accent_2.blue(), 90)))
        painter.drawEllipse(QPointF(out_x, out_y), 9.0, 9.0)
        painter.setBrush(QBrush(accent_2))
        painter.drawEllipse(QPointF(out_x, out_y), 5.5, 5.5)

        # Output Text Label
        painter.setPen(accent_2)
        painter.drawText(int(out_x + 8), int(out_y + 12), "* Output Vector")


class ThemePreviewWidget(QWidget):
    """
    Interactive Live Theme Preview Container hosting response curve, radar canvas,
    sample remapping controls, and working interactive widgets.
    """
    def __init__(self, theme_manager: Optional[ThemeManager] = None, parent=None):
        super().__init__(parent)
        self.theme_mgr = theme_manager or ThemeManager.get_instance()
        self.theme_mgr.theme_changed.connect(self.on_theme_changed)

        self.setup_ui()
        self.update_styles()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)

        # Main Group Box / Frame
        self.container_frame = QFrame()
        self.container_frame.setObjectName("preview_frame")
        frame_layout = QVBoxLayout(self.container_frame)
        frame_layout.setContentsMargins(14, 12, 14, 12)
        frame_layout.setSpacing(12)

        header_title = QLabel("LIVE INTERACTIVE THEME PREVIEW PANEL")
        header_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #ffffff;")
        frame_layout.addWidget(header_title)

        # 2x2 Grid Layout for Canvases & Sample Controls
        grid = QGridLayout()
        grid.setSpacing(12)

        # 1. Mock Response Curve Canvas
        self.curve_canvas = MockResponseCurveCanvas(self.theme_mgr)
        grid.addWidget(self.curve_canvas, 0, 0)

        # 2. Mock Radar Canvas
        self.radar_canvas = MockStickRadarCanvas(self.theme_mgr)
        grid.addWidget(self.radar_canvas, 0, 1)

        # 3. Sample Remapping Widgets Panel
        self.remap_panel = QFrame()
        self.remap_panel.setObjectName("sample_card")
        remap_layout = QVBoxLayout(self.remap_panel)
        remap_layout.setContentsMargins(10, 10, 10, 10)
        remap_layout.setSpacing(8)

        remap_title = QLabel("SAMPLE REMAPPING WIDGETS")
        remap_title.setStyleSheet("font-weight: bold; font-size: 10px; color: rgba(255, 255, 255, 0.8);")
        remap_layout.addWidget(remap_title)

        # Row 1
        r1_layout = QHBoxLayout()
        r1_btn = QPushButton("Button A")
        r1_btn.setFixedWidth(80)
        r1_arrow = QLabel("➔")
        r1_input = QLineEdit("Space")
        r1_input.setReadOnly(True)
        r1_chk = QCheckBox("Block XInput")
        r1_chk.setChecked(True)
        r1_layout.addWidget(r1_btn)
        r1_layout.addWidget(r1_arrow)
        r1_layout.addWidget(r1_input)
        r1_layout.addWidget(r1_chk)
        remap_layout.addLayout(r1_layout)

        # Row 2
        r2_layout = QHBoxLayout()
        r2_btn = QPushButton("Button B")
        r2_btn.setFixedWidth(80)
        r2_arrow = QLabel("➔")
        r2_input = QLineEdit("Shift+C")
        r2_input.setReadOnly(True)
        r2_chk = QCheckBox("Block XInput")
        r2_chk.setChecked(False)
        r2_layout.addWidget(r2_btn)
        r2_layout.addWidget(r2_arrow)
        r2_layout.addWidget(r2_input)
        r2_layout.addWidget(r2_chk)
        remap_layout.addLayout(r2_layout)

        grid.addWidget(self.remap_panel, 1, 0)

        # 4. Sample Controls Panel
        self.controls_panel = QFrame()
        self.controls_panel.setObjectName("sample_card")
        ctrl_layout = QVBoxLayout(self.controls_panel)
        ctrl_layout.setContentsMargins(10, 10, 10, 10)
        ctrl_layout.setSpacing(8)

        ctrl_title = QLabel("SAMPLE CONTROLS")
        ctrl_title.setStyleSheet("font-weight: bold; font-size: 10px; color: rgba(255, 255, 255, 0.8);")
        ctrl_layout.addWidget(ctrl_title)

        # Slider Row
        slider_layout = QHBoxLayout()
        slider_label = QLabel("Working Slider:")
        slider_label.setFixedWidth(95)
        self.sample_slider = QSlider(Qt.Orientation.Horizontal)
        self.sample_slider.setRange(0, 100)
        self.sample_slider.setValue(45)
        self.slider_val_label = QLabel("45%")
        self.slider_val_label.setFixedWidth(40)
        self.sample_slider.valueChanged.connect(lambda v: self.slider_val_label.setText(f"{v}%"))

        slider_layout.addWidget(slider_label)
        slider_layout.addWidget(self.sample_slider)
        slider_layout.addWidget(self.slider_val_label)
        ctrl_layout.addLayout(slider_layout)

        # Simple Button Row
        btn_layout = QHBoxLayout()
        btn_label = QLabel("Simple Button:")
        btn_label.setFixedWidth(95)
        self.sample_action_btn = QPushButton("Click Action Button")
        self.sample_action_btn.setObjectName("action_btn")
        self.sample_action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_layout.addWidget(btn_label)
        btn_layout.addWidget(self.sample_action_btn)
        ctrl_layout.addLayout(btn_layout)

        # Outlined Text Box Row
        txt_layout = QHBoxLayout()
        txt_label = QLabel("Outlined Text:")
        txt_label.setFixedWidth(95)
        self.sample_line_edit = QLineEdit()
        self.sample_line_edit.setPlaceholderText("Sample Typed Input Text...")
        txt_layout.addWidget(txt_label)
        txt_layout.addWidget(self.sample_line_edit)
        ctrl_layout.addLayout(txt_layout)

        grid.addWidget(self.controls_panel, 1, 1)

        frame_layout.addLayout(grid)
        main_layout.addWidget(self.container_frame)

    @Slot(dict)
    def on_theme_changed(self, tokens: dict):
        """Refreshes sub-canvas painting and updates dynamic widget styles."""
        self.update_styles()
        self.curve_canvas.update()
        self.radar_canvas.update()
        self.update()

    def update_styles(self):
        """Applies dynamic QSS tokens to sample preview cards and controls."""
        bg_color = self.theme_mgr.get_color("background")
        accent_1 = self.theme_mgr.get_color("accent_1")
        accent_2 = self.theme_mgr.get_color("accent_2")

        bg_glass = color_to_rgba_str(bg_color, alpha_override=0.85)
        border_glass = color_to_rgba_str(accent_1, alpha_override=0.35)
        accent_1_rgba = color_to_rgba_str(accent_1, alpha_override=1.0)
        accent_1_subtle = color_to_rgba_str(accent_1, alpha_override=0.20)
        accent_2_rgba = color_to_rgba_str(accent_2, alpha_override=1.0)

        style = f"""
        QFrame#preview_frame {{
            background-color: {bg_glass};
            border: 1.5px solid {border_glass};
            border-radius: 12px;
        }}

        QFrame#sample_card {{
            background-color: rgba({bg_color.red()}, {bg_color.green()}, {bg_color.blue()}, 0.65);
            border: 1px solid {border_glass};
            border-radius: 8px;
        }}

        QLineEdit {{
            background-color: rgba({bg_color.red()}, {bg_color.green()}, {bg_color.blue()}, 0.85);
            border: 1.5px solid {accent_1_rgba};
            color: #ffffff;
            border-radius: 6px;
            padding: 4px 8px;
        }}

        QLineEdit:focus {{
            border: 2px solid {accent_2_rgba};
        }}

        QPushButton {{
            background-color: {accent_1_subtle};
            border: 1px solid {border_glass};
            color: #ffffff;
            border-radius: 6px;
            padding: 5px 10px;
        }}

        QPushButton:hover {{
            background-color: rgba({accent_1.red()}, {accent_1.green()}, {accent_1.blue()}, 0.40);
            border: 1px solid {accent_1_rgba};
        }}

        QPushButton:pressed {{
            background-color: rgba({accent_1.red()}, {accent_1.green()}, {accent_1.blue()}, 0.60);
        }}

        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border-radius: 4px;
            border: 1.5px solid {border_glass};
            background-color: rgba({bg_color.red()}, {bg_color.green()}, {bg_color.blue()}, 0.9);
        }}

        QCheckBox::indicator:checked {{
            background-color: {accent_1_rgba};
            border: 1.5px solid {accent_1_rgba};
        }}

        QSlider::groove:horizontal {{
            height: 6px;
            background: rgba({bg_color.red()}, {bg_color.green()}, {bg_color.blue()}, 0.9);
            border: 1px solid {border_glass};
            border-radius: 3px;
        }}

        QSlider::sub-page:horizontal {{
            background: {accent_2_rgba};
            border-radius: 3px;
        }}

        QSlider::handle:horizontal {{
            background: {accent_2_rgba};
            border: 2px solid #ffffff;
            width: 16px;
            height: 16px;
            margin: -5px 0;
            border-radius: 8px;
        }}

        QSlider::handle:horizontal:hover {{
            background: #ffffff;
            border: 2px solid {accent_2_rgba};
        }}
        """
        self.setStyleSheet(style)
