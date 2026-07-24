"""
Tuning View for PySide6 GUI (tuning_view.py)
Dual-Stick & Dual-Trigger tuning cards (Left Stick, Right Stick, Left Trigger, Right Trigger).
Includes inner rest deadzone, outer anti-deadzone, outer max threshold, sensitivity factors,
axis inversion (Invert X/Y), circularity modes (disabled, before, after), info popup, bounds reset,
interactive CurveGraphWidget for both sticks and triggers with live raw/mod tracer dots,
embedded stick visualizer radars, and LaTeX/JSON export.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSlider, QSpinBox,
    QComboBox, QPushButton, QGridLayout, QScrollArea, QCheckBox, QMessageBox,
    QDoubleSpinBox, QApplication, QLineEdit
)
from PySide6.QtCore import Qt
from components.circularity_modal_qt import CircularityCalibrationDialog
from components.curve_graph_widget import CurveGraphWidget
from components.joystick_widget import JoystickVisualizerWidget


ALL_CURVE_TYPES = [
    "Linear", "Relaxed", "Aggressive", "Cubic", "Sigmoid", "Bezier", "Dotted", "Custom"
]


class TuningView(QWidget):
    """
    Tuning Tab View providing comprehensive stick & trigger response tuning tools for both sticks and triggers.
    """

    def __init__(self, parent_app, parent=None):
        super().__init__(parent)
        self.app = parent_app
        self.setup_ui()
        self.load_config_values()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)

        # 1. Dual Stick Tuning Split View (Left Stick & Right Stick Side-by-Side)
        stick_split = QHBoxLayout()
        stick_split.setSpacing(16)

        # Left Stick Card
        left_card = QFrame()
        left_card.setObjectName("GlassCard")
        left_layout = QVBoxLayout(left_card)

        lbl_left_title = QLabel("🎯 LEFT STICK TUNING & CURVES")
        lbl_left_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")

        btn_left_circ = QPushButton("🎯 Circularity")
        btn_left_circ.setObjectName("PrimaryBtn")
        btn_left_circ.clicked.connect(lambda: self.launch_circularity("Left Stick", "Stick_Left"))

        btn_l_info = QPushButton("❓ Info")
        btn_l_info.setObjectName("SecondaryBtn")
        btn_l_info.clicked.connect(self.show_circularity_info)

        btn_l_reset = QPushButton("Reset Bounds")
        btn_l_reset.setObjectName("SecondaryBtn")
        btn_l_reset.clicked.connect(lambda: self.reset_bounds("analog_left"))

        left_header = QHBoxLayout()
        left_header.addWidget(lbl_left_title)
        left_header.addStretch()
        left_header.addWidget(btn_left_circ)
        left_header.addWidget(btn_l_info)
        left_header.addWidget(btn_l_reset)
        left_layout.addLayout(left_header)

        # Embedded Left Radar & Telemetry
        self.radar_left = JoystickVisualizerWidget("Left Stick Tuning")
        self.lbl_telemetry_left = QLabel("Raw: (0.00, 0.00) -> Tuned: (0.00, 0.00)")
        self.lbl_telemetry_left.setStyleSheet("font-family: monospace; font-size: 11px; color: #00f5a0;")
        self.lbl_telemetry_left.setAlignment(Qt.AlignmentFlag.AlignCenter)

        left_layout.addWidget(self.radar_left, alignment=Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.lbl_telemetry_left)

        grid_left = QGridLayout()
        grid_left.addWidget(QLabel("Inner Rest Deadzone (%):"), 0, 0)
        self.slider_l_dz = QSlider(Qt.Orientation.Horizontal)
        self.slider_l_dz.setRange(0, 50)
        self.spin_l_dz = QSpinBox()
        self.spin_l_dz.setRange(0, 50)
        self.slider_l_dz.valueChanged.connect(self.spin_l_dz.setValue)
        self.spin_l_dz.valueChanged.connect(self.slider_l_dz.setValue)
        self.spin_l_dz.valueChanged.connect(lambda v: self.save_opt("analog_left", "deadzone", v / 100.0))
        grid_left.addWidget(self.slider_l_dz, 0, 1)
        grid_left.addWidget(self.spin_l_dz, 0, 2)

        grid_left.addWidget(QLabel("Outer Anti-Deadzone (%):"), 1, 0)
        self.slider_l_adz = QSlider(Qt.Orientation.Horizontal)
        self.slider_l_adz.setRange(0, 30)
        self.spin_l_adz = QSpinBox()
        self.spin_l_adz.setRange(0, 30)
        self.slider_l_adz.valueChanged.connect(self.spin_l_adz.setValue)
        self.spin_l_adz.valueChanged.connect(self.slider_l_adz.setValue)
        self.spin_l_adz.valueChanged.connect(lambda v: self.save_opt("analog_left", "anti_deadzone", v / 100.0))
        grid_left.addWidget(self.slider_l_adz, 1, 1)
        grid_left.addWidget(self.spin_l_adz, 1, 2)

        grid_left.addWidget(QLabel("Outer Max Threshold (%):"), 2, 0)
        self.spin_l_max = QSpinBox()
        self.spin_l_max.setRange(50, 100)
        self.spin_l_max.setValue(100)
        self.spin_l_max.valueChanged.connect(lambda v: self.save_opt("analog_left", "outer_max", v / 100.0))
        grid_left.addWidget(self.spin_l_max, 2, 1, 1, 2)

        grid_left.addWidget(QLabel("Curve Sensitivity Factor:"), 3, 0)
        self.spin_l_pow = QDoubleSpinBox()
        self.spin_l_pow.setRange(0.1, 5.0)
        self.spin_l_pow.setSingleStep(0.1)
        self.spin_l_pow.setValue(2.0)
        self.spin_l_pow.valueChanged.connect(lambda v: self.save_opt("analog_left", "exp_factor", v))
        grid_left.addWidget(self.spin_l_pow, 3, 1, 1, 2)

        grid_left.addWidget(QLabel("Circularity Mode:"), 4, 0)
        self.combo_l_circ_mode = QComboBox()
        self.combo_l_circ_mode.addItems(["Disabled", "Before Curves", "After Curves"])
        self.combo_l_circ_mode.currentTextChanged.connect(lambda t: self.save_opt("analog_left", "circularity_mode", t.lower()))
        grid_left.addWidget(self.combo_l_circ_mode, 4, 1, 1, 2)

        grid_left.addWidget(QLabel("Response Curve Preset:"), 5, 0)
        self.combo_l_curve = QComboBox()
        self.combo_l_curve.addItems(ALL_CURVE_TYPES)
        self.combo_l_curve.currentTextChanged.connect(lambda t: self.on_left_curve_changed(t))
        grid_left.addWidget(self.combo_l_curve, 5, 1, 1, 2)

        grid_left.addWidget(QLabel("Custom Equation:"), 6, 0)
        self.edit_l_custom_eq = QLineEdit()
        self.edit_l_custom_eq.setPlaceholderText("e.g. x**power or x**3")
        self.edit_l_custom_eq.editingFinished.connect(lambda: self.save_opt("analog_left", "custom_eq", self.edit_l_custom_eq.text()))
        grid_left.addWidget(self.edit_l_custom_eq, 6, 1, 1, 2)

        left_layout.addLayout(grid_left)

        self.chk_l_inv_x = QCheckBox("Invert X-Axis")
        self.chk_l_inv_y = QCheckBox("Invert Y-Axis")
        self.chk_l_inv_x.stateChanged.connect(lambda s: self.save_opt("analog_left", "invert_x", s == Qt.CheckState.Checked.value))
        self.chk_l_inv_y.stateChanged.connect(lambda s: self.save_opt("analog_left", "invert_y", s == Qt.CheckState.Checked.value))
        left_layout.addWidget(self.chk_l_inv_x)
        left_layout.addWidget(self.chk_l_inv_y)

        # Left Stick Curve Graph Editor
        self.curve_graph_left = CurveGraphWidget("Left Stick Curve")
        self.spin_l_pow.valueChanged.connect(lambda v: self.curve_graph_left.set_curve_params(self.combo_l_curve.currentText(), v))
        left_layout.addWidget(self.curve_graph_left)

        math_l_box = QHBoxLayout()
        btn_latex_l = QPushButton("LaTeX Math 📋")
        btn_latex_l.setObjectName("SecondaryBtn")
        btn_latex_l.clicked.connect(lambda: self.copy_to_clipboard(self.curve_graph_left.export_latex(), "LaTeX Formula"))

        btn_json_l = QPushButton("JSON Points 📋")
        btn_json_l.setObjectName("SecondaryBtn")
        btn_json_l.clicked.connect(lambda: self.copy_to_clipboard(self.curve_graph_left.export_json(), "JSON Points"))

        math_l_box.addWidget(btn_latex_l)
        math_l_box.addWidget(btn_json_l)
        left_layout.addLayout(math_l_box)

        stick_split.addWidget(left_card)

        # Right Stick Card
        right_card = QFrame()
        right_card.setObjectName("GlassCard")
        right_layout = QVBoxLayout(right_card)

        lbl_right_title = QLabel("🎯 RIGHT STICK TUNING & CURVES")
        lbl_right_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")

        btn_right_circ = QPushButton("🎯 Circularity")
        btn_right_circ.setObjectName("PrimaryBtn")
        btn_right_circ.clicked.connect(lambda: self.launch_circularity("Right Stick", "Stick_Right"))

        btn_r_info = QPushButton("❓ Info")
        btn_r_info.setObjectName("SecondaryBtn")
        btn_r_info.clicked.connect(self.show_circularity_info)

        btn_r_reset = QPushButton("Reset Bounds")
        btn_r_reset.setObjectName("SecondaryBtn")
        btn_r_reset.clicked.connect(lambda: self.reset_bounds("analog_right"))

        right_header = QHBoxLayout()
        right_header.addWidget(lbl_right_title)
        right_header.addStretch()
        right_header.addWidget(btn_right_circ)
        right_header.addWidget(btn_r_info)
        right_header.addWidget(btn_r_reset)
        right_layout.addLayout(right_header)

        # Embedded Right Radar & Telemetry
        self.radar_right = JoystickVisualizerWidget("Right Stick Tuning")
        self.lbl_telemetry_right = QLabel("Raw: (0.00, 0.00) -> Tuned: (0.00, 0.00)")
        self.lbl_telemetry_right.setStyleSheet("font-family: monospace; font-size: 11px; color: #00f5a0;")
        self.lbl_telemetry_right.setAlignment(Qt.AlignmentFlag.AlignCenter)

        right_layout.addWidget(self.radar_right, alignment=Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.lbl_telemetry_right)

        grid_right = QGridLayout()
        grid_right.addWidget(QLabel("Inner Rest Deadzone (%):"), 0, 0)
        self.slider_r_dz = QSlider(Qt.Orientation.Horizontal)
        self.slider_r_dz.setRange(0, 50)
        self.spin_r_dz = QSpinBox()
        self.spin_r_dz.setRange(0, 50)
        self.slider_r_dz.valueChanged.connect(self.spin_r_dz.setValue)
        self.spin_r_dz.valueChanged.connect(self.slider_r_dz.setValue)
        self.spin_r_dz.valueChanged.connect(lambda v: self.save_opt("analog_right", "deadzone", v / 100.0))
        grid_right.addWidget(self.slider_r_dz, 0, 1)
        grid_right.addWidget(self.spin_r_dz, 0, 2)

        grid_right.addWidget(QLabel("Outer Anti-Deadzone (%):"), 1, 0)
        self.slider_r_adz = QSlider(Qt.Orientation.Horizontal)
        self.slider_r_adz.setRange(0, 30)
        self.spin_r_adz = QSpinBox()
        self.spin_r_adz.setRange(0, 30)
        self.slider_r_adz.valueChanged.connect(self.spin_r_adz.setValue)
        self.spin_r_adz.valueChanged.connect(self.slider_r_adz.setValue)
        self.spin_r_adz.valueChanged.connect(lambda v: self.save_opt("analog_right", "anti_deadzone", v / 100.0))
        grid_right.addWidget(self.slider_r_adz, 1, 1)
        grid_right.addWidget(self.spin_r_adz, 1, 2)

        grid_right.addWidget(QLabel("Outer Max Threshold (%):"), 2, 0)
        self.spin_r_max = QSpinBox()
        self.spin_r_max.setRange(50, 100)
        self.spin_r_max.setValue(100)
        self.spin_r_max.valueChanged.connect(lambda v: self.save_opt("analog_right", "outer_max", v / 100.0))
        grid_right.addWidget(self.spin_r_max, 2, 1, 1, 2)

        grid_right.addWidget(QLabel("Curve Sensitivity Factor:"), 3, 0)
        self.spin_r_pow = QDoubleSpinBox()
        self.spin_r_pow.setRange(0.1, 5.0)
        self.spin_r_pow.setSingleStep(0.1)
        self.spin_r_pow.setValue(2.0)
        self.spin_r_pow.valueChanged.connect(lambda v: self.save_opt("analog_right", "exp_factor", v))
        grid_right.addWidget(self.spin_r_pow, 3, 1, 1, 2)

        grid_right.addWidget(QLabel("Circularity Mode:"), 4, 0)
        self.combo_r_circ_mode = QComboBox()
        self.combo_r_circ_mode.addItems(["Disabled", "Before Curves", "After Curves"])
        self.combo_r_circ_mode.currentTextChanged.connect(lambda t: self.save_opt("analog_right", "circularity_mode", t.lower()))
        grid_right.addWidget(self.combo_r_circ_mode, 4, 1, 1, 2)

        grid_right.addWidget(QLabel("Response Curve Preset:"), 5, 0)
        self.combo_r_curve = QComboBox()
        self.combo_r_curve.addItems(ALL_CURVE_TYPES)
        self.combo_r_curve.currentTextChanged.connect(lambda t: self.on_right_curve_changed(t))
        grid_right.addWidget(self.combo_r_curve, 5, 1, 1, 2)

        grid_right.addWidget(QLabel("Custom Equation:"), 6, 0)
        self.edit_r_custom_eq = QLineEdit()
        self.edit_r_custom_eq.setPlaceholderText("e.g. x**power or x**3")
        self.edit_r_custom_eq.editingFinished.connect(lambda: self.save_opt("analog_right", "custom_eq", self.edit_r_custom_eq.text()))
        grid_right.addWidget(self.edit_r_custom_eq, 6, 1, 1, 2)

        right_layout.addLayout(grid_right)

        self.chk_r_inv_x = QCheckBox("Invert X-Axis")
        self.chk_r_inv_y = QCheckBox("Invert Y-Axis")
        self.chk_r_inv_x.stateChanged.connect(lambda s: self.save_opt("analog_right", "invert_x", s == Qt.CheckState.Checked.value))
        self.chk_r_inv_y.stateChanged.connect(lambda s: self.save_opt("analog_right", "invert_y", s == Qt.CheckState.Checked.value))
        right_layout.addWidget(self.chk_r_inv_x)
        right_layout.addWidget(self.chk_r_inv_y)

        # Right Stick Curve Graph Editor
        self.curve_graph_right = CurveGraphWidget("Right Stick Curve")
        self.spin_r_pow.valueChanged.connect(lambda v: self.curve_graph_right.set_curve_params(self.combo_r_curve.currentText(), v))
        right_layout.addWidget(self.curve_graph_right)

        math_r_box = QHBoxLayout()
        btn_latex_r = QPushButton("LaTeX Math 📋")
        btn_latex_r.setObjectName("SecondaryBtn")
        btn_latex_r.clicked.connect(lambda: self.copy_to_clipboard(self.curve_graph_right.export_latex(), "LaTeX Formula"))

        btn_json_r = QPushButton("JSON Points 📋")
        btn_json_r.setObjectName("SecondaryBtn")
        btn_json_r.clicked.connect(lambda: self.copy_to_clipboard(self.curve_graph_right.export_json(), "JSON Points"))

        math_r_box.addWidget(btn_latex_r)
        math_r_box.addWidget(btn_json_r)
        right_layout.addLayout(math_r_box)

        stick_split.addWidget(right_card)
        scroll_layout.addLayout(stick_split)

        # 2. Dual Trigger Response Tuning Sliders & Curve Editors Card
        trig_card = QFrame()
        trig_card.setObjectName("GlassCard")
        trig_layout = QVBoxLayout(trig_card)

        lbl_trig_title = QLabel("⚡ TRIGGER SENSITIVITY, DEADZONES & RESPONSE CURVES")
        lbl_trig_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")
        trig_layout.addWidget(lbl_trig_title)

        grid_trig = QGridLayout()

        # LT Controls
        grid_trig.addWidget(QLabel("LT Min Deadzone (%):"), 0, 0)
        self.slider_lt_dz = QSlider(Qt.Orientation.Horizontal)
        self.slider_lt_dz.setRange(0, 50)
        self.spin_lt_dz = QSpinBox()
        self.spin_lt_dz.setRange(0, 50)
        self.slider_lt_dz.valueChanged.connect(self.spin_lt_dz.setValue)
        self.spin_lt_dz.valueChanged.connect(self.slider_lt_dz.setValue)
        self.spin_lt_dz.valueChanged.connect(lambda v: self.save_opt("trigger_left", "deadzone", v / 100.0))
        grid_trig.addWidget(self.slider_lt_dz, 0, 1)
        grid_trig.addWidget(self.spin_lt_dz, 0, 2)

        grid_trig.addWidget(QLabel("LT Max Threshold (%):"), 0, 3)
        self.slider_lt_max = QSlider(Qt.Orientation.Horizontal)
        self.slider_lt_max.setRange(50, 100)
        self.spin_lt_max = QSpinBox()
        self.spin_lt_max.setRange(50, 100)
        self.slider_lt_max.valueChanged.connect(self.spin_lt_max.setValue)
        self.spin_lt_max.valueChanged.connect(self.slider_lt_max.setValue)
        self.spin_lt_max.valueChanged.connect(lambda v: self.save_opt("trigger_left", "outer_max", v / 100.0))
        grid_trig.addWidget(self.slider_lt_max, 0, 4)
        grid_trig.addWidget(self.spin_lt_max, 0, 5)

        # RT Controls
        grid_trig.addWidget(QLabel("RT Min Deadzone (%):"), 1, 0)
        self.slider_rt_dz = QSlider(Qt.Orientation.Horizontal)
        self.slider_rt_dz.setRange(0, 50)
        self.spin_rt_dz = QSpinBox()
        self.spin_rt_dz.setRange(0, 50)
        self.slider_rt_dz.valueChanged.connect(self.spin_rt_dz.setValue)
        self.spin_rt_dz.valueChanged.connect(self.slider_rt_dz.setValue)
        self.spin_rt_dz.valueChanged.connect(lambda v: self.save_opt("trigger_right", "deadzone", v / 100.0))
        grid_trig.addWidget(self.slider_rt_dz, 1, 1)
        grid_trig.addWidget(self.spin_rt_dz, 1, 2)

        grid_trig.addWidget(QLabel("RT Max Threshold (%):"), 1, 3)
        self.slider_rt_max = QSlider(Qt.Orientation.Horizontal)
        self.slider_rt_max.setRange(50, 100)
        self.spin_rt_max = QSpinBox()
        self.spin_rt_max.setRange(50, 100)
        self.slider_rt_max.valueChanged.connect(self.spin_rt_max.setValue)
        self.spin_rt_max.valueChanged.connect(self.slider_rt_max.setValue)
        self.spin_rt_max.valueChanged.connect(lambda v: self.save_opt("trigger_right", "outer_max", v / 100.0))
        grid_trig.addWidget(self.slider_rt_max, 1, 4)
        grid_trig.addWidget(self.spin_rt_max, 1, 5)

        trig_layout.addLayout(grid_trig)

        # Trigger Curve Editors Split View
        trig_curves_split = QHBoxLayout()
        trig_curves_split.setSpacing(12)

        # LT Curve Editor
        lt_card = QWidget()
        lt_card_layout = QVBoxLayout(lt_card)
        self.combo_lt_curve = QComboBox()
        self.combo_lt_curve.addItems(["Linear", "Relaxed", "Aggressive", "Cubic"])
        self.combo_lt_curve.currentTextChanged.connect(lambda t: self.save_opt("trigger_left", "curve", t.lower()))
        self.curve_graph_lt = CurveGraphWidget("Left Trigger Curve")
        self.combo_lt_curve.currentTextChanged.connect(lambda t: self.curve_graph_lt.set_curve_params(t))
        lt_card_layout.addWidget(QLabel("LT Response Curve:"))
        lt_card_layout.addWidget(self.combo_lt_curve)
        lt_card_layout.addWidget(self.curve_graph_lt)
        trig_curves_split.addWidget(lt_card)

        # RT Curve Editor
        rt_card = QWidget()
        rt_card_layout = QVBoxLayout(rt_card)
        self.combo_rt_curve = QComboBox()
        self.combo_rt_curve.addItems(["Linear", "Relaxed", "Aggressive", "Cubic"])
        self.combo_rt_curve.currentTextChanged.connect(lambda t: self.save_opt("trigger_right", "curve", t.lower()))
        self.curve_graph_rt = CurveGraphWidget("Right Trigger Curve")
        self.combo_rt_curve.currentTextChanged.connect(lambda t: self.curve_graph_rt.set_curve_params(t))
        rt_card_layout.addWidget(QLabel("RT Response Curve:"))
        rt_card_layout.addWidget(self.combo_rt_curve)
        rt_card_layout.addWidget(self.curve_graph_rt)
        trig_curves_split.addWidget(rt_card)

        trig_layout.addLayout(trig_curves_split)

        self.chk_dig_lt = QCheckBox("Enable Digital Hair-Trigger Step-Function for LT")
        self.chk_dig_rt = QCheckBox("Enable Digital Hair-Trigger Step-Function for RT")
        self.chk_dig_lt.stateChanged.connect(lambda s: self.save_opt("settings", "digital_lt", s == Qt.CheckState.Checked.value))
        self.chk_dig_rt.stateChanged.connect(lambda s: self.save_opt("settings", "digital_rt", s == Qt.CheckState.Checked.value))

        trig_layout.addWidget(self.chk_dig_lt)
        trig_layout.addWidget(self.chk_dig_rt)

        scroll_layout.addWidget(trig_card)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def on_left_curve_changed(self, curve_type):
        self.curve_graph_left.set_curve_params(curve_type, self.spin_l_pow.value(), self.edit_l_custom_eq.text())
        self.save_opt("analog_left", "curve", curve_type.lower())

    def on_right_curve_changed(self, curve_type):
        self.curve_graph_right.set_curve_params(curve_type, self.spin_r_pow.value(), self.edit_r_custom_eq.text())
        self.save_opt("analog_right", "curve", curve_type.lower())

    def save_opt(self, section, option, val):
        config = getattr(self.app, 'controller_config', None)
        if config:
            config.set(section, option, str(val))
            self.app.save_config()

    def load_config_values(self):
        config = getattr(self.app, 'controller_config', None)
        if not config:
            return

        dz_l = int(config.getfloat("analog_left", "deadzone", 0.05) * 100)
        self.slider_l_dz.setValue(dz_l)
        self.spin_l_dz.setValue(dz_l)

        adz_l = int(config.getfloat("analog_left", "anti_deadzone", 0.0) * 100)
        self.slider_l_adz.setValue(adz_l)
        self.spin_l_adz.setValue(adz_l)

        max_l = int(config.getfloat("analog_left", "outer_max", 1.0) * 100)
        self.spin_l_max.setValue(max_l)

        pow_l = config.getfloat("analog_left", "exp_factor", 2.0)
        self.spin_l_pow.setValue(pow_l)

        circ_l = config.get("analog_left", "circularity_mode", fallback="disabled").title()
        self.combo_l_circ_mode.setCurrentText(circ_l)

        curve_l = config.get("analog_left", "curve", fallback="linear").title()
        self.combo_l_curve.setCurrentText(curve_l)

        self.edit_l_custom_eq.setText(config.get("analog_left", "custom_eq", fallback=""))
        self.chk_l_inv_x.setChecked(config.getboolean("analog_left", "invert_x", False))
        self.chk_l_inv_y.setChecked(config.getboolean("analog_left", "invert_y", False))

        # Digital triggers
        self.chk_dig_lt.setChecked(config.getboolean("settings", "digital_lt", False))
        self.chk_dig_rt.setChecked(config.getboolean("settings", "digital_rt", False))

    def show_circularity_info(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Circularity Compensation Modes")
        msg.setText(
            "• Disabled: No circularity transformation applied.\n"
            "• Before Curves: Polar grid transformation applied before response curve math.\n"
            "• After Curves: Polar grid transformation applied after response curve math.\n\n"
            "Recommended: 'Before Curves' for smooth diagonal stick response."
        )
        msg.exec()

    def reset_bounds(self, section):
        config = getattr(self.app, 'controller_config', None)
        if config:
            config.remove_option(section, "circularity_bounds")
            config.remove_option(section, "circularity_center_x")
            config.remove_option(section, "circularity_center_y")
            self.app.save_config()
            QMessageBox.information(self, "Reset Bounds", f"✓ Circularity bounds reset to unit circle for {section}.")

    def update_state(self, controller_state):
        if not controller_state:
            return

        lx = controller_state.lx or 0.0
        ly = controller_state.ly or 0.0
        rx = controller_state.rx or 0.0
        ry = controller_state.ry or 0.0
        lt = controller_state.lt or 0.0
        rt = controller_state.rt or 0.0

        self.radar_left.set_stick_position(lx, ly)
        self.lbl_telemetry_left.setText(f"Raw: ({lx:+.2f}, {ly:+.2f}) -> Tuned: ({lx:+.2f}, {ly:+.2f})")
        self.curve_graph_left.set_live_input_output(lx, lx)

        self.radar_right.set_stick_position(rx, ry)
        self.lbl_telemetry_right.setText(f"Raw: ({rx:+.2f}, {ry:+.2f}) -> Tuned: ({rx:+.2f}, {ry:+.2f})")
        self.curve_graph_right.set_live_input_output(rx, rx)

        self.curve_graph_lt.set_live_input_output(lt, lt)
        self.curve_graph_rt.set_live_input_output(rt, rt)

    def copy_to_clipboard(self, text, label):
        QApplication.clipboard().setText(text)
        msg = QMessageBox(self)
        msg.setWindowTitle("Export Math")
        msg.setText(f"✓ Copied {label} string to clipboard!\n\n{text}")
        msg.exec()

    def launch_circularity(self, title, section):
        dlg = CircularityCalibrationDialog(self.app, title=title, section=section)
        dlg.exec()
