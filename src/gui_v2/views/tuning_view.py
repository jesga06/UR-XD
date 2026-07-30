"""
Analog Tuning View Module for PySide6 UI (gui_v2).

Features:
  - Dual side-by-side canvases per Stick & Trigger Card.
  - RESET button under every curve widget resetting all deadzones/warp/custom/digital to 0.0/off/disabled,
    setting curve factor & sensitivity to 1.0, and resetting preset to 'linear'.
  - Full curve options & sliders for Triggers (Deadzone, Anti-Deadzone, Rest Deadzone, Curve Factor, Sensitivity,
    Presets, Dotted Dot Selector, Custom Math QLineEdit, and Digital Mode Checkbox).
  - Clean dot styling: removed white border outlines, increased dot radius by ~20%.
  - Interactive mouse drag-and-drop dotted curve control point editing.
  - 300ms debounced config persistence.
"""

import sys
import os
import math
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QLineEdit, QCheckBox, QComboBox, QGroupBox,
    QSlider, QScrollArea, QFrame, QDialog, QTextEdit,
    QApplication, QMessageBox
)
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath, QPolygonF
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QPointF

# Add root src directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import math_utils
import curves
from gui_v2.dialogs.circularity_modal import CircularityCalibrationModal

logger = logging.getLogger('tuning_view')


_LABEL_STYLE = "color: rgba(255, 255, 255, 0.7); font-size: 11px; font-weight: bold;"


# ---------------------------------------------------------------------------
# ColorGuideModal
# ---------------------------------------------------------------------------
class ColorGuideModal(QDialog):
    """
    QDialog explaining Raw hardware input vs Processed output color legend across visualizers.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Color Guide — Signal Telemetry Legend")
        self.setMinimumSize(440, 260)

        try:
            from gui_v2.services.theme_manager import ThemeManager, color_to_rgba_str, color_to_hex6
            tm = ThemeManager.get_instance()
            window_bg = tm.get_color("window_bg")
            accent_1 = tm.get_color("accent_1")
            accent_2 = tm.get_color("accent_2")
            bg_hex = color_to_rgba_str(window_bg, alpha_override=1.0)
            acc1_hex = color_to_hex6(accent_1)
            acc2_hex = color_to_hex6(accent_2)
            acc1_subtle = color_to_rgba_str(accent_1, alpha_override=0.20)
            acc1_border = color_to_rgba_str(accent_1, alpha_override=0.50)
        except Exception:
            bg_hex = "#000000FF"
            acc1_hex = "#A855F7"
            acc2_hex = "#00F5A0"
            acc1_subtle = "rgba(168, 85, 247, 0.20)"
            acc1_border = "rgba(168, 85, 247, 0.50)"

        self.setStyleSheet(f"QDialog {{ background-color: {bg_hex}; color: #ffffff; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel("🎨 COLOR GUIDE & SIGNAL TELEMETRY")
        header.setStyleSheet(f"color: {acc1_hex}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        guide_text = (
            f"<b style='color: {acc1_hex};'>🔵 Accent #1 (Primary / Input Color):</b><br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;Raw controller hardware input vector and curve control point indicators.<br><br>"
            f"<b style='color: {acc2_hex};'>🟢 Accent #2 (Secondary / Output Color):</b><br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;Processed virtual output received by the game (after deadzones, response curves, sensitivity, and circularity scaling).<br><br>"
            "<i>The response curve graph displays calculated output magnitude relative to physical movement.</i>"
        )

        label = QLabel(guide_text)
        label.setWordWrap(True)
        label.setTextFormat(Qt.RichText)
        label.setStyleSheet("color: #ffffff; font-size: 11px; line-height: 1.4;")
        layout.addWidget(label)

        btn_close = QPushButton("Close")
        btn_close.setFocusPolicy(Qt.NoFocus)
        btn_close.setStyleSheet(f"QPushButton {{ background-color: {acc1_subtle}; border: 1px solid {acc1_border}; border-radius: 6px; color: #ffffff; padding: 4px 10px; font-size: 11px; font-weight: bold; }}")
        btn_close.clicked.connect(self.accept)

        layout.addStretch()
        layout.addWidget(btn_close, 0, Qt.AlignRight)


# ---------------------------------------------------------------------------
# LatexExportModal
# ---------------------------------------------------------------------------
class LatexExportModal(QDialog):
    """
    QDialog displaying LaTeX formulas for Desmos & copyable JSON profile snippets.
    """
    def __init__(self, curve_type: str, power: float, inner_dz: float, anti_dz: float, rest_dz: float, custom_eq: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Curve Math & Configuration")
        self.setMinimumSize(480, 420)

        try:
            from gui_v2.services.theme_manager import ThemeManager, color_to_rgba_str, color_to_hex6
            tm = ThemeManager.get_instance()
            bg_color = tm.get_color("background")
            window_bg = tm.get_color("window_bg")
            accent_1 = tm.get_color("accent_1")
            accent_2 = tm.get_color("accent_2")
            win_bg_hex = color_to_rgba_str(window_bg, alpha_override=1.0)
            bg_inner = color_to_rgba_str(bg_color, alpha_override=0.60)
            border_glass = color_to_rgba_str(accent_1, alpha_override=0.35)
            acc1_hex = color_to_hex6(accent_1)
            acc2_hex = color_to_hex6(accent_2)
            acc1_subtle = color_to_rgba_str(accent_1, alpha_override=0.20)
            acc1_border = color_to_rgba_str(accent_1, alpha_override=0.50)
            acc2_subtle = color_to_rgba_str(accent_2, alpha_override=0.20)
            acc2_border = color_to_rgba_str(accent_2, alpha_override=0.50)
        except Exception:
            win_bg_hex = "#000000FF"
            bg_inner = "rgba(22, 16, 36, 0.60)"
            border_glass = "rgba(168, 85, 247, 0.35)"
            acc1_hex = "#A855F7FF"
            acc2_hex = "#00F5A0FF"
            acc1_subtle = "rgba(168, 85, 247, 0.20)"
            acc1_border = "rgba(168, 85, 247, 0.50)"
            acc2_subtle = "rgba(0, 245, 160, 0.20)"
            acc2_border = "rgba(0, 245, 160, 0.50)"

        self.setStyleSheet(f"QDialog {{ background-color: {win_bg_hex}; color: #ffffff; }}")

        txt_style = f"QTextEdit {{ background-color: {bg_inner}; border: 1.5px solid {border_glass}; border-radius: 6px; color: {acc2_hex}; font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 11px; padding: 6px; }}"
        btn_acc_style = f"QPushButton {{ background-color: {acc2_subtle}; border: 1px solid {acc2_border}; border-radius: 6px; color: #ffffff; padding: 4px 10px; font-size: 11px; font-weight: bold; }} QPushButton:hover {{ background-color: {acc2_border}; }}"
        btn_close_style = f"QPushButton {{ background-color: {acc1_subtle}; border: 1px solid {acc1_border}; border-radius: 6px; color: #ffffff; padding: 4px 10px; font-size: 11px; font-weight: bold; }}"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        # 1. LaTeX Section
        h1 = QLabel("📄 LATEX FORMULA (DESMOS)")
        h1.setStyleSheet(f"color: {acc1_hex}; font-weight: bold; font-size: 11px;")
        layout.addWidget(h1)

        latex_str = curves.export_to_latex(curve_type, power, inner_dz, anti_dz, rest_dz)
        self.txt_latex = QTextEdit()
        self.txt_latex.setReadOnly(True)
        self.txt_latex.setText(latex_str)
        self.txt_latex.setStyleSheet(txt_style)
        self.txt_latex.setMaximumHeight(90)
        layout.addWidget(self.txt_latex)

        btn_copy_latex = QPushButton("Copy LaTeX")
        btn_copy_latex.setFocusPolicy(Qt.NoFocus)
        btn_copy_latex.setStyleSheet(btn_acc_style)
        btn_copy_latex.clicked.connect(lambda: self._copy(latex_str, "LaTeX formula copied to clipboard!"))
        layout.addWidget(btn_copy_latex, 0, Qt.AlignLeft)

        # 2. JSON Snippet Section
        h2 = QLabel("⚙️ JSON PROFILE SNIPPET")
        h2.setStyleSheet(f"color: {acc1_hex}; font-weight: bold; font-size: 11px;")
        layout.addWidget(h2)

        json_obj = {
            "curve_type": curve_type,
            "power": power,
            "deadzone": inner_dz,
            "anti_deadzone": anti_dz,
            "rest_deadzone": rest_dz,
            "custom_equation": custom_eq if curve_type.lower() in ("custom", "dotted") else ""
        }
        json_str = json.dumps(json_obj, indent=4)
        self.txt_json = QTextEdit()
        self.txt_json.setReadOnly(True)
        self.txt_json.setText(json_str)
        self.txt_json.setStyleSheet(txt_style)
        self.txt_json.setMaximumHeight(110)
        layout.addWidget(self.txt_json)

        btn_copy_json = QPushButton("Copy JSON")
        btn_copy_json.setFocusPolicy(Qt.NoFocus)
        btn_copy_json.setStyleSheet(btn_acc_style)
        btn_copy_json.clicked.connect(lambda: self._copy(json_str, "JSON profile snippet copied to clipboard!"))
        layout.addWidget(btn_copy_json, 0, Qt.AlignLeft)

        btn_close = QPushButton("Close")
        btn_close.setFocusPolicy(Qt.NoFocus)
        btn_close.setStyleSheet(btn_close_style)
        btn_close.clicked.connect(self.accept)

        layout.addStretch()
        layout.addWidget(btn_close, 0, Qt.AlignRight)

    def _copy(self, text: str, msg: str) -> None:
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copied", msg)


# ---------------------------------------------------------------------------
# StickCurveCanvas (1D Curve Plot with Interactive Dotted Point Dragging)
# ---------------------------------------------------------------------------
class StickCurveCanvas(QWidget):
    """
    180x180 1D Response Curve canvas:
      - Plots input magnitude vs output magnitude curve
      - Renders live magnitude cursor dot
      - Renders interactive control-point dots when curve_type == 'dotted'
      - Supports mouse press, drag, and release to move control points interactively!
    """
    dot_changed = Signal(str)  # Emits new custom_eq JSON string on mouse drag

    def __init__(self, is_trigger: bool = False, parent=None):
        super().__init__(parent)
        self.setFixedSize(180, 180)
        self.is_trigger: bool = is_trigger

        self.dz: float = 0.00
        self.adz: float = 0.00
        self.rest_dz: float = 0.00
        self.curve_type: str = "linear"
        self.power: float = 1.0
        self.sens: float = 1.0
        self.custom_eq: str = ""
        self.is_digital: bool = False

        self.live_raw_mag: float = 0.0
        self.live_out_mag: float = 0.0

        self.active_dot_idx: Optional[int] = None
        self.setMouseTracking(True)

    def update_params(
        self, dz: float, adz: float, rest_dz: float,
        curve_type: str, power: float, sens: float, custom_eq: str,
        is_digital: bool = False
    ) -> None:
        self.dz = dz
        self.adz = adz
        self.rest_dz = rest_dz
        self.curve_type = curve_type
        self.power = power
        self.sens = sens
        self.custom_eq = custom_eq
        self.is_digital = is_digital
        self.update()

    def update_live_magnitude(self, raw_mag: float, out_mag: float) -> None:
        self.live_raw_mag = max(0.0, min(1.0, raw_mag))
        self.live_out_mag = max(0.0, min(1.0, out_mag))
        self.update()

    def _get_dotted_points(self) -> List[List[float]]:
        if self.curve_type.lower() != "dotted" or not self.custom_eq:
            return []
        try:
            dots = json.loads(self.custom_eq)
            if isinstance(dots, list) and all(isinstance(d, list) and len(d) == 2 for d in dots):
                return dots
        except Exception:
            pass
        return []

    # --- Mouse Event Handlers for Dotted Drag & Drop ---
    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.LeftButton or self.curve_type.lower() != "dotted":
            return
        dots = self._get_dotted_points()
        if not dots:
            return

        w = float(self.width())
        h = float(self.height())
        mx = event.position().x()
        my = event.position().y()

        closest_idx = None
        min_dist = 14.0  # 14px hit radius

        for idx, d in enumerate(dots):
            px = d[0] * w
            py = h - (d[1] * h)
            dist = math.hypot(mx - px, my - py)
            if dist < min_dist:
                min_dist = dist
                closest_idx = idx

        self.active_dot_idx = closest_idx

    def mouseMoveEvent(self, event) -> None:
        if self.active_dot_idx is None or self.curve_type.lower() != "dotted":
            return
        dots = self._get_dotted_points()
        if not dots or self.active_dot_idx >= len(dots):
            return

        w = float(self.width())
        h = float(self.height())

        new_x = max(0.0, min(1.0, event.position().x() / w))
        new_y = max(0.0, min(1.0, (h - event.position().y()) / h))

        idx = self.active_dot_idx
        if idx == 0:
            new_x = 0.0
        elif idx == len(dots) - 1:
            new_x = 1.0

        if idx > 0:
            new_x = max(new_x, dots[idx - 1][0])
        if idx < len(dots) - 1:
            new_x = min(new_x, dots[idx + 1][0])

        dots[idx] = [round(new_x, 4), round(new_y, 4)]
        self.custom_eq = json.dumps(dots)
        self.dot_changed.emit(self.custom_eq)
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.active_dot_idx = None

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        try:
            from gui_v2.services.theme_manager import ThemeManager
            tm = ThemeManager.get_instance()
            accent_1 = tm.get_color("accent_1")
            accent_2 = tm.get_color("accent_2")
            bg_color = tm.get_color("background")
        except Exception:
            accent_1 = QColor(168, 85, 247)
            accent_2 = QColor(0, 245, 160)
            bg_color = QColor(22, 16, 36)

        w = self.width()
        h = self.height()
        painter.fillRect(self.rect(), QColor(bg_color.red(), bg_color.green(), bg_color.blue(), 215))

        # Grid lines
        painter.setPen(QPen(QColor(accent_1.red(), accent_1.green(), accent_1.blue(), 40), 1, Qt.DashLine))
        painter.drawLine(w // 2, 0, w // 2, h)
        painter.drawLine(0, h // 2, w, h // 2)

        # Response Curve Path
        path = QPainterPath()
        steps = 100
        for i in range(steps + 1):
            x_in = i / float(steps)
            if self.is_trigger:
                if self.is_digital:
                    out_val = 1.0 if x_in >= self.dz else 0.0
                else:
                    out_val = math_utils.process_trigger(
                        x_in, self.dz, self.adz, self.curve_type, self.power, self.rest_dz, self.sens, self.custom_eq
                    )
            else:
                out_val, _ = math_utils.process_analog_stick(
                    x_in, 0.0, self.dz, self.adz, self.curve_type, self.power, self.rest_dz, self.sens, self.custom_eq
                )

            px = x_in * w
            py = h - (out_val * h)
            if i == 0:
                path.moveTo(px, py)
            else:
                path.lineTo(px, py)

        painter.setPen(QPen(accent_2, 2.0))
        painter.drawPath(path)

        # Dotted Control Point Circles
        dots = self._get_dotted_points()
        if dots:
            for idx, d in enumerate(dots):
                px = d[0] * w
                py = h - (d[1] * h)
                is_active = (idx == self.active_dot_idx)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(accent_1 if is_active else QColor(accent_1.red(), accent_1.green(), accent_1.blue(), 180)))
                painter.drawEllipse(QPointF(px, py), 6.0, 6.0)

        # Live Cursor Dot (Output Accent #2 Color)
        if self.live_raw_mag > 0.0:
            cx = self.live_raw_mag * w
            cy = h - (self.live_out_mag * h)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(accent_2))
            painter.drawEllipse(QPointF(cx, cy), 6.0, 6.0)

        painter.end()


# ---------------------------------------------------------------------------
# DualStickRadarWidget (180x180 Crosshair Radar with Dual Dots)
# ---------------------------------------------------------------------------
class DualStickRadarWidget(QWidget):
    """
    180x180 2D X/Y Radar Canvas rendering DUAL live dots:
      - Cyan / Yellow Dot: Raw hardware input (raw_x, raw_y)
      - Purple / Green Dot: Processed output (out_x, out_y)
      - Dynamic Red Deadzone Circle Overlay
      - Dotted vector trailing lines linked to output dots
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(180, 180)

        self.raw_x: float = 0.0
        self.raw_y: float = 0.0
        self.out_x: float = 0.0
        self.out_y: float = 0.0
        self.deadzone: float = 0.0

    def set_deadzone(self, dz: float) -> None:
        self.deadzone = max(0.0, min(1.0, float(dz)))
        self.update()

    def update_positions(self, raw_x: float, raw_y: float, out_x: float, out_y: float) -> None:
        self.raw_x = raw_x
        self.raw_y = raw_y
        self.out_x = out_x
        self.out_y = out_y
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0
        max_r = (min(w, h) / 2.0) - 10.0

        try:
            from gui_v2.services.theme_manager import ThemeManager
            tm = ThemeManager.get_instance()
            accent_1 = tm.get_color("accent_1")
            accent_2 = tm.get_color("accent_2")
            bg_color = tm.get_color("background")
        except Exception:
            accent_1 = QColor(168, 85, 247)
            accent_2 = QColor(0, 245, 160)
            bg_color = QColor(22, 16, 36)

        painter.fillRect(self.rect(), QColor(bg_color.red(), bg_color.green(), bg_color.blue(), 215))

        # Grid lines
        painter.setPen(QPen(QColor(accent_1.red(), accent_1.green(), accent_1.blue(), 50), 1, Qt.DashLine))
        painter.drawEllipse(QPointF(cx, cy), max_r, max_r)
        painter.drawLine(QPointF(cx, 0), QPointF(cx, h))
        painter.drawLine(QPointF(0, cy), QPointF(w, cy))

        # Dynamic Inner Deadzone Circle Overlay (Transparent Red)
        if self.deadzone > 0.0:
            dz_radius = max_r * self.deadzone
            dz_pen = QPen(QColor(239, 68, 68, 140), 1.2, Qt.DashLine)
            painter.setPen(dz_pen)
            painter.setBrush(QBrush(QColor(239, 68, 68, 25)))
            painter.drawEllipse(QPointF(cx, cy), dz_radius, dz_radius)

        # 1. Raw Hardware Input Trailing Line & Dot (Accent #1 Color)
        rx_px = cx + (self.raw_x * max_r)
        ry_px = cy - (self.raw_y * max_r)
        if abs(self.raw_x) > 0.001 or abs(self.raw_y) > 0.001:
            raw_line_pen = QPen(QColor(accent_1.red(), accent_1.green(), accent_1.blue(), 160), 1.5, Qt.DotLine)
            painter.setPen(raw_line_pen)
            painter.drawLine(QPointF(cx, cy), QPointF(rx_px, ry_px))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(accent_1))
        painter.drawEllipse(QPointF(rx_px, ry_px), 6.0, 6.0)

        # 2. Processed Output Trailing Line & Dot (Accent #2 Color)
        ox_px = cx + (self.out_x * max_r)
        oy_px = cy - (self.out_y * max_r)
        if abs(self.out_x) > 0.001 or abs(self.out_y) > 0.001:
            out_line_pen = QPen(QColor(accent_2.red(), accent_2.green(), accent_2.blue(), 220), 1.5, Qt.DotLine)
            painter.setPen(out_line_pen)
            painter.drawLine(QPointF(cx, cy), QPointF(ox_px, oy_px))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(accent_2))
        painter.drawEllipse(QPointF(ox_px, oy_px), 6.0, 6.0)

        painter.end()


# ---------------------------------------------------------------------------
# TriggerPullBarWidget (60x180 Vertical Dual Actuation Meter)
# ---------------------------------------------------------------------------
class TriggerPullBarWidget(QWidget):
    """
    60x180 Vertical Actuation Meter canvas rendering DUAL fill bars:
      - Raw Pull Bar (Cyan)
      - Processed Output Bar (Neon Green)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 180)

        self.raw_val: float = 0.0
        self.out_val: float = 0.0

    def update_levels(self, raw_val: float, out_val: float) -> None:
        self.raw_val = max(0.0, min(1.0, raw_val))
        self.out_val = max(0.0, min(1.0, out_val))
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        try:
            from gui_v2.services.theme_manager import ThemeManager
            tm = ThemeManager.get_instance()
            accent_1 = tm.get_color("accent_1")
            accent_2 = tm.get_color("accent_2")
            bg_color = tm.get_color("background")
        except Exception:
            accent_1 = QColor(168, 85, 247)
            accent_2 = QColor(0, 245, 160)
            bg_color = QColor(22, 16, 36)

        w = self.width()
        h = self.height()
        painter.fillRect(self.rect(), QColor(bg_color.red(), bg_color.green(), bg_color.blue(), 215))

        margin = 8
        bar_w = 18
        max_h = h - (margin * 2)

        # Grid box
        painter.setPen(QPen(QColor(accent_1.red(), accent_1.green(), accent_1.blue(), 60), 1))
        painter.drawRect(margin, margin, bar_w, max_h)
        painter.drawRect(margin + bar_w + 8, margin, bar_w, max_h)

        # 1. Raw Fill Bar (Accent #1 Color)
        raw_h = self.raw_val * max_h
        if raw_h > 0:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(accent_1))
            painter.drawRect(margin + 1, int(h - margin - raw_h), bar_w - 1, int(raw_h))

        # 2. Processed Output Fill Bar (Accent #2 Color)
        out_h = self.out_val * max_h
        if out_h > 0:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(accent_2))
            painter.drawRect(margin + bar_w + 9, int(h - margin - out_h), bar_w - 1, int(out_h))

        painter.end()


# ---------------------------------------------------------------------------
# TuningView
# ---------------------------------------------------------------------------
class TuningView(QWidget):
    """
    Primary PySide6 Analog Tuning View with 100% v2.3-beta feature parity + RESET buttons.
    """
    def __init__(self, config_manager: Any = None, parent=None, controller_config: Any = None):
        super().__init__(parent)
        self.config = config_manager if config_manager is not None else controller_config


        # Debounced save timer (300ms)
        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(300)
        self.save_timer.timeout.connect(self._do_save)

        self._stick_widgets: Dict[str, Dict[str, Any]] = {}
        self._trigger_widgets: Dict[str, Dict[str, Any]] = {}
        self._cards: List[QGroupBox] = []

        self.setup_ui()
        self._setup_theme_sync()

    def _setup_theme_sync(self) -> None:
        try:
            from gui_v2.services.theme_manager import ThemeManager
            tm = ThemeManager.get_instance()
            tm.theme_changed.connect(self.on_theme_changed)
            self.on_theme_changed(tm.tokens)
        except Exception:
            pass

    @Slot(dict)
    def on_theme_changed(self, tokens: dict = None):
        try:
            from gui_v2.services.theme_manager import ThemeManager, color_to_rgba_str, color_to_hex6
            tm = ThemeManager.get_instance()
            bg_color = tm.get_color("background")
            accent_1 = tm.get_color("accent_1")
            accent_2 = tm.get_color("accent_2")

            bg_glass = color_to_rgba_str(bg_color, alpha_override=0.85)
            bg_inner = color_to_rgba_str(bg_color, alpha_override=0.60)
            border_glass = color_to_rgba_str(accent_1, alpha_override=0.35)
            accent_1_hex = color_to_hex6(accent_1)
            accent_2_hex = color_to_hex6(accent_2)
            accent_1_subtle = color_to_rgba_str(accent_1, alpha_override=0.20)
            accent_1_border = color_to_rgba_str(accent_1, alpha_override=0.50)

            card_qss = f"""
            QGroupBox {{
                background-color: {bg_glass};
                border: 1px solid {border_glass};
                border-radius: 10px;
                margin-top: 12px;
                color: #ffffff;
                font-weight: bold;
                font-size: 11px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
                color: #ffffff;
                font-weight: bold;
            }}
            """

            input_qss = f"""
            QLineEdit, QComboBox {{
                background-color: {bg_inner};
                border: 1.5px solid {border_glass};
                border-radius: 6px;
                color: #ffffff;
                padding: 3px 6px;
                font-size: 11px;
            }}
            QLineEdit:focus, QComboBox:focus {{
                border: 1.5px solid {accent_1_hex};
            }}
            QLineEdit::placeholder {{ color: rgba(255,255,255,0.4); font-style: italic; }}
            QComboBox QAbstractItemView {{ background: {color_to_rgba_str(bg_color, alpha_override=1.0)}; color: #ffffff; }}
            """

            slider_qss = f"""
            QSlider::groove:horizontal {{
                border: 1px solid {border_glass};
                height: 6px;
                background: {bg_inner};
                border-radius: 3px;
            }}
            QSlider::sub-page:horizontal {{
                background: {accent_1_hex};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: #ffffff;
                border: 1.5px solid {accent_1_hex};
                width: 14px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 7px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {accent_1_hex};
                border-color: #ffffff;
            }}
            """

            cb_qss = f"""
            QCheckBox {{ color: #ffffff; font-size: 11px; font-weight: bold; }}
            QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 4px;
                border: 1px solid {border_glass}; background: {bg_inner}; }}
            QCheckBox::indicator:checked {{ background: {accent_1_hex}; border-color: {accent_1_hex}; }}
            """

            btn_qss = f"""
            QPushButton {{
                background-color: {accent_1_subtle};
                border: 1px solid {accent_1_border};
                border-radius: 6px; color: #ffffff; padding: 4px 10px; font-size: 11px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {color_to_rgba_str(accent_1, alpha_override=0.40)}; border-color: {accent_1_hex}; }}
            QPushButton:pressed {{ background-color: {accent_1_hex}; }}
            """

            self.setStyleSheet(card_qss + input_qss + slider_qss + cb_qss + btn_qss)
            self.update()
        except RuntimeError:
            pass

    def mark_config_dirty(self) -> None:
        self.save_timer.start()

    def _do_save(self) -> None:
        try:
            if hasattr(self.config, 'save'):
                self.config.save()
                logger.debug("[TUNING] Config saved OK")
        except Exception as e:
            logger.error(f"[TUNING] Config save error: {e}", exc_info=True)

    # ------------------------------------------------------------------
    # UI Setup
    # ------------------------------------------------------------------
    def setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(10)

        # Header Row: Color Guide Button
        top_bar = QHBoxLayout()
        btn_color_guide = QPushButton("🎨 Color Guide")
        btn_color_guide.setFocusPolicy(Qt.NoFocus)
        btn_color_guide.setObjectName("btn_accent")
        btn_color_guide.clicked.connect(self._open_color_guide)
        top_bar.addWidget(btn_color_guide)
        top_bar.addStretch()

        outer.addLayout(top_bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        inner_widget = QWidget()
        inner_layout = QVBoxLayout(inner_widget)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(12)

        # Dual Stick Cards Row
        sticks_row = QHBoxLayout()
        sticks_row.setSpacing(12)

        self.left_stick_card = self._build_stick_card("Left Stick", "analog_left", "Stick_Left")
        self.right_stick_card = self._build_stick_card("Right Stick", "analog_right", "Stick_Right")

        sticks_row.addWidget(self.left_stick_card)
        sticks_row.addWidget(self.right_stick_card)
        inner_layout.addLayout(sticks_row)

        # Dual Trigger Cards Row
        triggers_row = QHBoxLayout()
        triggers_row.setSpacing(12)

        self.left_trig_card = self._build_trigger_card("Left Trigger (LT)", "trigger_left", "lt")
        self.right_trig_card = self._build_trigger_card("Right Trigger (RT)", "trigger_right", "rt")

        triggers_row.addWidget(self.left_trig_card)
        triggers_row.addWidget(self.right_trig_card)
        inner_layout.addLayout(triggers_row)

        inner_layout.addStretch()
        scroll.setWidget(inner_widget)
        outer.addWidget(scroll)

    # ------------------------------------------------------------------
    # Stick Card Builder
    # ------------------------------------------------------------------
    def _build_stick_card(self, title: str, config_key: str, section_name: str) -> QGroupBox:
        group = QGroupBox(title.upper())
        self._cards.append(group)
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        # Canvases Frame: Side-by-Side Dual Canvases
        canv_row = QHBoxLayout()
        canv_row.setSpacing(10)

        # Left Canvas: 1D Response Curve
        col_curve = QVBoxLayout()
        lbl_c = QLabel("Response Curve")
        lbl_c.setStyleSheet(_LABEL_STYLE)
        lbl_c.setAlignment(Qt.AlignCenter)
        curve_canvas = StickCurveCanvas(is_trigger=False, parent=self)
        col_curve.addWidget(lbl_c)
        col_curve.addWidget(curve_canvas)
        canv_row.addLayout(col_curve)

        # Right Canvas: 2D Position Radar with Dual Dots
        col_radar = QVBoxLayout()
        lbl_r = QLabel("Current Position")
        lbl_r.setStyleSheet(_LABEL_STYLE)
        lbl_r.setAlignment(Qt.AlignCenter)
        radar_canvas = DualStickRadarWidget(self)
        col_radar.addWidget(lbl_r)
        col_radar.addWidget(radar_canvas)
        canv_row.addLayout(col_radar)

        layout.addLayout(canv_row)

        # Action Buttons Row (Circularity, LaTeX, and RESET)
        btn_row = QHBoxLayout()
        btn_calib = QPushButton("🔄 Circularity Calibration")
        btn_calib.setFocusPolicy(Qt.NoFocus)
        btn_calib.setObjectName("btn_accent")
        btn_calib.clicked.connect(lambda: self.open_circularity_modal(section_name))

        btn_latex = QPushButton("📄 Export Math")
        btn_latex.setFocusPolicy(Qt.NoFocus)
        btn_latex.clicked.connect(lambda: self.open_latex_modal(config_key))

        btn_reset = QPushButton("↺ Reset Defaults")
        btn_reset.setFocusPolicy(Qt.NoFocus)
        btn_reset.setObjectName("btn_reset")

        btn_row.addWidget(btn_calib)
        btn_row.addWidget(btn_latex)
        btn_row.addWidget(btn_reset)
        layout.addLayout(btn_row)

        # Sliders & Controls Grid
        grid = QGridLayout()
        grid.setSpacing(6)

        cfg_data = getattr(self.config, 'data', {}).get(config_key, {})
        def_dz = float(cfg_data.get("deadzone", 0.05))
        def_adz = float(cfg_data.get("anti_deadzone", 0.0))
        def_rdz = float(cfg_data.get("rest_deadzone", 0.0))
        def_warp = float(cfg_data.get("warp_threshold", cfg_data.get("warped_stick_threshold", 0.0)))
        def_curve = str(cfg_data.get("curve", "linear"))
        def_factor = float(cfg_data.get("exp_factor", 1.0))
        def_sens = float(cfg_data.get("sensitivity", 1.0))
        def_custom = str(cfg_data.get("custom_eq", cfg_data.get("custom_curve", "")))
        def_circ_mode = str(cfg_data.get("circularity_mode", "disabled")).lower()

        row_idx = 0

        def make_slider_row(label_str: str, min_v: float, max_v: float, step_v: float, init_v: float, param_key: str):
            nonlocal row_idx
            lbl = QLabel(label_str)
            lbl.setStyleSheet(_LABEL_STYLE)

            slider = QSlider(Qt.Horizontal)
            slider.setFocusPolicy(Qt.NoFocus)
            num_steps = int(round((max_v - min_v) / step_v))
            slider.setRange(0, num_steps)

            init_step = int(round((init_v - min_v) / step_v))
            slider.setValue(init_step)

            val_lbl = QLabel(f"{init_v:.2f}")
            val_lbl.setStyleSheet("color: #ffffff; font-family: 'JetBrains Mono', monospace; font-size: 11px;")
            val_lbl.setFixedWidth(36)

            def on_slide(val_int: int):
                computed = min_v + (val_int * step_v)
                val_lbl.setText(f"{computed:.2f}")
                self._on_stick_param_changed(config_key, param_key, computed)

            slider.valueChanged.connect(on_slide)

            grid.addWidget(lbl, row_idx, 0)
            grid.addWidget(slider, row_idx, 1)
            grid.addWidget(val_lbl, row_idx, 2)
            row_idx += 1
            return slider, val_lbl

        sl_dz, _ = make_slider_row("Deadzone:", 0.00, 0.50, 0.01, def_dz, "deadzone")
        sl_adz, _ = make_slider_row("Anti-Deadzone:", 0.00, 0.50, 0.01, def_adz, "anti_deadzone")
        sl_rdz, _ = make_slider_row("Rest Deadzone:", 0.00, 0.30, 0.01, def_rdz, "rest_deadzone")
        sl_warp, _ = make_slider_row("Warp Threshold:", 0.00, 0.20, 0.01, def_warp, "warp_threshold")
        sl_factor, _ = make_slider_row("Curve Factor:", 0.50, 5.00, 0.10, def_factor, "exp_factor")
        sl_sens, _ = make_slider_row("Sensitivity:", 0.10, 5.00, 0.05, def_sens, "sensitivity")

        # Preset Selector
        lbl_preset = QLabel("Preset:")
        lbl_preset.setStyleSheet(_LABEL_STYLE)
        combo_preset = QComboBox()
        combo_preset.addItems(['linear', 'exponential', 'relaxed', 'aggressive', 'cubic', 'sigmoid', 'bezier', 'dotted', 'custom'])
        c_idx = combo_preset.findText(def_curve.lower())
        if c_idx >= 0:
            combo_preset.setCurrentIndex(c_idx)
        grid.addWidget(lbl_preset, row_idx, 0)
        grid.addWidget(combo_preset, row_idx, 1, 1, 2)
        row_idx += 1

        # Circularity Mode Selector
        lbl_circ = QLabel("Circularity Mode:")
        lbl_circ.setStyleSheet(_LABEL_STYLE)
        combo_circ = QComboBox()
        combo_circ.addItems(['disabled', 'before', 'after'])
        cm_idx = combo_circ.findText(def_circ_mode)
        if cm_idx >= 0:
            combo_circ.setCurrentIndex(cm_idx)
        combo_circ.currentTextChanged.connect(lambda txt: self._on_stick_param_changed(config_key, "circularity_mode", txt.lower()))
        grid.addWidget(lbl_circ, row_idx, 0)
        grid.addWidget(combo_circ, row_idx, 1, 1, 2)
        row_idx += 1

        # Number of Dots (for Dotted mode)
        lbl_dots = QLabel("Number of Dots:")
        lbl_dots.setStyleSheet(_LABEL_STYLE)
        combo_dots = QComboBox()
        combo_dots.addItems(['2', '3', '4', '5', '6', '7', '8'])
        combo_dots.setVisible(def_curve.lower() == "dotted")
        lbl_dots.setVisible(def_curve.lower() == "dotted")
        grid.addWidget(lbl_dots, row_idx, 0)
        grid.addWidget(combo_dots, row_idx, 1, 1, 2)
        row_idx += 1

        # Custom Equation Field
        lbl_custom = QLabel("Custom Math / Dots:")
        lbl_custom.setStyleSheet(_LABEL_STYLE)
        edit_custom = QLineEdit()
        edit_custom.setPlaceholderText("e.g. (x**power)*sin(x) or JSON dots array")
        edit_custom.setText(def_custom)
        edit_custom.setVisible(def_curve.lower() in ('custom', 'dotted'))
        lbl_custom.setVisible(def_curve.lower() in ('custom', 'dotted'))
        grid.addWidget(lbl_custom, row_idx, 0)
        grid.addWidget(edit_custom, row_idx, 1, 1, 2)
        row_idx += 1

        layout.addLayout(grid)

        # Sync Canvas Parameters
        curve_canvas.update_params(def_dz, def_adz, def_rdz, def_curve, def_factor, def_sens, def_custom)
        radar_canvas.set_deadzone(def_dz)

        # RESET Button Logic for Stick Card
        def reset_stick_defaults():
            if config_key not in self.config.data:
                self.config.data[config_key] = {}
            self.config.data[config_key]["deadzone"] = "0.00"
            self.config.data[config_key]["anti_deadzone"] = "0.00"
            self.config.data[config_key]["rest_deadzone"] = "0.00"
            self.config.data[config_key]["warp_threshold"] = "0.00"
            self.config.data[config_key]["exp_factor"] = "1.00"
            self.config.data[config_key]["sensitivity"] = "1.00"
            self.config.data[config_key]["curve"] = "linear"
            self.config.data[config_key]["circularity_mode"] = "disabled"
            self.config.data[config_key]["custom_eq"] = ""

            sl_dz.setValue(0)
            sl_adz.setValue(0)
            sl_rdz.setValue(0)
            sl_warp.setValue(0)
            sl_factor.setValue(int(round((1.00 - 0.50) / 0.10)))
            sl_sens.setValue(int(round((1.00 - 0.10) / 0.05)))
            combo_preset.setCurrentText("linear")
            combo_circ.setCurrentText("disabled")
            edit_custom.setText("")
            edit_custom.setVisible(False)
            combo_dots.setVisible(False)
            lbl_dots.setVisible(False)

            curve_canvas.update_params(0.0, 0.0, 0.0, "linear", 1.0, 1.0, "")
            radar_canvas.set_deadzone(0.0)
            self.mark_config_dirty()

        btn_reset.clicked.connect(reset_stick_defaults)

        # Wire Signals
        combo_preset.currentTextChanged.connect(
            lambda txt: self._on_preset_changed(config_key, txt, edit_custom, lbl_custom, combo_dots, lbl_dots)
        )
        combo_dots.currentTextChanged.connect(
            lambda txt: self._on_num_dots_changed(config_key, txt, edit_custom, curve_canvas)
        )
        edit_custom.textChanged.connect(
            lambda txt: self._on_custom_eq_changed(config_key, txt, curve_canvas)
        )
        curve_canvas.dot_changed.connect(
            lambda json_str: self._on_dot_dragged(config_key, json_str, edit_custom)
        )

        self._stick_widgets[config_key] = {
            "curve_canvas": curve_canvas,
            "radar_canvas": radar_canvas,
            "edit_custom": edit_custom,
            "combo_preset": combo_preset,
            "combo_circ": combo_circ
        }

        return group

    # ------------------------------------------------------------------
    # Trigger Card Builder (Full Stick-Parity Sliders & Curve Options)
    # ------------------------------------------------------------------
    def _build_trigger_card(self, title: str, config_key: str, trigger_id: str) -> QGroupBox:
        group = QGroupBox(title.upper())
        self._cards.append(group)
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        # Dual Canvases Frame (Curve Canvas + Vertical Pull Bar)
        canv_row = QHBoxLayout()
        canv_row.setSpacing(10)

        col_curve = QVBoxLayout()
        lbl_c = QLabel("Response Curve")
        lbl_c.setStyleSheet(_LABEL_STYLE)
        lbl_c.setAlignment(Qt.AlignCenter)
        curve_canvas = StickCurveCanvas(is_trigger=True, parent=self)
        col_curve.addWidget(lbl_c)
        col_curve.addWidget(curve_canvas)
        canv_row.addLayout(col_curve)

        col_bar = QVBoxLayout()
        lbl_b = QLabel("Trigger Pull")
        lbl_b.setStyleSheet(_LABEL_STYLE)
        lbl_b.setAlignment(Qt.AlignCenter)
        bar_widget = TriggerPullBarWidget(self)
        col_bar.addWidget(lbl_b)
        col_bar.addWidget(bar_widget)
        canv_row.addLayout(col_bar)

        layout.addLayout(canv_row)

        # Action Buttons Row (Export & RESET)
        btn_row = QHBoxLayout()
        btn_latex = QPushButton("📄 Export Math")
        btn_latex.setFocusPolicy(Qt.NoFocus)
        btn_latex.clicked.connect(lambda: self.open_latex_modal(config_key))

        btn_reset = QPushButton("↺ Reset Defaults")
        btn_reset.setFocusPolicy(Qt.NoFocus)
        btn_reset.setObjectName("btn_reset")

        btn_row.addWidget(btn_latex)
        btn_row.addWidget(btn_reset)
        layout.addLayout(btn_row)

        # Sliders Grid
        grid = QGridLayout()
        grid.setSpacing(6)

        cfg_data = getattr(self.config, 'data', {}).get(config_key, {})
        def_dz = float(cfg_data.get("deadzone", 0.00))
        def_adz = float(cfg_data.get("anti_deadzone", 0.00))
        def_rdz = float(cfg_data.get("rest_deadzone", 0.00))
        def_factor = float(cfg_data.get("exp_factor", 1.00))
        def_sens = float(cfg_data.get("sensitivity", 1.00))
        def_curve = str(cfg_data.get("curve", "linear"))
        def_custom = str(cfg_data.get("custom_eq", ""))

        settings = getattr(self.config, 'data', {}).get("settings", {})
        digital_key = f"digital_{trigger_id}"
        def_digital = str(settings.get(digital_key, cfg_data.get("digital", "false"))).lower() in ("true", "1", "yes")

        row_idx = 0

        def make_trig_slider_row(label_str: str, min_v: float, max_v: float, step_v: float, init_v: float, param_key: str):
            nonlocal row_idx
            lbl = QLabel(label_str)
            lbl.setStyleSheet(_LABEL_STYLE)

            slider = QSlider(Qt.Horizontal)
            slider.setFocusPolicy(Qt.NoFocus)
            num_steps = int(round((max_v - min_v) / step_v))
            slider.setRange(0, num_steps)

            init_step = int(round((init_v - min_v) / step_v))
            slider.setValue(init_step)

            val_lbl = QLabel(f"{init_v:.2f}")
            val_lbl.setStyleSheet("color: #ffffff; font-family: 'JetBrains Mono', monospace; font-size: 11px;")
            val_lbl.setFixedWidth(36)

            def on_slide(val_int: int):
                computed = min_v + (val_int * step_v)
                val_lbl.setText(f"{computed:.2f}")
                self._on_stick_param_changed(config_key, param_key, computed)

            slider.valueChanged.connect(on_slide)

            grid.addWidget(lbl, row_idx, 0)
            grid.addWidget(slider, row_idx, 1)
            grid.addWidget(val_lbl, row_idx, 2)
            row_idx += 1
            return slider, val_lbl

        sl_dz, _ = make_trig_slider_row("Deadzone:", 0.00, 0.50, 0.01, def_dz, "deadzone")
        sl_adz, _ = make_trig_slider_row("Anti-Deadzone:", 0.00, 0.50, 0.01, def_adz, "anti_deadzone")
        sl_rdz, _ = make_trig_slider_row("Rest Deadzone:", 0.00, 0.30, 0.01, def_rdz, "rest_deadzone")
        sl_factor, _ = make_trig_slider_row("Curve Factor:", 0.50, 5.00, 0.10, def_factor, "exp_factor")
        sl_sens, _ = make_trig_slider_row("Sensitivity:", 0.10, 5.00, 0.05, def_sens, "sensitivity")

        # Preset Selector
        lbl_preset = QLabel("Preset:")
        lbl_preset.setStyleSheet(_LABEL_STYLE)
        combo_preset = QComboBox()
        combo_preset.addItems(['linear', 'exponential', 'relaxed', 'aggressive', 'cubic', 'sigmoid', 'bezier', 'dotted', 'custom'])
        c_idx = combo_preset.findText(def_curve.lower())
        if c_idx >= 0:
            combo_preset.setCurrentIndex(c_idx)
        grid.addWidget(lbl_preset, row_idx, 0)
        grid.addWidget(combo_preset, row_idx, 1, 1, 2)
        row_idx += 1

        # Number of Dots (for Dotted mode)
        lbl_dots = QLabel("Number of Dots:")
        lbl_dots.setStyleSheet(_LABEL_STYLE)
        combo_dots = QComboBox()
        combo_dots.addItems(['2', '3', '4', '5', '6', '7', '8'])
        combo_dots.setVisible(def_curve.lower() == "dotted")
        lbl_dots.setVisible(def_curve.lower() == "dotted")
        grid.addWidget(lbl_dots, row_idx, 0)
        grid.addWidget(combo_dots, row_idx, 1, 1, 2)
        row_idx += 1

        # Custom Equation Field
        lbl_custom = QLabel("Custom Math / Dots:")
        lbl_custom.setStyleSheet(_LABEL_STYLE)
        edit_custom = QLineEdit()
        edit_custom.setPlaceholderText("e.g. (x**power)*sin(x) or JSON dots array")
        edit_custom.setText(def_custom)
        edit_custom.setVisible(def_curve.lower() in ('custom', 'dotted'))
        lbl_custom.setVisible(def_curve.lower() in ('custom', 'dotted'))
        grid.addWidget(lbl_custom, row_idx, 0)
        grid.addWidget(edit_custom, row_idx, 1, 1, 2)
        row_idx += 1

        # Digital Trigger Mode Checkbox
        cb_digital = QCheckBox("Digital Trigger Mode")
        cb_digital.setFocusPolicy(Qt.NoFocus)
        cb_digital.setChecked(def_digital)
        cb_digital.setChecked(def_digital)
        cb_digital.stateChanged.connect(lambda st: self._on_digital_trig_changed(config_key, trigger_id, bool(st)))
        grid.addWidget(cb_digital, row_idx, 0, 1, 3)

        layout.addLayout(grid)

        curve_canvas.update_params(def_dz, def_adz, def_rdz, def_curve, def_factor, def_sens, def_custom, def_digital)

        # RESET Button Logic for Trigger Card
        def reset_trigger_defaults():
            if config_key not in self.config.data:
                self.config.data[config_key] = {}
            self.config.data[config_key]["deadzone"] = "0.00"
            self.config.data[config_key]["anti_deadzone"] = "0.00"
            self.config.data[config_key]["rest_deadzone"] = "0.00"
            self.config.data[config_key]["exp_factor"] = "1.00"
            self.config.data[config_key]["sensitivity"] = "1.00"
            self.config.data[config_key]["curve"] = "linear"
            self.config.data[config_key]["custom_eq"] = ""

            if "settings" not in self.config.data:
                self.config.data["settings"] = {}
            self.config.data["settings"][f"digital_{trigger_id}"] = "false"

            sl_dz.setValue(0)
            sl_adz.setValue(0)
            sl_rdz.setValue(0)
            sl_factor.setValue(int(round((1.00 - 0.50) / 0.10)))
            sl_sens.setValue(int(round((1.00 - 0.10) / 0.05)))
            combo_preset.setCurrentText("linear")
            cb_digital.setChecked(False)
            edit_custom.setText("")
            edit_custom.setVisible(False)
            combo_dots.setVisible(False)
            lbl_dots.setVisible(False)

            curve_canvas.update_params(0.0, 0.0, 0.0, "linear", 1.0, 1.0, "", False)
            self.mark_config_dirty()

        btn_reset.clicked.connect(reset_trigger_defaults)

        # Wire Signals
        combo_preset.currentTextChanged.connect(
            lambda txt: self._on_preset_changed(config_key, txt, edit_custom, lbl_custom, combo_dots, lbl_dots)
        )
        combo_dots.currentTextChanged.connect(
            lambda txt: self._on_num_dots_changed(config_key, txt, edit_custom, curve_canvas)
        )
        edit_custom.textChanged.connect(
            lambda txt: self._on_custom_eq_changed(config_key, txt, curve_canvas)
        )
        curve_canvas.dot_changed.connect(
            lambda json_str: self._on_dot_dragged(config_key, json_str, edit_custom)
        )

        self._trigger_widgets[config_key] = {
            "curve_canvas": curve_canvas,
            "bar_widget": bar_widget,
            "digital": cb_digital,
            "edit_custom": edit_custom,
            "combo_preset": combo_preset
        }

        return group

    # ------------------------------------------------------------------
    # Dynamic Slot Updates & Handlers
    # ------------------------------------------------------------------
    def _on_stick_param_changed(self, config_key: str, param: str, val: Any) -> None:
        if config_key not in self.config.data:
            self.config.data[config_key] = {}

        self.config.data[config_key][param] = str(val) if not isinstance(val, str) else val

        # Refresh canvas
        w = self._stick_widgets.get(config_key, self._trigger_widgets.get(config_key, {}))
        canvas: Optional[StickCurveCanvas] = w.get("curve_canvas")
        if canvas:
            cfg = self.config.data[config_key]
            is_dig = str(self.config.data.get("settings", {}).get(f"digital_{config_key.replace('trigger_', '')}", "false")).lower() in ("true", "1")
            canvas.update_params(
                float(cfg.get("deadzone", 0.00)),
                float(cfg.get("anti_deadzone", 0.00)),
                float(cfg.get("rest_deadzone", 0.00)),
                str(cfg.get("curve", "linear")),
                float(cfg.get("exp_factor", 1.00)),
                float(cfg.get("sensitivity", 1.00)),
                str(cfg.get("custom_eq", cfg.get("custom_curve", ""))),
                is_dig
            )

        radar: Optional[DualStickRadarWidget] = w.get("radar_canvas")
        if radar and param == "deadzone":
            try:
                radar.set_deadzone(float(val))
            except Exception:
                pass

        self.mark_config_dirty()

    def _on_preset_changed(
        self, config_key: str, preset_str: str,
        edit_custom: QLineEdit, lbl_custom: QLabel,
        combo_dots: QComboBox, lbl_dots: QLabel
    ) -> None:
        p_lower = preset_str.lower()
        if config_key not in self.config.data:
            self.config.data[config_key] = {}
        self.config.data[config_key]["curve"] = p_lower

        is_custom = (p_lower == "custom")
        is_dotted = (p_lower == "dotted")

        edit_custom.setVisible(is_custom or is_dotted)
        lbl_custom.setVisible(is_custom or is_dotted)
        combo_dots.setVisible(is_dotted)
        lbl_dots.setVisible(is_dotted)

        if is_dotted:
            n_dots = int(combo_dots.currentText())
            self._generate_dots_json(config_key, n_dots, edit_custom)

        self._on_stick_param_changed(config_key, "curve", p_lower)

    def _on_num_dots_changed(self, config_key: str, dots_str: str, edit_custom: QLineEdit, canvas: StickCurveCanvas) -> None:
        try:
            n = int(dots_str)
            self._generate_dots_json(config_key, n, edit_custom)
        except Exception:
            pass

    def _generate_dots_json(self, config_key: str, n: int, edit_custom: QLineEdit) -> None:
        dots = [[round(i / float(n - 1), 4), round(i / float(n - 1), 4)] for i in range(n)]
        json_str = json.dumps(dots)
        edit_custom.setText(json_str)
        self.config.data[config_key]["custom_eq"] = json_str
        self._on_stick_param_changed(config_key, "custom_eq", json_str)

    def _on_custom_eq_changed(self, config_key: str, text: str, canvas: StickCurveCanvas) -> None:
        self.config.data[config_key]["custom_eq"] = text
        self._on_stick_param_changed(config_key, "custom_eq", text)

    def _on_dot_dragged(self, config_key: str, json_str: str, edit_custom: QLineEdit) -> None:
        edit_custom.setText(json_str)
        self.config.data[config_key]["custom_eq"] = json_str
        self.mark_config_dirty()

    def _on_digital_trig_changed(self, config_key: str, trigger_id: str, checked: bool) -> None:
        if "settings" not in self.config.data:
            self.config.data["settings"] = {}
        self.config.data["settings"][f"digital_{trigger_id}"] = "true" if checked else "false"

        wt = self._trigger_widgets.get(config_key, {})
        canvas: Optional[StickCurveCanvas] = wt.get("curve_canvas")
        if canvas:
            cfg = self.config.data.get(config_key, {})
            canvas.update_params(
                float(cfg.get("deadzone", 0.00)),
                float(cfg.get("anti_deadzone", 0.00)),
                float(cfg.get("rest_deadzone", 0.00)),
                str(cfg.get("curve", "linear")),
                float(cfg.get("exp_factor", 1.00)),
                float(cfg.get("sensitivity", 1.00)),
                str(cfg.get("custom_eq", "")),
                checked
            )
        self.mark_config_dirty()

    # ------------------------------------------------------------------
    # Telemetry Updates (~500Hz)
    # ------------------------------------------------------------------
    @Slot(dict)
    def update_telemetry(self, state_dict: dict) -> None:
        if not isinstance(state_dict, dict):
            return

        # Raw hardware inputs
        raw_lx = float(state_dict.get("lx", 0.0))
        raw_ly = float(state_dict.get("ly", 0.0))
        raw_rx = float(state_dict.get("rx", 0.0))
        raw_ry = float(state_dict.get("ry", 0.0))
        raw_lt = float(state_dict.get("lt", 0.0))
        raw_rt = float(state_dict.get("rt", 0.0))

        # 1. Left Stick Telemetry & Output Calculation
        cfg_ls = getattr(self.config, 'data', {}).get("analog_left", {})
        ls_dz = float(cfg_ls.get("deadzone", 0.00))
        ls_adz = float(cfg_ls.get("anti_deadzone", 0.00))
        ls_rdz = float(cfg_ls.get("rest_deadzone", 0.00))
        ls_curve = str(cfg_ls.get("curve", "linear"))
        ls_factor = float(cfg_ls.get("exp_factor", 1.00))
        ls_sens = float(cfg_ls.get("sensitivity", 1.00))
        ls_custom = str(cfg_ls.get("custom_eq", cfg_ls.get("custom_curve", "")))
        ls_warp = float(cfg_ls.get("warp_threshold", cfg_ls.get("warped_stick_threshold", 0.00)))
        ls_circ_mode = str(cfg_ls.get("circularity_mode", "disabled")).lower()
        ls_cx = float(cfg_ls.get("circularity_center_x", 0.0))
        ls_cy = float(cfg_ls.get("circularity_center_y", 0.0))
        ls_bounds_str = str(cfg_ls.get("circularity_bounds", ""))
        ls_bounds = [float(x) for x in ls_bounds_str.split(",")] if ls_bounds_str and len(ls_bounds_str.split(",")) == 360 else None

        # Process Left Stick Output
        out_lx, out_ly = math_utils.apply_warped_stick_correction(raw_lx, raw_ly, ls_warp)
        if ls_circ_mode == "before":
            out_lx, out_ly = math_utils.apply_circularity_correction(out_lx, out_ly, ls_cx, ls_cy, ls_bounds)
            out_lx, out_ly = math_utils.process_analog_stick(out_lx, out_ly, ls_dz, ls_adz, ls_curve, ls_factor, ls_rdz, ls_sens, ls_custom)
        elif ls_circ_mode == "after":
            out_lx, out_ly = math_utils.process_analog_stick(out_lx, out_ly, ls_dz, ls_adz, ls_curve, ls_factor, ls_rdz, ls_sens, ls_custom)
            out_lx, out_ly = math_utils.apply_circularity_correction(out_lx, out_ly, ls_cx, ls_cy, ls_bounds)
        else:
            out_lx, out_ly = math_utils.process_analog_stick(out_lx, out_ly, ls_dz, ls_adz, ls_curve, ls_factor, ls_rdz, ls_sens, ls_custom)

        w_ls = self._stick_widgets.get("analog_left", {})
        if "radar_canvas" in w_ls and w_ls["radar_canvas"]:
            w_ls["radar_canvas"].update_positions(raw_lx, raw_ly, out_lx, out_ly)
        if "curve_canvas" in w_ls and w_ls["curve_canvas"]:
            raw_mag = math.hypot(raw_lx, raw_ly)
            out_mag = math.hypot(out_lx, out_ly)
            w_ls["curve_canvas"].update_live_magnitude(raw_mag, out_mag)

        # 2. Right Stick Telemetry & Output Calculation
        cfg_rs = getattr(self.config, 'data', {}).get("analog_right", {})
        rs_dz = float(cfg_rs.get("deadzone", 0.00))
        rs_adz = float(cfg_rs.get("anti_deadzone", 0.00))
        rs_rdz = float(cfg_rs.get("rest_deadzone", 0.00))
        rs_curve = str(cfg_rs.get("curve", "linear"))
        rs_factor = float(cfg_rs.get("exp_factor", 1.00))
        rs_sens = float(cfg_rs.get("sensitivity", 1.00))
        rs_custom = str(cfg_rs.get("custom_eq", cfg_rs.get("custom_curve", "")))
        rs_warp = float(cfg_rs.get("warp_threshold", cfg_rs.get("warped_stick_threshold", 0.00)))
        rs_circ_mode = str(cfg_rs.get("circularity_mode", "disabled")).lower()
        rs_cx = float(cfg_rs.get("circularity_center_x", 0.0))
        rs_cy = float(cfg_rs.get("circularity_center_y", 0.0))
        rs_bounds_str = str(cfg_rs.get("circularity_bounds", ""))
        rs_bounds = [float(x) for x in rs_bounds_str.split(",")] if rs_bounds_str and len(rs_bounds_str.split(",")) == 360 else None

        out_rx, out_ry = math_utils.apply_warped_stick_correction(raw_rx, raw_ry, rs_warp)
        if rs_circ_mode == "before":
            out_rx, out_ry = math_utils.apply_circularity_correction(out_rx, out_ry, rs_cx, rs_cy, rs_bounds)
            out_rx, out_ry = math_utils.process_analog_stick(out_rx, out_ry, rs_dz, rs_adz, rs_curve, rs_factor, rs_rdz, rs_sens, rs_custom)
        elif rs_circ_mode == "after":
            out_rx, out_ry = math_utils.process_analog_stick(out_rx, out_ry, rs_dz, rs_adz, rs_curve, rs_factor, rs_rdz, rs_sens, rs_custom)
            out_rx, out_ry = math_utils.apply_circularity_correction(out_rx, out_ry, rs_cx, rs_cy, rs_bounds)
        else:
            out_rx, out_ry = math_utils.process_analog_stick(out_rx, out_ry, rs_dz, rs_adz, rs_curve, rs_factor, rs_rdz, rs_sens, rs_custom)

        w_rs = self._stick_widgets.get("analog_right", {})
        if "radar_canvas" in w_rs and w_rs["radar_canvas"]:
            w_rs["radar_canvas"].update_positions(raw_rx, raw_ry, out_rx, out_ry)
        if "curve_canvas" in w_rs and w_rs["curve_canvas"]:
            raw_mag = math.hypot(raw_rx, raw_ry)
            out_mag = math.hypot(out_rx, out_ry)
            w_rs["curve_canvas"].update_live_magnitude(raw_mag, out_mag)

        # 3. Triggers Telemetry & Output Calculation
        cfg_lt = getattr(self.config, 'data', {}).get("trigger_left", {})
        lt_dz = float(cfg_lt.get("deadzone", 0.00))
        lt_adz = float(cfg_lt.get("anti_deadzone", 0.00))
        lt_rdz = float(cfg_lt.get("rest_deadzone", 0.00))
        lt_curve = str(cfg_lt.get("curve", "linear"))
        lt_factor = float(cfg_lt.get("exp_factor", 1.00))
        lt_sens = float(cfg_lt.get("sensitivity", 1.00))
        lt_custom = str(cfg_lt.get("custom_eq", ""))
        lt_dig = str(getattr(self.config, 'data', {}).get("settings", {}).get("digital_lt", "false")).lower() in ("true", "1")

        if lt_dig:
            out_lt = 1.0 if raw_lt >= lt_dz else 0.0
        else:
            out_lt = math_utils.process_trigger(raw_lt, lt_dz, lt_adz, lt_curve, lt_factor, lt_rdz, lt_sens, lt_custom)

        wt_lt = self._trigger_widgets.get("trigger_left", {})
        if "bar_widget" in wt_lt and wt_lt["bar_widget"]:
            wt_lt["bar_widget"].update_levels(raw_lt, out_lt)
        if "curve_canvas" in wt_lt and wt_lt["curve_canvas"]:
            wt_lt["curve_canvas"].update_live_magnitude(raw_lt, out_lt)

        cfg_rt = getattr(self.config, 'data', {}).get("trigger_right", {})
        rt_dz = float(cfg_rt.get("deadzone", 0.00))
        rt_adz = float(cfg_rt.get("anti_deadzone", 0.00))
        rt_rdz = float(cfg_rt.get("rest_deadzone", 0.00))
        rt_curve = str(cfg_rt.get("curve", "linear"))
        rt_factor = float(cfg_rt.get("exp_factor", 1.00))
        rt_sens = float(cfg_rt.get("sensitivity", 1.00))
        rt_custom = str(cfg_rt.get("custom_eq", ""))
        rt_dig = str(getattr(self.config, 'data', {}).get("settings", {}).get("digital_rt", "false")).lower() in ("true", "1")

        if rt_dig:
            out_rt = 1.0 if raw_rt >= rt_dz else 0.0
        else:
            out_rt = math_utils.process_trigger(raw_rt, rt_dz, rt_adz, rt_curve, rt_factor, rt_rdz, rt_sens, rt_custom)

        wt_rt = self._trigger_widgets.get("trigger_right", {})
        if "bar_widget" in wt_rt and wt_rt["bar_widget"]:
            wt_rt["bar_widget"].update_levels(raw_rt, out_rt)
        if "curve_canvas" in wt_rt and wt_rt["curve_canvas"]:
            wt_rt["curve_canvas"].update_live_magnitude(raw_rt, out_rt)

    # ------------------------------------------------------------------
    # Dialog Launchers
    # ------------------------------------------------------------------
    def _open_color_guide(self) -> None:
        dlg = ColorGuideModal(parent=self)
        dlg.exec()

    def open_circularity_modal(self, section_name: str) -> None:
        modal = CircularityCalibrationModal(parent=self, section_name=section_name, config_manager=self.config)
        main_win = self.window()
        worker = getattr(main_win, 'telemetry_worker', getattr(main_win, 'udp_worker', None))
        sig = getattr(worker, 'telemetry_updated', getattr(worker, 'telemetry_received', None)) if worker else None

        if sig:
            sig.connect(modal.update_telemetry)

        try:
            modal.exec()
        finally:
            if sig:
                try:
                    sig.disconnect(modal.update_telemetry)
                except Exception:
                    pass

    def open_latex_modal(self, config_key: str) -> None:
        cfg_data = getattr(self.config, 'data', {}).get(config_key, {})
        curve_type = str(cfg_data.get("curve", "linear"))
        power = float(cfg_data.get("exp_factor", 1.00))
        inner_dz = float(cfg_data.get("deadzone", 0.00))
        anti_dz = float(cfg_data.get("anti_deadzone", 0.00))
        rest_dz = float(cfg_data.get("rest_deadzone", 0.00))
        custom_eq = str(cfg_data.get("custom_eq", cfg_data.get("custom_curve", "")))

        dlg = LatexExportModal(curve_type, power, inner_dz, anti_dz, rest_dz, custom_eq, parent=self)
        dlg.exec()


if __name__ == "__main__":
    from config_manager import ControllerConfig

    app = QApplication(sys.argv)
    cfg = ControllerConfig()
    view = TuningView(cfg)
    view.setWindowTitle("TuningView Complete Reset & Trigger Controls Test")
    view.resize(1050, 750)
    view.show()
    sys.exit(app.exec())
