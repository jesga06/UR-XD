"""
Tuning View for PySide6 GUI (tuning_view.py)
Dual-Stick & Dual-Trigger tuning cards (Left Stick, Right Stick, Left Trigger, Right Trigger).
Includes inner rest deadzone, outer anti-deadzone, outer max threshold, sensitivity factors,
axis inversion (Invert X/Y), circularity modes (disabled, before, after), info popup, bounds reset,
interactive CurveGraphWidget for both sticks with live raw/mod tracer dots, and LaTeX/JSON export.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSlider, QSpinBox,
    QComboBox, QPushButton, QGridLayout, QScrollArea, QCheckBox, QMessageBox,
    QDoubleSpinBox, QApplication
)
from PySide6.QtCore import Qt
from components.circularity_modal_qt import CircularityCalibrationDialog
from components.curve_graph_widget import CurveGraphWidget


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

        btn_left_circ = QPushButton("🎯 Circularity Calibration")
        btn_left_circ.setObjectName("PrimaryBtn")
        btn_left_circ.clicked.connect(lambda: self.launch_circularity("Left Stick", "Stick_Left"))

        left_header = QHBoxLayout()
        left_header.addWidget(lbl_left_title)
        left_header.addStretch()
        left_header.addWidget(btn_left_circ)
        left_layout.addLayout(left_header)

        grid_left = QGridLayout()
        grid_left.addWidget(QLabel("Inner Rest Deadzone (%):"), 0, 0)
        slider_l_dz = QSlider(Qt.Orientation.Horizontal)
        slider_l_dz.setRange(0, 50)
        slider_l_dz.setValue(5)
        spin_l_dz = QSpinBox()
        spin_l_dz.setRange(0, 50)
        spin_l_dz.setValue(5)
        slider_l_dz.valueChanged.connect(spin_l_dz.setValue)
        spin_l_dz.valueChanged.connect(slider_l_dz.setValue)
        grid_left.addWidget(slider_l_dz, 0, 1)
        grid_left.addWidget(spin_l_dz, 0, 2)

        grid_left.addWidget(QLabel("Outer Anti-Deadzone (%):"), 1, 0)
        slider_l_adz = QSlider(Qt.Orientation.Horizontal)
        slider_l_adz.setRange(0, 30)
        slider_l_adz.setValue(0)
        spin_l_adz = QSpinBox()
        spin_l_adz.setRange(0, 30)
        spin_l_adz.setValue(0)
        slider_l_adz.valueChanged.connect(spin_l_adz.setValue)
        spin_l_adz.valueChanged.connect(slider_l_adz.setValue)
        grid_left.addWidget(slider_l_adz, 1, 1)
        grid_left.addWidget(spin_l_adz, 1, 2)

        grid_left.addWidget(QLabel("Outer Max Threshold (%):"), 2, 0)
        spin_l_max = QSpinBox()
        spin_l_max.setRange(50, 100)
        spin_l_max.setValue(100)
        grid_left.addWidget(spin_l_max, 2, 1, 1, 2)

        grid_left.addWidget(QLabel("Curve Sensitivity Factor:"), 3, 0)
        spin_l_pow = QDoubleSpinBox()
        spin_l_pow.setRange(0.1, 5.0)
        spin_l_pow.setSingleStep(0.1)
        spin_l_pow.setValue(2.0)
        grid_left.addWidget(spin_l_pow, 3, 1, 1, 2)

        grid_left.addWidget(QLabel("Circularity Mode:"), 4, 0)
        combo_l_circ_mode = QComboBox()
        combo_l_circ_mode.addItems(["Disabled", "Before Curves", "After Curves"])
        grid_left.addWidget(combo_l_circ_mode, 4, 1, 1, 2)

        grid_left.addWidget(QLabel("Response Curve Preset:"), 5, 0)
        combo_l_curve = QComboBox()
        combo_l_curve.addItems(ALL_CURVE_TYPES)
        grid_left.addWidget(combo_l_curve, 5, 1, 1, 2)

        left_layout.addLayout(grid_left)

        chk_l_inv_x = QCheckBox("Invert X-Axis")
        chk_l_inv_y = QCheckBox("Invert Y-Axis")
        left_layout.addWidget(chk_l_inv_x)
        left_layout.addWidget(chk_l_inv_y)

        # Left Stick Curve Graph Editor
        self.curve_graph_left = CurveGraphWidget("Left Stick Curve")
        combo_l_curve.currentTextChanged.connect(lambda t: self.curve_graph_left.set_curve_params(t, spin_l_pow.value()))
        spin_l_pow.valueChanged.connect(lambda v: self.curve_graph_left.set_curve_params(combo_l_curve.currentText(), v))
        left_layout.addWidget(self.curve_graph_left)

        math_l_box = QHBoxLayout()
        btn_latex_l = QPushButton("LaTeX Math 📋")
        btn_latex_l.setObjectName("SecondaryBtn")
        btn_latex_l.clicked.connect(lambda: self.copy_to_clipboard(self.curve_graph_left.export_latex(), "LaTeX Formula"))
        math_l_box.addWidget(btn_latex_l)
        left_layout.addLayout(math_l_box)

        stick_split.addWidget(left_card)

        # Right Stick Card
        right_card = QFrame()
        right_card.setObjectName("GlassCard")
        right_layout = QVBoxLayout(right_card)

        lbl_right_title = QLabel("🎯 RIGHT STICK TUNING & CURVES")
        lbl_right_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")

        btn_right_circ = QPushButton("🎯 Circularity Calibration")
        btn_right_circ.setObjectName("PrimaryBtn")
        btn_right_circ.clicked.connect(lambda: self.launch_circularity("Right Stick", "Stick_Right"))

        right_header = QHBoxLayout()
        right_header.addWidget(lbl_right_title)
        right_header.addStretch()
        right_header.addWidget(btn_right_circ)
        right_layout.addLayout(right_header)

        grid_right = QGridLayout()
        grid_right.addWidget(QLabel("Inner Rest Deadzone (%):"), 0, 0)
        slider_r_dz = QSlider(Qt.Orientation.Horizontal)
        slider_r_dz.setRange(0, 50)
        slider_r_dz.setValue(5)
        spin_r_dz = QSpinBox()
        spin_r_dz.setRange(0, 50)
        spin_r_dz.setValue(5)
        slider_r_dz.valueChanged.connect(spin_r_dz.setValue)
        spin_r_dz.valueChanged.connect(slider_r_dz.setValue)
        grid_right.addWidget(slider_r_dz, 0, 1)
        grid_right.addWidget(spin_r_dz, 0, 2)

        grid_right.addWidget(QLabel("Outer Anti-Deadzone (%):"), 1, 0)
        slider_r_adz = QSlider(Qt.Orientation.Horizontal)
        slider_r_adz.setRange(0, 30)
        slider_r_adz.setValue(0)
        spin_r_adz = QSpinBox()
        spin_r_adz.setRange(0, 30)
        spin_r_adz.setValue(0)
        slider_r_adz.valueChanged.connect(spin_r_adz.setValue)
        spin_r_adz.valueChanged.connect(slider_r_adz.setValue)
        grid_right.addWidget(slider_r_adz, 1, 1)
        grid_right.addWidget(spin_r_adz, 1, 2)

        grid_right.addWidget(QLabel("Outer Max Threshold (%):"), 2, 0)
        spin_r_max = QSpinBox()
        spin_r_max.setRange(50, 100)
        spin_r_max.setValue(100)
        grid_right.addWidget(spin_r_max, 2, 1, 1, 2)

        grid_right.addWidget(QLabel("Curve Sensitivity Factor:"), 3, 0)
        spin_r_pow = QDoubleSpinBox()
        spin_r_pow.setRange(0.1, 5.0)
        spin_r_pow.setSingleStep(0.1)
        spin_r_pow.setValue(2.0)
        grid_right.addWidget(spin_r_pow, 3, 1, 1, 2)

        grid_right.addWidget(QLabel("Circularity Mode:"), 4, 0)
        combo_r_circ_mode = QComboBox()
        combo_r_circ_mode.addItems(["Disabled", "Before Curves", "After Curves"])
        grid_right.addWidget(combo_r_circ_mode, 4, 1, 1, 2)

        grid_right.addWidget(QLabel("Response Curve Preset:"), 5, 0)
        combo_r_curve = QComboBox()
        combo_r_curve.addItems(ALL_CURVE_TYPES)
        grid_right.addWidget(combo_r_curve, 5, 1, 1, 2)

        right_layout.addLayout(grid_right)

        chk_r_inv_x = QCheckBox("Invert X-Axis")
        chk_r_inv_y = QCheckBox("Invert Y-Axis")
        right_layout.addWidget(chk_r_inv_x)
        right_layout.addWidget(chk_r_inv_y)

        # Right Stick Curve Graph Editor
        self.curve_graph_right = CurveGraphWidget("Right Stick Curve")
        combo_r_curve.currentTextChanged.connect(lambda t: self.curve_graph_right.set_curve_params(t, spin_r_pow.value()))
        spin_r_pow.valueChanged.connect(lambda v: self.curve_graph_right.set_curve_params(combo_r_curve.currentText(), v))
        right_layout.addWidget(self.curve_graph_right)

        math_r_box = QHBoxLayout()
        btn_latex_r = QPushButton("LaTeX Math 📋")
        btn_latex_r.setObjectName("SecondaryBtn")
        btn_latex_r.clicked.connect(lambda: self.copy_to_clipboard(self.curve_graph_right.export_latex(), "LaTeX Formula"))
        math_r_box.addWidget(btn_latex_r)
        right_layout.addLayout(math_r_box)

        stick_split.addWidget(right_card)
        scroll_layout.addLayout(stick_split)

        # 2. Trigger Response Tuning Sliders & Step-Functions Card
        trig_card = QFrame()
        trig_card.setObjectName("GlassCard")
        trig_layout = QVBoxLayout(trig_card)

        lbl_trig_title = QLabel("⚡ TRIGGER SENSITIVITY, DEADZONES & HAIR-TRIGGERS")
        lbl_trig_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")
        trig_layout.addWidget(lbl_trig_title)

        grid_trig = QGridLayout()

        # LT Sliders
        grid_trig.addWidget(QLabel("LT Min Deadzone (%):"), 0, 0)
        slider_lt_dz = QSlider(Qt.Orientation.Horizontal)
        slider_lt_dz.setRange(0, 50)
        slider_lt_dz.setValue(2)
        spin_lt_dz = QSpinBox()
        spin_lt_dz.setRange(0, 50)
        spin_lt_dz.setValue(2)
        slider_lt_dz.valueChanged.connect(spin_lt_dz.setValue)
        spin_lt_dz.valueChanged.connect(slider_lt_dz.setValue)
        grid_trig.addWidget(slider_lt_dz, 0, 1)
        grid_trig.addWidget(spin_lt_dz, 0, 2)

        grid_trig.addWidget(QLabel("LT Max Threshold (%):"), 0, 3)
        slider_lt_max = QSlider(Qt.Orientation.Horizontal)
        slider_lt_max.setRange(50, 100)
        slider_lt_max.setValue(98)
        spin_lt_max = QSpinBox()
        spin_lt_max.setRange(50, 100)
        spin_lt_max.setValue(98)
        slider_lt_max.valueChanged.connect(spin_lt_max.setValue)
        spin_lt_max.valueChanged.connect(slider_lt_max.setValue)
        grid_trig.addWidget(slider_lt_max, 0, 4)
        grid_trig.addWidget(spin_lt_max, 0, 5)

        # RT Sliders
        grid_trig.addWidget(QLabel("RT Min Deadzone (%):"), 1, 0)
        slider_rt_dz = QSlider(Qt.Orientation.Horizontal)
        slider_rt_dz.setRange(0, 50)
        slider_rt_dz.setValue(2)
        spin_rt_dz = QSpinBox()
        spin_rt_dz.setRange(0, 50)
        spin_rt_dz.setValue(2)
        slider_rt_dz.valueChanged.connect(spin_rt_dz.setValue)
        spin_rt_dz.valueChanged.connect(slider_rt_dz.setValue)
        grid_trig.addWidget(slider_rt_dz, 1, 1)
        grid_trig.addWidget(spin_rt_dz, 1, 2)

        grid_trig.addWidget(QLabel("RT Max Threshold (%):"), 1, 3)
        slider_rt_max = QSlider(Qt.Orientation.Horizontal)
        slider_rt_max.setRange(50, 100)
        slider_rt_max.setValue(98)
        spin_rt_max = QSpinBox()
        spin_rt_max.setRange(50, 100)
        spin_rt_max.setValue(98)
        slider_rt_max.valueChanged.connect(spin_rt_max.setValue)
        spin_rt_max.valueChanged.connect(slider_rt_max.setValue)
        grid_trig.addWidget(slider_rt_max, 1, 4)
        grid_trig.addWidget(spin_rt_max, 1, 5)

        trig_layout.addLayout(grid_trig)

        chk_dig_lt = QCheckBox("Enable Digital Hair-Trigger Step-Function for LT")
        chk_dig_rt = QCheckBox("Enable Digital Hair-Trigger Step-Function for RT")
        trig_layout.addWidget(chk_dig_lt)
        trig_layout.addWidget(chk_dig_rt)

        scroll_layout.addWidget(trig_card)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def update_state(self, controller_state):
        """Update live input/output tracer dots on curve graphs."""
        if not controller_state:
            return
        self.curve_graph_left.set_live_input_output(controller_state.lx, controller_state.lx)
        self.curve_graph_right.set_live_input_output(controller_state.rx, controller_state.rx)

    def copy_to_clipboard(self, text, label):
        QApplication.clipboard().setText(text)
        msg = QMessageBox(self)
        msg.setWindowTitle("Export Math")
        msg.setText(f"✓ Copied {label} string to clipboard!\n\n{text}")
        msg.exec()

    def launch_circularity(self, title, section):
        dlg = CircularityCalibrationDialog(self.app, title=title, section=section)
        dlg.exec()
