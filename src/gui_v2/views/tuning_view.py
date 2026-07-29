"""
Analog Tuning View Module for PySide6 UI (gui_v2).

Provides high-precision analog stick & trigger response curve tuning with:
  - Dual stick radar visualizers & live deadzone ring displays
  - 60Hz Circularity Calibration modal launcher
  - LaTeX mathematical curve exporter for Desmos
  - Dynamic deadzones (Inner, Anti, Rest, Warp Threshold)
  - Curve presets (linear, exponential, relaxed, aggressive, cubic, sigmoid, bezier, dotted, custom)
  - Custom safe math equation validator
  - Dual trigger actuation response curve graphs & digital trigger mode toggle
  - Debounced (300ms) config disk writes
"""

import sys
import os
import math
import logging
from typing import Dict, Any, List, Optional, Tuple

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QLineEdit, QCheckBox, QComboBox, QGroupBox,
    QDoubleSpinBox, QScrollArea, QFrame, QDialog, QTextEdit,
    QApplication, QMessageBox
)
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath, QPolygonF
from PySide6.QtCore import Qt, Slot, QTimer, QPointF

# Add root src directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import math_utils
import curves
from gui_v2.widgets.stick_radar import StickRadarWidget
from gui_v2.dialogs.circularity_modal import CircularityCalibrationModal

logger = logging.getLogger('tuning_view')


# ---------------------------------------------------------------------------
# QSS Styling Tokens
# ---------------------------------------------------------------------------
_CARD_STYLE = """
QGroupBox {
    background-color: rgba(22, 16, 36, 0.85);
    border: 1px solid rgba(168, 85, 247, 0.35);
    border-radius: 10px;
    margin-top: 12px;
    color: #a855f7;
    font-weight: bold;
    font-size: 11px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
}
"""

_INPUT_STYLE = """
QLineEdit, QComboBox, QDoubleSpinBox {
    background-color: #161024;
    border: 1.5px solid #a855f7;
    border-radius: 6px;
    color: #ffffff;
    padding: 3px 6px;
    font-size: 11px;
}
QLineEdit::placeholder { color: rgba(255,255,255,0.4); font-style: italic; }
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView { background: #161024; color: #ffffff; }
"""

_CB_STYLE = """
QCheckBox { color: #ffffff; font-size: 11px; font-weight: bold; }
QCheckBox::indicator { width: 16px; height: 16px; border-radius: 4px;
    border: 1px solid rgba(168,85,247,0.4); background: #161024; }
QCheckBox::indicator:checked { background: #a855f7; border-color: #a855f7; }
"""

_BTN_STYLE = """
QPushButton {
    background-color: rgba(168, 85, 247, 0.2);
    border: 1px solid rgba(168, 85, 247, 0.4);
    border-radius: 6px; color: #ffffff; padding: 4px 10px; font-size: 11px; font-weight: bold;
}
QPushButton:hover { background-color: rgba(168, 85, 247, 0.4); border-color: #a855f7; }
QPushButton:pressed { background-color: #7500ab; }
"""

_BTN_ACCENT = """
QPushButton {
    background-color: rgba(0, 245, 160, 0.2);
    border: 1px solid rgba(0, 245, 160, 0.5);
    border-radius: 6px; color: #ffffff; padding: 4px 10px; font-size: 11px; font-weight: bold;
}
QPushButton:hover { background-color: rgba(0, 245, 160, 0.4); }
"""

_LABEL_STYLE = "color: rgba(255, 255, 255, 0.7); font-size: 11px; font-weight: bold;"


# ---------------------------------------------------------------------------
# TriggerCurveCanvas Widget
# ---------------------------------------------------------------------------
class TriggerCurveCanvas(QWidget):
    """
    2D response curve preview canvas rendering trigger actuation:
      - Input [0.0..1.0] (horizontal) vs Output [0.0..1.0] (vertical)
      - Smooth curve path generated via math_utils.process_trigger()
      - Crisp step-function when digital trigger mode is enabled
      - Live actuation level indicator line
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(140)

        self.inner_dz: float = 0.05
        self.anti_dz: float = 0.0
        self.max_dz: float = 1.0
        self.curve_type: str = "linear"
        self.power: float = 1.0
        self.is_digital: bool = False
        self.live_val: float = 0.0

    def update_params(
        self,
        inner_dz: float,
        anti_dz: float,
        max_dz: float,
        curve_type: str,
        power: float,
        is_digital: bool
    ) -> None:
        self.inner_dz = inner_dz
        self.anti_dz = anti_dz
        self.max_dz = max_dz
        self.curve_type = curve_type
        self.power = power
        self.is_digital = is_digital
        self.update()

    def update_live_value(self, val: float) -> None:
        self.live_val = max(0.0, min(1.0, val))
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = self.rect()
        w = rect.width()
        h = rect.height()

        margin = 25
        pw = w - (margin * 2)
        ph = h - (margin * 2)

        # Background
        painter.fillRect(rect, QColor(22, 16, 36, 215))

        if pw <= 0 or ph <= 0:
            painter.end()
            return

        # 1. Draw Grid Lines
        painter.setPen(QPen(QColor(168, 85, 247, 40), 1, Qt.DashLine))
        for step in (0.25, 0.50, 0.75):
            gx = margin + (pw * step)
            gy = margin + ph - (ph * step)
            painter.drawLine(QPointF(gx, margin), QPointF(gx, margin + ph))
            painter.drawLine(QPointF(margin, gy), QPointF(margin + pw, gy))

        # 2. Draw Axes
        painter.setPen(QPen(QColor(168, 85, 247, 100), 1.5))
        painter.drawLine(QPointF(margin, margin + ph), QPointF(margin + pw, margin + ph))
        painter.drawLine(QPointF(margin, margin), QPointF(margin, margin + ph))

        # 3. Render Response Curve Path
        path = QPainterPath()
        steps = 100

        for i in range(steps + 1):
            t_in = i / float(steps)

            if self.is_digital:
                out = 1.0 if t_in >= self.inner_dz else 0.0
            else:
                # Scale t_in against max_dz
                effective_in = min(t_in / self.max_dz, 1.0) if self.max_dz > 0.0 else t_in
                out = math_utils.process_trigger(
                    effective_in, self.inner_dz, self.anti_dz,
                    self.curve_type, self.power
                )

            px = margin + (t_in * pw)
            py = margin + ph - (out * ph)

            if i == 0:
                path.moveTo(px, py)
            else:
                path.lineTo(px, py)

        painter.setPen(QPen(QColor(0, 245, 160) if not self.is_digital else QColor(168, 85, 247), 2.0))
        painter.drawPath(path)

        # 4. Live Value Indicator Line
        if self.live_val > 0.0:
            lx = margin + (self.live_val * pw)
            painter.setPen(QPen(QColor(245, 158, 11), 1.5, Qt.SolidLine))
            painter.drawLine(QPointF(lx, margin), QPointF(lx, margin + ph))

        painter.end()


# ---------------------------------------------------------------------------
# LatexExportModal
# ---------------------------------------------------------------------------
class LatexExportModal(QDialog):
    """
    QDialog displaying mathematical LaTeX string exports for Desmos visualization.
    """
    def __init__(self, curve_type: str, power: float, inner_dz: float, anti_dz: float, rest_dz: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Curve Math (LaTeX)")
        self.setMinimumSize(460, 280)
        self.setStyleSheet("QDialog { background-color: #0f0a1e; color: #ffffff; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        header = QLabel("📄 DESMOS / LATEX MATHEMATICAL FORMULA")
        header.setStyleSheet("color: #a855f7; font-weight: bold; font-size: 12px;")
        layout.addWidget(header)

        latex_str = curves.export_to_latex(curve_type, power, inner_dz, anti_dz, rest_dz)

        self.text_box = QTextEdit()
        self.text_box.setReadOnly(True)
        self.text_box.setText(latex_str)
        self.text_box.setStyleSheet("""
            QTextEdit {
                background-color: #161024;
                border: 1.5px solid #a855f7;
                border-radius: 6px;
                color: #00f5a0;
                font-family: 'JetBrains Mono', 'Consolas', monospace;
                font-size: 11px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.text_box)

        btn_row = QHBoxLayout()
        btn_copy = QPushButton("Copy to Clipboard")
        btn_copy.setFocusPolicy(Qt.NoFocus)
        btn_copy.setStyleSheet(_BTN_ACCENT)
        btn_copy.clicked.connect(self._copy_to_clipboard)

        btn_close = QPushButton("Close")
        btn_close.setFocusPolicy(Qt.NoFocus)
        btn_close.setStyleSheet(_BTN_STYLE)
        btn_close.clicked.connect(self.accept)

        btn_row.addWidget(btn_copy)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)

        layout.addLayout(btn_row)

    def _copy_to_clipboard(self) -> None:
        QApplication.clipboard().setText(self.text_box.toPlainText())
        QMessageBox.information(self, "Copied", "LaTeX formula copied to clipboard!")


# ---------------------------------------------------------------------------
# CircularityInfoModal
# ---------------------------------------------------------------------------
class CircularityInfoModal(QDialog):
    """
    Informational modal explaining circularity error, warped stick scaling, and deadzones.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Analog Stick Tuning & Circularity Info")
        self.setMinimumSize(480, 320)
        self.setStyleSheet("QDialog { background-color: #0f0a1e; color: #ffffff; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        header = QLabel("❓ ANALOG TUNING & CIRCULARITY EXPLANATION")
        header.setStyleSheet("color: #a855f7; font-weight: bold; font-size: 12px;")
        layout.addWidget(header)

        info_text = (
            "<b>1. Inner Deadzone:</b> Suppresses small resting stick jitter near the center.<br>"
            "<b>2. Anti-Deadzone:</b> Offsets output to bypass game-level deadzones (e.g. in FPS games).<br>"
            "<b>3. Rest Deadzone:</b> Secondary buffer preventing anti-deadzone from activating on drift.<br>"
            "<b>4. Warp Threshold:</b> Scaled outer threshold for asymmetric/weak axes to ensure full 1.0 diagonal reach.<br>"
            "<b>5. Circularity Calibration:</b> 360-degree polar sweep mapping that normalizes physical stick geometry into a true unit circle.<br>"
            "<b>6. Digital Trigger Mode:</b> Converts analog trigger actuation directly into binary 0 or 100% threshold clicks."
        )

        label = QLabel(info_text)
        label.setWordWrap(True)
        label.setTextFormat(Qt.RichText)
        label.setStyleSheet("color: rgba(255, 255, 255, 0.85); font-size: 11px; line-height: 1.4;")
        layout.addWidget(label)

        btn_close = QPushButton("Close")
        btn_close.setFocusPolicy(Qt.NoFocus)
        btn_close.setStyleSheet(_BTN_STYLE)
        btn_close.clicked.connect(self.accept)

        layout.addStretch()
        layout.addWidget(btn_close, 0, Qt.AlignRight)


# ---------------------------------------------------------------------------
# TuningView
# ---------------------------------------------------------------------------
class TuningView(QWidget):
    """
    Primary Analog Tuning View containing:
      - Left & Right Stick tuning cards (Radars, Circularity modal launchers, LaTeX export, deadzones, curves, warp threshold)
      - Left & Right Trigger tuning cards (2D curve preview graphs, Min/Max deadzones, digital trigger mode)
      - 300ms debounced disk saving
    """
    def __init__(self, config_manager: Any, parent=None):
        super().__init__(parent)
        self.config = config_manager

        # Debounced write timer: fires 300ms after last change
        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(300)
        self.save_timer.timeout.connect(self._do_save)

        # Widget registries for live updates
        self._stick_widgets: Dict[str, Dict[str, QWidget]] = {}
        self._trigger_widgets: Dict[str, Dict[str, QWidget]] = {}

        self.setup_ui()

    def mark_config_dirty(self) -> None:
        """Restarts the 300ms debounced save timer."""
        self.save_timer.start()

    def _do_save(self) -> None:
        """Writes config data to disk when debounced timer fires."""
        try:
            if hasattr(self.config, 'save'):
                self.config.save()
                logger.debug("[TUNING] Config saved OK")
        except Exception as e:
            logger.error(f"[TUNING] Config save error: {e}", exc_info=True)

    # ------------------------------------------------------------------
    # UI Assembly
    # ------------------------------------------------------------------
    def setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        inner_widget = QWidget()
        inner_layout = QVBoxLayout(inner_widget)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(12)

        # 1. Dual Stick Cards Row (Side-by-Side)
        sticks_row = QHBoxLayout()
        sticks_row.setSpacing(12)

        self.left_stick_card = self._build_stick_card("Left Stick", "analog_left", "Stick_Left")
        self.right_stick_card = self._build_stick_card("Right Stick", "analog_right", "Stick_Right")

        sticks_row.addWidget(self.left_stick_card)
        sticks_row.addWidget(self.right_stick_card)
        inner_layout.addLayout(sticks_row)

        # 2. Dual Trigger Cards Row (Side-by-Side)
        triggers_row = QHBoxLayout()
        triggers_row.setSpacing(12)

        self.left_trig_card = self._build_trigger_card("Left Trigger (LT)", "trigger_left", "lt")
        self.right_trig_card = self._build_trigger_card("Right Trigger (RT)", "trigger_right", "rt")

        triggers_row.addWidget(self.left_trig_card)
        triggers_row.addWidget(self.right_trig_card)
        inner_layout.addLayout(triggers_row)

        # 3. Bottom Action Bar
        bottom_row = QHBoxLayout()
        btn_info = QPushButton("❓ Circularity Info Modal")
        btn_info.setFocusPolicy(Qt.NoFocus)
        btn_info.setStyleSheet(_BTN_STYLE)
        btn_info.clicked.connect(self._open_info_modal)
        bottom_row.addWidget(btn_info)
        bottom_row.addStretch()

        inner_layout.addLayout(bottom_row)
        inner_layout.addStretch()

        scroll.setWidget(inner_widget)
        outer.addWidget(scroll)

    # ------------------------------------------------------------------
    # Stick Card Builder
    # ------------------------------------------------------------------
    def _build_stick_card(self, title: str, config_key: str, section_name: str) -> QGroupBox:
        group = QGroupBox(title.upper())
        group.setStyleSheet(_CARD_STYLE)
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        # Radar Canvas
        radar = StickRadarWidget(f"{title.upper()} RADAR")
        layout.addWidget(radar)

        # Action Buttons Row (Circularity & LaTeX)
        btn_row = QHBoxLayout()
        btn_calib = QPushButton("🔄 Circularity Calibration")
        btn_calib.setFocusPolicy(Qt.NoFocus)
        btn_calib.setStyleSheet(_BTN_ACCENT)
        btn_calib.clicked.connect(lambda: self.open_circularity_modal(section_name))

        btn_latex = QPushButton("📄 Export Curve Math (LaTeX)")
        btn_latex.setFocusPolicy(Qt.NoFocus)
        btn_latex.setStyleSheet(_BTN_STYLE)
        btn_latex.clicked.connect(lambda: self.open_latex_modal(config_key))

        btn_row.addWidget(btn_calib)
        btn_row.addWidget(btn_latex)
        layout.addLayout(btn_row)

        # Sliders & SpinBoxes Grid
        grid = QGridLayout()
        grid.setSpacing(6)

        # Fetch initial config values
        cfg_data = getattr(self.config, 'data', {}).get(config_key, {})
        def_dz = float(cfg_data.get("deadzone", 0.05))
        def_adz = float(cfg_data.get("anti_deadzone", 0.0))
        def_rdz = float(cfg_data.get("rest_deadzone", 0.0))
        def_warp = float(cfg_data.get("warp_threshold", cfg_data.get("warped_stick_threshold", 0.0)))
        def_curve = str(cfg_data.get("curve", "linear"))
        def_factor = float(cfg_data.get("exp_factor", 1.0))
        def_sens = float(cfg_data.get("sensitivity", 1.0))
        def_custom = str(cfg_data.get("custom_eq", ""))

        # 1. Inner Deadzone
        lbl_dz = QLabel("Deadzone:")
        lbl_dz.setStyleSheet(_LABEL_STYLE)
        spin_dz = QDoubleSpinBox()
        spin_dz.setFocusPolicy(Qt.NoFocus)
        spin_dz.setStyleSheet(_INPUT_STYLE)
        spin_dz.setRange(0.00, 0.50)
        spin_dz.setSingleStep(0.01)
        spin_dz.setValue(def_dz)
        spin_dz.valueChanged.connect(lambda v: self._on_stick_param_changed(config_key, "deadzone", v))
        grid.addWidget(lbl_dz, 0, 0)
        grid.addWidget(spin_dz, 0, 1)

        # 2. Anti-Deadzone
        lbl_adz = QLabel("Anti-Deadzone:")
        lbl_adz.setStyleSheet(_LABEL_STYLE)
        spin_adz = QDoubleSpinBox()
        spin_adz.setFocusPolicy(Qt.NoFocus)
        spin_adz.setStyleSheet(_INPUT_STYLE)
        spin_adz.setRange(0.00, 0.30)
        spin_adz.setSingleStep(0.01)
        spin_adz.setValue(def_adz)
        spin_adz.valueChanged.connect(lambda v: self._on_stick_param_changed(config_key, "anti_deadzone", v))
        grid.addWidget(lbl_adz, 1, 0)
        grid.addWidget(spin_adz, 1, 1)

        # 3. Rest Deadzone
        lbl_rdz = QLabel("Rest Deadzone:")
        lbl_rdz.setStyleSheet(_LABEL_STYLE)
        spin_rdz = QDoubleSpinBox()
        spin_rdz.setFocusPolicy(Qt.NoFocus)
        spin_rdz.setStyleSheet(_INPUT_STYLE)
        spin_rdz.setRange(0.00, 0.20)
        spin_rdz.setSingleStep(0.01)
        spin_rdz.setValue(def_rdz)
        spin_rdz.valueChanged.connect(lambda v: self._on_stick_param_changed(config_key, "rest_deadzone", v))
        grid.addWidget(lbl_rdz, 2, 0)
        grid.addWidget(spin_rdz, 2, 1)

        # 4. Warp Threshold
        lbl_warp = QLabel("Warp Threshold:")
        lbl_warp.setStyleSheet(_LABEL_STYLE)
        spin_warp = QDoubleSpinBox()
        spin_warp.setFocusPolicy(Qt.NoFocus)
        spin_warp.setStyleSheet(_INPUT_STYLE)
        spin_warp.setRange(0.00, 0.20)
        spin_warp.setSingleStep(0.01)
        spin_warp.setValue(def_warp)
        spin_warp.valueChanged.connect(lambda v: self._on_stick_param_changed(config_key, "warp_threshold", v))
        grid.addWidget(lbl_warp, 3, 0)
        grid.addWidget(spin_warp, 3, 1)

        # 5. Curve Factor
        lbl_factor = QLabel("Curve Factor:")
        lbl_factor.setStyleSheet(_LABEL_STYLE)
        spin_factor = QDoubleSpinBox()
        spin_factor.setFocusPolicy(Qt.NoFocus)
        spin_factor.setStyleSheet(_INPUT_STYLE)
        spin_factor.setRange(0.10, 3.00)
        spin_factor.setSingleStep(0.05)
        spin_factor.setValue(def_factor)
        spin_factor.valueChanged.connect(lambda v: self._on_stick_param_changed(config_key, "exp_factor", v))
        grid.addWidget(lbl_factor, 4, 0)
        grid.addWidget(spin_factor, 4, 1)

        # 6. Sensitivity
        lbl_sens = QLabel("Sensitivity:")
        lbl_sens.setStyleSheet(_LABEL_STYLE)
        spin_sens = QDoubleSpinBox()
        spin_sens.setFocusPolicy(Qt.NoFocus)
        spin_sens.setStyleSheet(_INPUT_STYLE)
        spin_sens.setRange(0.10, 2.00)
        spin_sens.setSingleStep(0.05)
        spin_sens.setValue(def_sens)
        spin_sens.valueChanged.connect(lambda v: self._on_stick_param_changed(config_key, "sensitivity", v))
        grid.addWidget(lbl_sens, 5, 0)
        grid.addWidget(spin_sens, 5, 1)

        # 7. Preset Dropdown
        lbl_preset = QLabel("Preset:")
        lbl_preset.setStyleSheet(_LABEL_STYLE)
        combo_preset = QComboBox()
        combo_preset.setStyleSheet(_INPUT_STYLE)
        combo_preset.addItems(['linear', 'exponential', 'relaxed', 'aggressive', 'cubic', 'sigmoid', 'bezier', 'dotted', 'custom'])
        idx = combo_preset.findText(def_curve.lower())
        if idx >= 0:
            combo_preset.setCurrentIndex(idx)
        combo_preset.currentTextChanged.connect(lambda txt: self._on_stick_preset_changed(config_key, txt))
        grid.addWidget(lbl_preset, 6, 0)
        grid.addWidget(combo_preset, 6, 1)

        # 8. Custom Equation Field
        lbl_custom = QLabel("Custom Math:")
        lbl_custom.setStyleSheet(_LABEL_STYLE)
        edit_custom = QLineEdit()
        edit_custom.setStyleSheet(_INPUT_STYLE)
        edit_custom.setPlaceholderText("e.g. x^1.2 or x**power")
        edit_custom.setText(def_custom)
        edit_custom.setEnabled(def_curve.lower() in ('custom', 'dotted'))
        edit_custom.textChanged.connect(lambda txt: self._on_stick_param_changed(config_key, "custom_eq", txt))
        grid.addWidget(lbl_custom, 7, 0)
        grid.addWidget(edit_custom, 7, 1)

        layout.addLayout(grid)

        # Register widget references
        self._stick_widgets[config_key] = {
            "radar": radar,
            "dz": spin_dz,
            "adz": spin_adz,
            "rdz": spin_rdz,
            "warp": spin_warp,
            "factor": spin_factor,
            "sens": spin_sens,
            "preset": combo_preset,
            "custom": edit_custom
        }

        return group

    # ------------------------------------------------------------------
    # Trigger Card Builder
    # ------------------------------------------------------------------
    def _build_trigger_card(self, title: str, config_key: str, trigger_id: str) -> QGroupBox:
        group = QGroupBox(title.upper())
        group.setStyleSheet(_CARD_STYLE)
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        # Response Curve Canvas
        canvas = TriggerCurveCanvas(self)
        layout.addWidget(canvas)

        # Sliders Grid
        grid = QGridLayout()
        grid.setSpacing(6)

        cfg_data = getattr(self.config, 'data', {}).get(config_key, {})
        def_min_dz = float(cfg_data.get("deadzone", 0.05))
        def_max_dz = float(cfg_data.get("max_deadzone", 1.0))
        def_factor = float(cfg_data.get("exp_factor", 1.0))
        def_curve = str(cfg_data.get("curve", "linear"))

        # Check settings for digital mode
        settings = getattr(self.config, 'data', {}).get("settings", {})
        digital_key = f"digital_{trigger_id}"
        def_digital = str(settings.get(digital_key, cfg_data.get("digital", "false"))).lower() in ("true", "1", "yes")

        # 1. Min Deadzone
        lbl_min = QLabel("Min Deadzone:")
        lbl_min.setStyleSheet(_LABEL_STYLE)
        spin_min = QDoubleSpinBox()
        spin_min.setFocusPolicy(Qt.NoFocus)
        spin_min.setStyleSheet(_INPUT_STYLE)
        spin_min.setRange(0.00, 0.50)
        spin_min.setSingleStep(0.01)
        spin_min.setValue(def_min_dz)
        spin_min.valueChanged.connect(lambda v: self._on_trig_param_changed(config_key, trigger_id, "deadzone", v))
        grid.addWidget(lbl_min, 0, 0)
        grid.addWidget(spin_min, 0, 1)

        # 2. Max Deadzone
        lbl_max = QLabel("Max Deadzone:")
        lbl_max.setStyleSheet(_LABEL_STYLE)
        spin_max = QDoubleSpinBox()
        spin_max.setFocusPolicy(Qt.NoFocus)
        spin_max.setStyleSheet(_INPUT_STYLE)
        spin_max.setRange(0.50, 1.00)
        spin_max.setSingleStep(0.01)
        spin_max.setValue(def_max_dz)
        spin_max.valueChanged.connect(lambda v: self._on_trig_param_changed(config_key, trigger_id, "max_deadzone", v))
        grid.addWidget(lbl_max, 1, 0)
        grid.addWidget(spin_max, 1, 1)

        # 3. Curve Factor
        lbl_factor = QLabel("Curve Factor:")
        lbl_factor.setStyleSheet(_LABEL_STYLE)
        spin_factor = QDoubleSpinBox()
        spin_factor.setFocusPolicy(Qt.NoFocus)
        spin_factor.setStyleSheet(_INPUT_STYLE)
        spin_factor.setRange(0.10, 3.00)
        spin_factor.setSingleStep(0.05)
        spin_factor.setValue(def_factor)
        spin_factor.valueChanged.connect(lambda v: self._on_trig_param_changed(config_key, trigger_id, "exp_factor", v))
        grid.addWidget(lbl_factor, 2, 0)
        grid.addWidget(spin_factor, 2, 1)

        # 4. Digital Trigger Mode Checkbox
        cb_digital = QCheckBox("Digital Trigger Mode")
        cb_digital.setFocusPolicy(Qt.NoFocus)
        cb_digital.setStyleSheet(_CB_STYLE)
        cb_digital.setChecked(def_digital)
        cb_digital.stateChanged.connect(lambda st: self._on_digital_trig_changed(config_key, trigger_id, bool(st)))
        grid.addWidget(cb_digital, 3, 0, 1, 2)

        layout.addLayout(grid)

        # Sync Canvas Parameters
        canvas.update_params(def_min_dz, 0.0, def_max_dz, def_curve, def_factor, def_digital)

        self._trigger_widgets[config_key] = {
            "canvas": canvas,
            "min_dz": spin_min,
            "max_dz": spin_max,
            "factor": spin_factor,
            "digital": cb_digital
        }

        return group

    # ------------------------------------------------------------------
    # Parameter Mutation Slots
    # ------------------------------------------------------------------
    def _on_stick_param_changed(self, config_key: str, param: str, val: Any) -> None:
        if config_key not in self.config.data:
            self.config.data[config_key] = {}

        self.config.data[config_key][param] = str(val) if not isinstance(val, str) else val
        self.mark_config_dirty()

    def _on_stick_preset_changed(self, config_key: str, preset_text: str) -> None:
        preset_lower = preset_text.lower()
        if config_key not in self.config.data:
            self.config.data[config_key] = {}

        self.config.data[config_key]["curve"] = preset_lower

        widgets = self._stick_widgets.get(config_key, {})
        edit_custom = widgets.get("custom")
        if edit_custom:
            edit_custom.setEnabled(preset_lower in ('custom', 'dotted'))

        self.mark_config_dirty()

    def _on_trig_param_changed(self, config_key: str, trigger_id: str, param: str, val: float) -> None:
        if config_key not in self.config.data:
            self.config.data[config_key] = {}

        self.config.data[config_key][param] = str(val)

        # Update Canvas
        widgets = self._trigger_widgets.get(config_key, {})
        canvas: Optional[TriggerCurveCanvas] = widgets.get("canvas")
        if canvas:
            min_dz = float(widgets["min_dz"].value())
            max_dz = float(widgets["max_dz"].value())
            factor = float(widgets["factor"].value())
            is_dig = bool(widgets["digital"].isChecked())
            canvas.update_params(min_dz, 0.0, max_dz, "linear", factor, is_dig)

        self.mark_config_dirty()

    def _on_digital_trig_changed(self, config_key: str, trigger_id: str, checked: bool) -> None:
        # Update settings section
        if "settings" not in self.config.data:
            self.config.data["settings"] = {}
        self.config.data["settings"][f"digital_{trigger_id}"] = "true" if checked else "false"

        if config_key not in self.config.data:
            self.config.data[config_key] = {}
        self.config.data[config_key]["digital"] = "true" if checked else "false"

        # Update Canvas
        widgets = self._trigger_widgets.get(config_key, {})
        canvas: Optional[TriggerCurveCanvas] = widgets.get("canvas")
        if canvas:
            min_dz = float(widgets["min_dz"].value())
            max_dz = float(widgets["max_dz"].value())
            factor = float(widgets["factor"].value())
            canvas.update_params(min_dz, 0.0, max_dz, "linear", factor, checked)

        self.mark_config_dirty()

    # ------------------------------------------------------------------
    # Telemetry Updates
    # ------------------------------------------------------------------
    @Slot(dict)
    def update_telemetry(self, state_dict: dict) -> None:
        """
        Receives live telemetry dictionary (~500Hz) from UDPTelemetryWorker.
        Updates Stick Radars and Trigger Curve preview indicators.
        """
        if not isinstance(state_dict, dict):
            return

        lx = float(state_dict.get("lx", 0.0))
        ly = float(state_dict.get("ly", 0.0))
        rx = float(state_dict.get("rx", 0.0))
        ry = float(state_dict.get("ry", 0.0))

        lt = float(state_dict.get("lt", 0.0))
        rt = float(state_dict.get("rt", 0.0))

        # Left Stick Radar
        w_left = self._stick_widgets.get("analog_left", {})
        if "radar" in w_left and w_left["radar"]:
            w_left["radar"].update_telemetry(lx, ly)

        # Right Stick Radar
        w_right = self._stick_widgets.get("analog_right", {})
        if "radar" in w_right and w_right["radar"]:
            w_right["radar"].update_telemetry(rx, ry)

        # Left Trigger Canvas
        wt_left = self._trigger_widgets.get("trigger_left", {})
        if "canvas" in wt_left and wt_left["canvas"]:
            wt_left["canvas"].update_live_value(lt)

        # Right Trigger Canvas
        wt_right = self._trigger_widgets.get("trigger_right", {})
        if "canvas" in wt_right and wt_right["canvas"]:
            wt_right["canvas"].update_live_value(rt)

    # ------------------------------------------------------------------
    # Dialog Launchers
    # ------------------------------------------------------------------
    def open_circularity_modal(self, section_name: str) -> None:
        """Instantiates CircularityCalibrationModal for 'Stick_Left' or 'Stick_Right'."""
        modal = CircularityCalibrationModal(
            parent=self,
            section_name=section_name,
            config_manager=self.config
        )

        # Connect live UDP worker if present on window
        main_win = self.window()
        udp_worker = getattr(main_win, 'udp_worker', None)
        if udp_worker and hasattr(udp_worker, 'telemetry_received'):
            udp_worker.telemetry_received.connect(modal.update_telemetry)

        try:
            modal.exec()
        finally:
            if udp_worker and hasattr(udp_worker, 'telemetry_received'):
                try:
                    udp_worker.telemetry_received.disconnect(modal.update_telemetry)
                except Exception:
                    pass

    def open_latex_modal(self, config_key: str) -> None:
        """Instantiates LaTeX Export Modal for a given stick configuration."""
        cfg_data = getattr(self.config, 'data', {}).get(config_key, {})
        curve_type = str(cfg_data.get("curve", "linear"))
        power = float(cfg_data.get("exp_factor", 1.0))
        inner_dz = float(cfg_data.get("deadzone", 0.05))
        anti_dz = float(cfg_data.get("anti_deadzone", 0.0))
        rest_dz = float(cfg_data.get("rest_deadzone", 0.0))

        dlg = LatexExportModal(curve_type, power, inner_dz, anti_dz, rest_dz, parent=self)
        dlg.exec()

    def _open_info_modal(self) -> None:
        dlg = CircularityInfoModal(parent=self)
        dlg.exec()


if __name__ == "__main__":
    from config_manager import ControllerConfig

    app = QApplication(sys.argv)
    cfg = ControllerConfig()
    view = TuningView(cfg)
    view.setWindowTitle("TuningView Standalone Test")
    view.resize(1000, 700)
    view.show()
    sys.exit(app.exec())
