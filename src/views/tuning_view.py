"""
Tuning View for PySide6 GUI (tuning_view.py)
Fully-featured stick and trigger response tuning tab matching legacy Screenshots 2 & 3.
Side-by-side cards for Left/Right Stick and Left/Right Trigger.
Includes Response Curve graphs, Current Position radars with white circularity bounds ring,
dual vertical Trigger Pull bars (Raw vs Tuned), 6 sliders per stick/trigger (Deadzone, Anti-Deadzone,
Rest Deadzone, Warp Threshold/Power, Sensitivity), 7 curve types (linear, exponential, aggressive, custom,
dotted custom, sigmoid, bezier), Reset buttons, Export Math buttons, and Digital Trigger Mode toggles.
Ensures 100% symmetrical configuration restoration and signal handling for both sticks and both triggers.
"""

import sys
import os
import math

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
from components.trigger_bar_widget import TriggerPullWidget
import math_utils
import curves


ALL_CURVE_TYPES = [
    "linear", "exponential", "aggressive", "custom", "dotted custom", "sigmoid", "bezier"
]

TRIGGER_CURVE_TYPES = [
    "linear", "exponential", "aggressive", "custom", "sigmoid", "bezier"
]


class TuningView(QWidget):
    """
    Tuning Tab View implementing 100% feature parity and symmetry across all 4 analog inputs.
    """

    def __init__(self, parent_app, parent=None):
        super().__init__(parent)
        self.app = parent_app
        self.setup_ui()
        self.load_config_values()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)

        # ---------------------------------------------------------------------
        # SECTION 1: DUAL STICK TUNING (Left Stick & Right Stick Side-by-Side)
        # ---------------------------------------------------------------------
        stick_split = QHBoxLayout()
        stick_split.setSpacing(14)

        # Left Stick Card
        left_card = QFrame()
        left_card.setObjectName("GlassCard")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(12, 10, 12, 10)

        lbl_l_title = QLabel("Left Stick")
        lbl_l_title.setStyleSheet("font-weight: bold; font-size: 15px;")
        lbl_l_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(lbl_l_title)

        # Visualizers Row: Response Curve & Current Position
        vis_l_box = QHBoxLayout()
        self.curve_graph_left = CurveGraphWidget("Left Stick Curve")
        self.radar_left = JoystickVisualizerWidget("Left Stick Position")

        vis_l_box.addWidget(self.curve_graph_left)
        vis_l_box.addWidget(self.radar_left)
        left_layout.addLayout(vis_l_box)

        # Sliders Grid (Matching Screenshot 2)
        grid_l = QGridLayout()
        grid_l.setSpacing(6)

        # 1. Deadzone
        grid_l.addWidget(QLabel("?  Deadzone"), 0, 0)
        self.slider_l_dz = QSlider(Qt.Orientation.Horizontal)
        self.slider_l_dz.setRange(0, 50)
        self.lbl_val_l_dz = QLabel("0.00")
        self.lbl_val_l_dz.setFixedWidth(40)
        self.slider_l_dz.valueChanged.connect(self.on_l_dz_changed)
        grid_l.addWidget(self.slider_l_dz, 0, 1)
        grid_l.addWidget(self.lbl_val_l_dz, 0, 2)

        # 2. Anti-Deadzone
        grid_l.addWidget(QLabel("?  Anti-Deadzone"), 1, 0)
        self.slider_l_adz = QSlider(Qt.Orientation.Horizontal)
        self.slider_l_adz.setRange(0, 30)
        self.lbl_val_l_adz = QLabel("0.00")
        self.lbl_val_l_adz.setFixedWidth(40)
        self.slider_l_adz.valueChanged.connect(self.on_l_adz_changed)
        grid_l.addWidget(self.slider_l_adz, 1, 1)
        grid_l.addWidget(self.lbl_val_l_adz, 1, 2)

        # 3. Rest Deadzone
        grid_l.addWidget(QLabel("?  Rest Deadzone"), 2, 0)
        self.slider_l_rdz = QSlider(Qt.Orientation.Horizontal)
        self.slider_l_rdz.setRange(0, 30)
        self.lbl_val_l_rdz = QLabel("0.00")
        self.lbl_val_l_rdz.setFixedWidth(40)
        self.slider_l_rdz.valueChanged.connect(self.on_l_rdz_changed)
        grid_l.addWidget(self.slider_l_rdz, 2, 1)
        grid_l.addWidget(self.lbl_val_l_rdz, 2, 2)

        # 4. Warp Threshold (Outer Max)
        grid_l.addWidget(QLabel("?  Warp Threshold"), 3, 0)
        self.slider_l_warp = QSlider(Qt.Orientation.Horizontal)
        self.slider_l_warp.setRange(50, 100)
        self.slider_l_warp.setValue(100)
        self.lbl_val_l_warp = QLabel("1.00")
        self.lbl_val_l_warp.setFixedWidth(40)
        self.slider_l_warp.valueChanged.connect(self.on_l_warp_changed)
        grid_l.addWidget(self.slider_l_warp, 3, 1)
        grid_l.addWidget(self.lbl_val_l_warp, 3, 2)

        # 5. Curve Factor (Exponent)
        grid_l.addWidget(QLabel("?  Curve Factor"), 4, 0)
        self.slider_l_cf = QSlider(Qt.Orientation.Horizontal)
        self.slider_l_cf.setRange(10, 50)  # 1.00 to 5.00
        self.slider_l_cf.setValue(10)
        self.lbl_val_l_cf = QLabel("1.00")
        self.lbl_val_l_cf.setFixedWidth(40)
        self.slider_l_cf.valueChanged.connect(self.on_l_cf_changed)
        grid_l.addWidget(self.slider_l_cf, 4, 1)
        grid_l.addWidget(self.lbl_val_l_cf, 4, 2)

        # 6. Sensitivity
        grid_l.addWidget(QLabel("?  Sensitivity"), 5, 0)
        self.slider_l_sens = QSlider(Qt.Orientation.Horizontal)
        self.slider_l_sens.setRange(5, 20)  # 0.50 to 2.00
        self.slider_l_sens.setValue(10)
        self.lbl_val_l_sens = QLabel("1.00")
        self.lbl_val_l_sens.setFixedWidth(40)
        self.slider_l_sens.valueChanged.connect(self.on_l_sens_changed)
        grid_l.addWidget(self.slider_l_sens, 5, 1)
        grid_l.addWidget(self.lbl_val_l_sens, 5, 2)

        left_layout.addLayout(grid_l)

        # Curve Type & Export Row
        ctype_l_box = QHBoxLayout()
        ctype_l_box.addWidget(QLabel("?  Curve Type:"))
        self.combo_l_ctype = QComboBox()
        self.combo_l_ctype.addItems(ALL_CURVE_TYPES)
        self.combo_l_ctype.currentTextChanged.connect(self.on_l_ctype_changed)

        btn_exp_l = QPushButton("Export Math")
        btn_exp_l.setObjectName("PrimaryBtn")
        btn_exp_l.clicked.connect(lambda: self.copy_to_clipboard(self.curve_graph_left.export_latex(), "Left Stick Math Formula"))

        ctype_l_box.addWidget(self.combo_l_ctype, stretch=2)
        ctype_l_box.addWidget(btn_exp_l, stretch=1)
        left_layout.addLayout(ctype_l_box)

        # Custom Equation Input (Visible when "custom" selected)
        self.edit_l_custom_eq = QLineEdit()
        self.edit_l_custom_eq.setObjectName("OutlinedEdit")
        self.edit_l_custom_eq.setPlaceholderText("Fill text box with equation (e.g. x**2 + 0.1*x)")
        self.edit_l_custom_eq.textChanged.connect(self.on_l_custom_eq_changed)
        self.edit_l_custom_eq.editingFinished.connect(lambda: self.save_opt("analog_left", "custom_eq", self.edit_l_custom_eq.text()))
        left_layout.addWidget(self.edit_l_custom_eq)

        # Reset Button
        btn_reset_l = QPushButton("Reset")
        btn_reset_l.setObjectName("PrimaryBtn")
        btn_reset_l.clicked.connect(lambda: self.reset_stick_defaults("analog_left"))
        left_layout.addWidget(btn_reset_l)

        # Bottom Circularity Row
        circ_l_box = QHBoxLayout()
        self.combo_l_circ = QComboBox()
        self.combo_l_circ.addItems(["before", "after", "disabled"])
        self.combo_l_circ.currentTextChanged.connect(self.on_l_circ_changed)

        btn_circ_l = QPushButton("Calibrate Circularity")
        btn_circ_l.setObjectName("SecondaryBtn")
        btn_circ_l.clicked.connect(lambda: self.launch_circularity("Left Stick", "Stick_Left"))

        btn_info_l = QPushButton("?")
        btn_info_l.setFixedWidth(28)
        btn_info_l.setObjectName("SecondaryBtn")
        btn_info_l.clicked.connect(self.show_circularity_info)

        circ_l_box.addWidget(self.combo_l_circ, stretch=2)
        circ_l_box.addWidget(btn_circ_l, stretch=2)
        circ_l_box.addWidget(btn_info_l, stretch=0)
        left_layout.addLayout(circ_l_box)

        stick_split.addWidget(left_card)

        # Right Stick Card
        right_card = QFrame()
        right_card.setObjectName("GlassCard")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(12, 10, 12, 10)

        lbl_r_title = QLabel("Right Stick")
        lbl_r_title.setStyleSheet("font-weight: bold; font-size: 15px;")
        lbl_r_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(lbl_r_title)

        # Visualizers Row: Response Curve & Current Position
        vis_r_box = QHBoxLayout()
        self.curve_graph_right = CurveGraphWidget("Right Stick Curve")
        self.radar_right = JoystickVisualizerWidget("Right Stick Position")

        vis_r_box.addWidget(self.curve_graph_right)
        vis_r_box.addWidget(self.radar_right)
        right_layout.addLayout(vis_r_box)

        # Sliders Grid (Matching Screenshot 2)
        grid_r = QGridLayout()
        grid_r.setSpacing(6)

        # 1. Deadzone
        grid_r.addWidget(QLabel("?  Deadzone"), 0, 0)
        self.slider_r_dz = QSlider(Qt.Orientation.Horizontal)
        self.slider_r_dz.setRange(0, 50)
        self.lbl_val_r_dz = QLabel("0.00")
        self.lbl_val_r_dz.setFixedWidth(40)
        self.slider_r_dz.valueChanged.connect(self.on_r_dz_changed)
        grid_r.addWidget(self.slider_r_dz, 0, 1)
        grid_r.addWidget(self.lbl_val_r_dz, 0, 2)

        # 2. Anti-Deadzone
        grid_r.addWidget(QLabel("?  Anti-Deadzone"), 1, 0)
        self.slider_r_adz = QSlider(Qt.Orientation.Horizontal)
        self.slider_r_adz.setRange(0, 30)
        self.lbl_val_r_adz = QLabel("0.00")
        self.lbl_val_r_adz.setFixedWidth(40)
        self.slider_r_adz.valueChanged.connect(self.on_r_adz_changed)
        grid_r.addWidget(self.slider_r_adz, 1, 1)
        grid_r.addWidget(self.lbl_val_r_adz, 1, 2)

        # 3. Rest Deadzone
        grid_r.addWidget(QLabel("?  Rest Deadzone"), 2, 0)
        self.slider_r_rdz = QSlider(Qt.Orientation.Horizontal)
        self.slider_r_rdz.setRange(0, 30)
        self.lbl_val_r_rdz = QLabel("0.00")
        self.lbl_val_r_rdz.setFixedWidth(40)
        self.slider_r_rdz.valueChanged.connect(self.on_r_rdz_changed)
        grid_r.addWidget(self.slider_r_rdz, 2, 1)
        grid_r.addWidget(self.lbl_val_r_rdz, 2, 2)

        # 4. Warp Threshold (Outer Max)
        grid_r.addWidget(QLabel("?  Warp Threshold"), 3, 0)
        self.slider_r_warp = QSlider(Qt.Orientation.Horizontal)
        self.slider_r_warp.setRange(50, 100)
        self.slider_r_warp.setValue(100)
        self.lbl_val_r_warp = QLabel("1.00")
        self.lbl_val_r_warp.setFixedWidth(40)
        self.slider_r_warp.valueChanged.connect(self.on_r_warp_changed)
        grid_r.addWidget(self.slider_r_warp, 3, 1)
        grid_r.addWidget(self.lbl_val_r_warp, 3, 2)

        # 5. Curve Factor (Exponent)
        grid_r.addWidget(QLabel("?  Curve Factor"), 4, 0)
        self.slider_r_cf = QSlider(Qt.Orientation.Horizontal)
        self.slider_r_cf.setRange(10, 50)  # 1.00 to 5.00
        self.slider_r_cf.setValue(10)
        self.lbl_val_r_cf = QLabel("1.00")
        self.lbl_val_r_cf.setFixedWidth(40)
        self.slider_r_cf.valueChanged.connect(self.on_r_cf_changed)
        grid_r.addWidget(self.slider_r_cf, 4, 1)
        grid_r.addWidget(self.lbl_val_r_cf, 4, 2)

        # 6. Sensitivity
        grid_r.addWidget(QLabel("?  Sensitivity"), 5, 0)
        self.slider_r_sens = QSlider(Qt.Orientation.Horizontal)
        self.slider_r_sens.setRange(5, 20)  # 0.50 to 2.00
        self.slider_r_sens.setValue(10)
        self.lbl_val_r_sens = QLabel("1.00")
        self.lbl_val_r_sens.setFixedWidth(40)
        self.slider_r_sens.valueChanged.connect(self.on_r_sens_changed)
        grid_r.addWidget(self.slider_r_sens, 5, 1)
        grid_r.addWidget(self.lbl_val_r_sens, 5, 2)

        right_layout.addLayout(grid_r)

        # Curve Type & Export Row
        ctype_r_box = QHBoxLayout()
        ctype_r_box.addWidget(QLabel("?  Curve Type:"))
        self.combo_r_ctype = QComboBox()
        self.combo_r_ctype.addItems(ALL_CURVE_TYPES)
        self.combo_r_ctype.currentTextChanged.connect(self.on_r_ctype_changed)

        btn_exp_r = QPushButton("Export Math")
        btn_exp_r.setObjectName("PrimaryBtn")
        btn_exp_r.clicked.connect(lambda: self.copy_to_clipboard(self.curve_graph_right.export_latex(), "Right Stick Math Formula"))

        ctype_r_box.addWidget(self.combo_r_ctype, stretch=2)
        ctype_r_box.addWidget(btn_exp_r, stretch=1)
        right_layout.addLayout(ctype_r_box)

        # Custom Equation Input
        self.edit_r_custom_eq = QLineEdit()
        self.edit_r_custom_eq.setObjectName("OutlinedEdit")
        self.edit_r_custom_eq.setPlaceholderText("Fill text box with equation (e.g. x**2 + 0.1*x)")
        self.edit_r_custom_eq.textChanged.connect(self.on_r_custom_eq_changed)
        self.edit_r_custom_eq.editingFinished.connect(lambda: self.save_opt("analog_right", "custom_eq", self.edit_r_custom_eq.text()))
        right_layout.addWidget(self.edit_r_custom_eq)

        # Reset Button
        btn_reset_r = QPushButton("Reset")
        btn_reset_r.setObjectName("PrimaryBtn")
        btn_reset_r.clicked.connect(lambda: self.reset_stick_defaults("analog_right"))
        right_layout.addWidget(btn_reset_r)

        # Bottom Circularity Row
        circ_r_box = QHBoxLayout()
        self.combo_r_circ = QComboBox()
        self.combo_r_circ.addItems(["disabled", "before", "after"])
        self.combo_r_circ.currentTextChanged.connect(self.on_r_circ_changed)

        btn_circ_r = QPushButton("Calibrate Circularity")
        btn_circ_r.setObjectName("SecondaryBtn")
        btn_circ_r.clicked.connect(lambda: self.launch_circularity("Right Stick", "Stick_Right"))

        btn_info_r = QPushButton("?")
        btn_info_r.setFixedWidth(28)
        btn_info_r.setObjectName("SecondaryBtn")
        btn_info_r.clicked.connect(self.show_circularity_info)

        circ_r_box.addWidget(self.combo_r_circ, stretch=2)
        circ_r_box.addWidget(btn_circ_r, stretch=2)
        circ_r_box.addWidget(btn_info_r, stretch=0)
        right_layout.addLayout(circ_r_box)

        stick_split.addWidget(right_card)
        scroll_layout.addLayout(stick_split)

        # ---------------------------------------------------------------------
        # SECTION 2: DUAL TRIGGER TUNING (Left Trigger & Right Trigger Side-by-Side)
        # ---------------------------------------------------------------------
        trig_split = QHBoxLayout()
        trig_split.setSpacing(14)

        # Left Trigger Card
        lt_card = QFrame()
        lt_card.setObjectName("GlassCard")
        lt_layout = QVBoxLayout(lt_card)
        lt_layout.setContentsMargins(12, 10, 12, 10)

        lbl_lt_title = QLabel("Left Trigger")
        lbl_lt_title.setStyleSheet("font-weight: bold; font-size: 15px;")
        lbl_lt_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lt_layout.addWidget(lbl_lt_title)

        # Visualizers Row: Response Curve & Trigger Pull Vertical Bars
        vis_lt_box = QHBoxLayout()
        self.curve_graph_lt = CurveGraphWidget("Left Trigger Curve")
        self.bar_lt = TriggerPullWidget("Left Trigger Pull")
        vis_lt_box.addWidget(self.curve_graph_lt)
        vis_lt_box.addWidget(self.bar_lt)
        lt_layout.addLayout(vis_lt_box)

        # Sliders Grid (Matching Screenshot 3)
        grid_lt = QGridLayout()
        grid_lt.setSpacing(6)

        # 1. Deadzone
        grid_lt.addWidget(QLabel("?  Deadzone"), 0, 0)
        self.slider_lt_dz = QSlider(Qt.Orientation.Horizontal)
        self.slider_lt_dz.setRange(0, 50)
        self.lbl_val_lt_dz = QLabel("0.00")
        self.lbl_val_lt_dz.setFixedWidth(40)
        self.slider_lt_dz.valueChanged.connect(self.on_lt_dz_changed)
        grid_lt.addWidget(self.slider_lt_dz, 0, 1)
        grid_lt.addWidget(self.lbl_val_lt_dz, 0, 2)

        # 2. Anti-Deadzone
        grid_lt.addWidget(QLabel("?  Anti-Deadzone"), 1, 0)
        self.slider_lt_adz = QSlider(Qt.Orientation.Horizontal)
        self.slider_lt_adz.setRange(0, 30)
        self.lbl_val_lt_adz = QLabel("0.00")
        self.lbl_val_lt_adz.setFixedWidth(40)
        self.slider_lt_adz.valueChanged.connect(self.on_lt_adz_changed)
        grid_lt.addWidget(self.slider_lt_adz, 1, 1)
        grid_lt.addWidget(self.lbl_val_lt_adz, 1, 2)

        # 3. Rest Deadzone
        grid_lt.addWidget(QLabel("?  Rest Deadzone"), 2, 0)
        self.slider_lt_rdz = QSlider(Qt.Orientation.Horizontal)
        self.slider_lt_rdz.setRange(0, 30)
        self.lbl_val_lt_rdz = QLabel("0.00")
        self.lbl_val_lt_rdz.setFixedWidth(40)
        self.slider_lt_rdz.valueChanged.connect(self.on_lt_rdz_changed)
        grid_lt.addWidget(self.slider_lt_rdz, 2, 1)
        grid_lt.addWidget(self.lbl_val_lt_rdz, 2, 2)

        # 4. Exponent (Curve Power)
        grid_lt.addWidget(QLabel("?  Exponent (Curve Power)"), 3, 0)
        self.slider_lt_exp = QSlider(Qt.Orientation.Horizontal)
        self.slider_lt_exp.setRange(10, 50)
        self.slider_lt_exp.setValue(10)
        self.lbl_val_lt_exp = QLabel("1.00")
        self.lbl_val_lt_exp.setFixedWidth(40)
        self.slider_lt_exp.valueChanged.connect(self.on_lt_exp_changed)
        grid_lt.addWidget(self.slider_lt_exp, 3, 1)
        grid_lt.addWidget(self.lbl_val_lt_exp, 3, 2)

        # 5. Sensitivity
        grid_lt.addWidget(QLabel("?  Sensitivity"), 4, 0)
        self.slider_lt_sens = QSlider(Qt.Orientation.Horizontal)
        self.slider_lt_sens.setRange(5, 20)
        self.slider_lt_sens.setValue(10)
        self.lbl_val_lt_sens = QLabel("1.00")
        self.lbl_val_lt_sens.setFixedWidth(40)
        self.slider_lt_sens.valueChanged.connect(self.on_lt_sens_changed)
        grid_lt.addWidget(self.slider_lt_sens, 4, 1)
        grid_lt.addWidget(self.lbl_val_lt_sens, 4, 2)

        lt_layout.addLayout(grid_lt)

        # Curve Type & Export Row
        ctype_lt_box = QHBoxLayout()
        ctype_lt_box.addWidget(QLabel("?  Curve Type:"))
        self.combo_lt_ctype = QComboBox()
        self.combo_lt_ctype.addItems(TRIGGER_CURVE_TYPES)
        self.combo_lt_ctype.currentTextChanged.connect(self.on_lt_ctype_changed)

        btn_exp_lt = QPushButton("Export Math")
        btn_exp_lt.setObjectName("PrimaryBtn")
        btn_exp_lt.clicked.connect(lambda: self.copy_to_clipboard(self.curve_graph_lt.export_latex(), "Left Trigger Math Formula"))

        ctype_lt_box.addWidget(self.combo_lt_ctype, stretch=2)
        ctype_lt_box.addWidget(btn_exp_lt, stretch=1)
        lt_layout.addLayout(ctype_lt_box)

        # Reset Button
        btn_reset_lt = QPushButton("Reset")
        btn_reset_lt.setObjectName("PrimaryBtn")
        btn_reset_lt.clicked.connect(lambda: self.reset_trigger_defaults("trigger_left"))
        lt_layout.addWidget(btn_reset_lt)

        # Digital Trigger Checkbox
        self.chk_dig_lt = QCheckBox("Digital Trigger Mode")
        self.chk_dig_lt.stateChanged.connect(lambda s: self.save_opt("settings", "digital_lt", str(s == Qt.CheckState.Checked.value or s == 2 or s is True).lower()))
        lt_layout.addWidget(self.chk_dig_lt)

        trig_split.addWidget(lt_card)

        # Right Trigger Card
        rt_card = QFrame()
        rt_card.setObjectName("GlassCard")
        rt_layout = QVBoxLayout(rt_card)
        rt_layout.setContentsMargins(12, 10, 12, 10)

        lbl_rt_title = QLabel("Right Trigger")
        lbl_rt_title.setStyleSheet("font-weight: bold; font-size: 15px;")
        lbl_rt_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rt_layout.addWidget(lbl_rt_title)

        # Visualizers Row: Response Curve & Trigger Pull Vertical Bars
        vis_rt_box = QHBoxLayout()
        self.curve_graph_rt = CurveGraphWidget("Right Trigger Curve")
        self.bar_rt = TriggerPullWidget("Right Trigger Pull")
        vis_rt_box.addWidget(self.curve_graph_rt)
        vis_rt_box.addWidget(self.bar_rt)
        rt_layout.addLayout(vis_rt_box)

        # Sliders Grid (Matching Screenshot 3)
        grid_rt = QGridLayout()
        grid_rt.setSpacing(6)

        # 1. Deadzone
        grid_rt.addWidget(QLabel("?  Deadzone"), 0, 0)
        self.slider_rt_dz = QSlider(Qt.Orientation.Horizontal)
        self.slider_rt_dz.setRange(0, 50)
        self.lbl_val_rt_dz = QLabel("0.00")
        self.lbl_val_rt_dz.setFixedWidth(40)
        self.slider_rt_dz.valueChanged.connect(self.on_rt_dz_changed)
        grid_rt.addWidget(self.slider_rt_dz, 0, 1)
        grid_rt.addWidget(self.lbl_val_rt_dz, 0, 2)

        # 2. Anti-Deadzone
        grid_rt.addWidget(QLabel("?  Anti-Deadzone"), 1, 0)
        self.slider_rt_adz = QSlider(Qt.Orientation.Horizontal)
        self.slider_rt_adz.setRange(0, 30)
        self.lbl_val_rt_adz = QLabel("0.00")
        self.lbl_val_rt_adz.setFixedWidth(40)
        self.slider_rt_adz.valueChanged.connect(self.on_rt_adz_changed)
        grid_rt.addWidget(self.slider_rt_adz, 1, 1)
        grid_rt.addWidget(self.lbl_val_rt_adz, 1, 2)

        # 3. Rest Deadzone
        grid_rt.addWidget(QLabel("?  Rest Deadzone"), 2, 0)
        self.slider_rt_rdz = QSlider(Qt.Orientation.Horizontal)
        self.slider_rt_rdz.setRange(0, 30)
        self.lbl_val_rt_rdz = QLabel("0.00")
        self.lbl_val_rt_rdz.setFixedWidth(40)
        self.slider_rt_rdz.valueChanged.connect(self.on_rt_rdz_changed)
        grid_rt.addWidget(self.slider_rt_rdz, 2, 1)
        grid_rt.addWidget(self.lbl_val_rt_rdz, 2, 2)

        # 4. Exponent (Curve Power)
        grid_rt.addWidget(QLabel("?  Exponent (Curve Power)"), 3, 0)
        self.slider_rt_exp = QSlider(Qt.Orientation.Horizontal)
        self.slider_rt_exp.setRange(10, 50)
        self.slider_rt_exp.setValue(10)
        self.lbl_val_rt_exp = QLabel("1.00")
        self.lbl_val_rt_exp.setFixedWidth(40)
        self.slider_rt_exp.valueChanged.connect(self.on_rt_exp_changed)
        grid_rt.addWidget(self.slider_rt_exp, 3, 1)
        grid_rt.addWidget(self.lbl_val_rt_exp, 3, 2)

        # 5. Sensitivity
        grid_rt.addWidget(QLabel("?  Sensitivity"), 4, 0)
        self.slider_rt_sens = QSlider(Qt.Orientation.Horizontal)
        self.slider_rt_sens.setRange(5, 20)
        self.slider_rt_sens.setValue(10)
        self.lbl_val_rt_sens = QLabel("1.00")
        self.lbl_val_rt_sens.setFixedWidth(40)
        self.slider_rt_sens.valueChanged.connect(self.on_rt_sens_changed)
        grid_rt.addWidget(self.slider_rt_sens, 4, 1)
        grid_rt.addWidget(self.lbl_val_rt_sens, 4, 2)

        rt_layout.addLayout(grid_rt)

        # Curve Type & Export Row
        ctype_rt_box = QHBoxLayout()
        ctype_rt_box.addWidget(QLabel("?  Curve Type:"))
        self.combo_rt_ctype = QComboBox()
        self.combo_rt_ctype.addItems(TRIGGER_CURVE_TYPES)
        self.combo_rt_ctype.currentTextChanged.connect(self.on_rt_ctype_changed)

        btn_exp_rt = QPushButton("Export Math")
        btn_exp_rt.setObjectName("PrimaryBtn")
        btn_exp_rt.clicked.connect(lambda: self.copy_to_clipboard(self.curve_graph_rt.export_latex(), "Right Trigger Math Formula"))

        ctype_rt_box.addWidget(self.combo_rt_ctype, stretch=2)
        ctype_rt_box.addWidget(btn_exp_rt, stretch=1)
        rt_layout.addLayout(ctype_rt_box)

        # Reset Button
        btn_reset_rt = QPushButton("Reset")
        btn_reset_rt.setObjectName("PrimaryBtn")
        btn_reset_rt.clicked.connect(lambda: self.reset_trigger_defaults("trigger_right"))
        rt_layout.addWidget(btn_reset_rt)

        # Digital Trigger Checkbox
        self.chk_dig_rt = QCheckBox("Digital Trigger Mode")
        self.chk_dig_rt.stateChanged.connect(lambda s: self.save_opt("settings", "digital_rt", str(s == Qt.CheckState.Checked.value or s == 2 or s is True).lower()))
        rt_layout.addWidget(self.chk_dig_rt)

        trig_split.addWidget(rt_card)

        scroll_layout.addLayout(trig_split)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    # ---------------------------------------------------------------------
    # Left Stick Event Handlers
    # ---------------------------------------------------------------------
    def on_l_dz_changed(self, v):
        val = v / 100.0
        self.lbl_val_l_dz.setText(f"{val:.2f}")
        self.radar_left.set_deadzone(v)
        self.save_opt("analog_left", "deadzone", val)

    def on_l_adz_changed(self, v):
        val = v / 100.0
        self.lbl_val_l_adz.setText(f"{val:.2f}")
        self.save_opt("analog_left", "anti_deadzone", val)

    def on_l_rdz_changed(self, v):
        val = v / 100.0
        self.lbl_val_l_rdz.setText(f"{val:.2f}")
        self.save_opt("analog_left", "rest_deadzone", val)

    def on_l_warp_changed(self, v):
        val = v / 100.0
        self.lbl_val_l_warp.setText(f"{val:.2f}")
        self.save_opt("analog_left", "outer_max", val)

    def on_l_cf_changed(self, v):
        val = v / 10.0
        self.lbl_val_l_cf.setText(f"{val:.2f}")
        self.curve_graph_left.set_curve_params(self.combo_l_ctype.currentText(), val, self.edit_l_custom_eq.text())
        self.save_opt("analog_left", "exp_factor", val)

    def on_l_sens_changed(self, v):
        val = v / 10.0
        self.lbl_val_l_sens.setText(f"{val:.2f}")
        self.save_opt("analog_left", "sensitivity", val)

    def on_l_ctype_changed(self, ctype):
        is_custom = (ctype == "custom")
        self.edit_l_custom_eq.setVisible(is_custom)
        self.curve_graph_left.set_curve_params(ctype, self.slider_l_cf.value() / 10.0, self.edit_l_custom_eq.text())
        self.save_opt("analog_left", "curve", ctype)

    def on_l_custom_eq_changed(self, text):
        self.curve_graph_left.set_curve_params(self.combo_l_ctype.currentText(), self.slider_l_cf.value() / 10.0, text)

    def on_l_circ_changed(self, mode):
        self.radar_left.set_circularity_mode(mode)
        self.save_opt("analog_left", "circularity_mode", mode)

    def on_r_circ_changed(self, mode):
        self.radar_right.set_circularity_mode(mode)
        self.save_opt("analog_right", "circularity_mode", mode)

    def reset_stick_defaults(self, section):
        if section == "analog_left":
            self.slider_l_dz.setValue(5)
            self.slider_l_adz.setValue(0)
            self.slider_l_rdz.setValue(0)
            self.slider_l_warp.setValue(100)
            self.slider_l_cf.setValue(10)
            self.slider_l_sens.setValue(10)
            self.combo_l_ctype.setCurrentText("linear")
        else:
            self.slider_r_dz.setValue(5)
            self.slider_r_adz.setValue(0)
            self.slider_r_rdz.setValue(0)
            self.slider_r_warp.setValue(100)
            self.slider_r_cf.setValue(10)
            self.slider_r_sens.setValue(10)
            self.combo_r_ctype.setCurrentText("linear")
        QMessageBox.information(self, "Reset Defaults", f"✓ Stick parameters reset to defaults for {section}.")

    # ---------------------------------------------------------------------
    # Right Stick Event Handlers
    # ---------------------------------------------------------------------
    def on_r_dz_changed(self, v):
        val = v / 100.0
        self.lbl_val_r_dz.setText(f"{val:.2f}")
        self.radar_right.set_deadzone(v)
        self.save_opt("analog_right", "deadzone", val)

    def on_r_adz_changed(self, v):
        val = v / 100.0
        self.lbl_val_r_adz.setText(f"{val:.2f}")
        self.save_opt("analog_right", "anti_deadzone", val)

    def on_r_rdz_changed(self, v):
        val = v / 100.0
        self.lbl_val_r_rdz.setText(f"{val:.2f}")
        self.save_opt("analog_right", "rest_deadzone", val)

    def on_r_warp_changed(self, v):
        val = v / 100.0
        self.lbl_val_r_warp.setText(f"{val:.2f}")
        self.save_opt("analog_right", "outer_max", val)

    def on_r_cf_changed(self, v):
        val = v / 10.0
        self.lbl_val_r_cf.setText(f"{val:.2f}")
        self.curve_graph_right.set_curve_params(self.combo_r_ctype.currentText(), val, self.edit_r_custom_eq.text())
        self.save_opt("analog_right", "exp_factor", val)

    def on_r_sens_changed(self, v):
        val = v / 10.0
        self.lbl_val_r_sens.setText(f"{val:.2f}")
        self.save_opt("analog_right", "sensitivity", val)

    def on_r_ctype_changed(self, ctype):
        is_custom = (ctype == "custom")
        self.edit_r_custom_eq.setVisible(is_custom)
        self.curve_graph_right.set_curve_params(ctype, self.slider_r_cf.value() / 10.0, self.edit_r_custom_eq.text())
        self.save_opt("analog_right", "curve", ctype)

    def on_r_custom_eq_changed(self, text):
        self.curve_graph_right.set_curve_params(self.combo_r_ctype.currentText(), self.slider_r_cf.value() / 10.0, text)

    # ---------------------------------------------------------------------
    # Left Trigger Event Handlers
    # ---------------------------------------------------------------------
    def on_lt_dz_changed(self, v):
        val = v / 100.0
        self.lbl_val_lt_dz.setText(f"{val:.2f}")
        self.curve_graph_lt.set_curve_params(self.combo_lt_ctype.currentText(), self.slider_lt_exp.value() / 10.0)
        self.save_opt("trigger_left", "deadzone", val)

    def on_lt_adz_changed(self, v):
        val = v / 100.0
        self.lbl_val_lt_adz.setText(f"{val:.2f}")
        self.curve_graph_lt.set_curve_params(self.combo_lt_ctype.currentText(), self.slider_lt_exp.value() / 10.0)
        self.save_opt("trigger_left", "anti_deadzone", val)

    def on_lt_rdz_changed(self, v):
        val = v / 100.0
        self.lbl_val_lt_rdz.setText(f"{val:.2f}")
        self.curve_graph_lt.set_curve_params(self.combo_lt_ctype.currentText(), self.slider_lt_exp.value() / 10.0)
        self.save_opt("trigger_left", "rest_deadzone", val)

    def on_lt_exp_changed(self, v):
        val = v / 10.0
        self.lbl_val_lt_exp.setText(f"{val:.2f}")
        self.curve_graph_lt.set_curve_params(self.combo_lt_ctype.currentText(), val)
        self.save_opt("trigger_left", "exp_factor", val)

    def on_lt_sens_changed(self, v):
        val = v / 10.0
        self.lbl_val_lt_sens.setText(f"{val:.2f}")
        self.curve_graph_lt.set_curve_params(self.combo_lt_ctype.currentText(), self.slider_lt_exp.value() / 10.0)
        self.save_opt("trigger_left", "sensitivity", val)

    def on_lt_ctype_changed(self, ctype):
        self.curve_graph_lt.set_curve_params(ctype, self.slider_lt_exp.value() / 10.0)
        self.save_opt("trigger_left", "curve", ctype)

    def reset_trigger_defaults(self, section):
        if section == "trigger_left":
            self.slider_lt_dz.setValue(5)
            self.slider_lt_adz.setValue(0)
            self.slider_lt_rdz.setValue(0)
            self.slider_lt_exp.setValue(10)
            self.slider_lt_sens.setValue(10)
            self.combo_lt_ctype.setCurrentText("linear")
        else:
            self.slider_rt_dz.setValue(5)
            self.slider_rt_adz.setValue(0)
            self.slider_rt_rdz.setValue(0)
            self.slider_rt_exp.setValue(10)
            self.slider_rt_sens.setValue(10)
            self.combo_rt_ctype.setCurrentText("linear")
        QMessageBox.information(self, "Reset Defaults", f"✓ Trigger parameters reset to defaults for {section}.")

    # ---------------------------------------------------------------------
    # Right Trigger Event Handlers
    # ---------------------------------------------------------------------
    def on_rt_dz_changed(self, v):
        val = v / 100.0
        self.lbl_val_rt_dz.setText(f"{val:.2f}")
        self.curve_graph_rt.set_curve_params(self.combo_rt_ctype.currentText(), self.slider_rt_exp.value() / 10.0)
        self.save_opt("trigger_right", "deadzone", val)

    def on_rt_adz_changed(self, v):
        val = v / 100.0
        self.lbl_val_rt_adz.setText(f"{val:.2f}")
        self.curve_graph_rt.set_curve_params(self.combo_rt_ctype.currentText(), self.slider_rt_exp.value() / 10.0)
        self.save_opt("trigger_right", "anti_deadzone", val)

    def on_rt_rdz_changed(self, v):
        val = v / 100.0
        self.lbl_val_rt_rdz.setText(f"{val:.2f}")
        self.curve_graph_rt.set_curve_params(self.combo_rt_ctype.currentText(), self.slider_rt_exp.value() / 10.0)
        self.save_opt("trigger_right", "rest_deadzone", val)

    def on_rt_exp_changed(self, v):
        val = v / 10.0
        self.lbl_val_rt_exp.setText(f"{val:.2f}")
        self.curve_graph_rt.set_curve_params(self.combo_rt_ctype.currentText(), val)
        self.save_opt("trigger_right", "exp_factor", val)

    def on_rt_sens_changed(self, v):
        val = v / 10.0
        self.lbl_val_rt_sens.setText(f"{val:.2f}")
        self.curve_graph_rt.set_curve_params(self.combo_rt_ctype.currentText(), self.slider_rt_exp.value() / 10.0)
        self.save_opt("trigger_right", "sensitivity", val)

    def on_rt_ctype_changed(self, ctype):
        self.curve_graph_rt.set_curve_params(ctype, self.slider_rt_exp.value() / 10.0)
        self.save_opt("trigger_right", "curve", ctype)

    def save_opt(self, section, option, val):
        config = getattr(self.app, 'controller_config', None)
        if config:
            config.set(section, option, str(val))
            self.app.save_config()

    def load_config_values(self):
        config = getattr(self.app, 'controller_config', None)
        if not config:
            return

        # 1. Left Stick (Symmetrical Load)
        dz_l = int(config.getfloat("analog_left", "deadzone", 0.05) * 100)
        self.slider_l_dz.setValue(dz_l)
        self.radar_left.set_deadzone(dz_l)

        adz_l = int(config.getfloat("analog_left", "anti_deadzone", 0.0) * 100)
        self.slider_l_adz.setValue(adz_l)

        rdz_l = int(config.getfloat("analog_left", "rest_deadzone", 0.0) * 100)
        self.slider_l_rdz.setValue(rdz_l)

        warp_l = int(config.getfloat("analog_left", "outer_max", 1.0) * 100)
        self.slider_l_warp.setValue(warp_l)

        cf_l = int(config.getfloat("analog_left", "exp_factor", 1.0) * 10)
        self.slider_l_cf.setValue(cf_l)

        sens_l = int(config.getfloat("analog_left", "sensitivity", 1.0) * 10)
        self.slider_l_sens.setValue(sens_l)

        ctype_l = config.get("analog_left", "curve", fallback="linear").lower()
        self.combo_l_ctype.setCurrentText(ctype_l)
        self.edit_l_custom_eq.setText(config.get("analog_left", "custom_eq", fallback=""))

        circ_l = config.get("analog_left", "circularity_mode", fallback="disabled").lower()
        self.combo_l_circ.setCurrentText(circ_l)
        self.radar_left.set_circularity_mode(circ_l)

        # 2. Right Stick (Symmetrical Load)
        dz_r = int(config.getfloat("analog_right", "deadzone", 0.05) * 100)
        self.slider_r_dz.setValue(dz_r)
        self.radar_right.set_deadzone(dz_r)

        adz_r = int(config.getfloat("analog_right", "anti_deadzone", 0.0) * 100)
        self.slider_r_adz.setValue(adz_r)

        rdz_r = int(config.getfloat("analog_right", "rest_deadzone", 0.0) * 100)
        self.slider_r_rdz.setValue(rdz_r)

        warp_r = int(config.getfloat("analog_right", "outer_max", 1.0) * 100)
        self.slider_r_warp.setValue(warp_r)

        cf_r = int(config.getfloat("analog_right", "exp_factor", 1.0) * 10)
        self.slider_r_cf.setValue(cf_r)

        sens_r = int(config.getfloat("analog_right", "sensitivity", 1.0) * 10)
        self.slider_r_sens.setValue(sens_r)

        ctype_r = config.get("analog_right", "curve", fallback="linear").lower()
        self.combo_r_ctype.setCurrentText(ctype_r)
        self.edit_r_custom_eq.setText(config.get("analog_right", "custom_eq", fallback=""))

        circ_r = config.get("analog_right", "circularity_mode", fallback="disabled").lower()
        self.combo_r_circ.setCurrentText(circ_r)
        self.radar_right.set_circularity_mode(circ_r)

        # 3. Left Trigger (Symmetrical Load)
        dz_lt = int(config.getfloat("trigger_left", "deadzone", 0.05) * 100)
        self.slider_lt_dz.setValue(dz_lt)

        adz_lt = int(config.getfloat("trigger_left", "anti_deadzone", 0.0) * 100)
        self.slider_lt_adz.setValue(adz_lt)

        rdz_lt = int(config.getfloat("trigger_left", "rest_deadzone", 0.0) * 100)
        self.slider_lt_rdz.setValue(rdz_lt)

        exp_lt = int(config.getfloat("trigger_left", "exp_factor", 1.0) * 10)
        self.slider_lt_exp.setValue(exp_lt)

        sens_lt = int(config.getfloat("trigger_left", "sensitivity", 1.0) * 10)
        self.slider_lt_sens.setValue(sens_lt)

        ctype_lt = config.get("trigger_left", "curve", fallback="linear").lower()
        self.combo_lt_ctype.setCurrentText(ctype_lt)

        # 4. Right Trigger (Symmetrical Load)
        dz_rt = int(config.getfloat("trigger_right", "deadzone", 0.05) * 100)
        self.slider_rt_dz.setValue(dz_rt)

        adz_rt = int(config.getfloat("trigger_right", "anti_deadzone", 0.0) * 100)
        self.slider_rt_adz.setValue(adz_rt)

        rdz_rt = int(config.getfloat("trigger_right", "rest_deadzone", 0.0) * 100)
        self.slider_rt_rdz.setValue(rdz_rt)

        exp_rt = int(config.getfloat("trigger_right", "exp_factor", 1.0) * 10)
        self.slider_rt_exp.setValue(exp_rt)

        sens_rt = int(config.getfloat("trigger_right", "sensitivity", 1.0) * 10)
        self.slider_rt_sens.setValue(sens_rt)

        ctype_rt = config.get("trigger_right", "curve", fallback="linear").lower()
        self.combo_rt_ctype.setCurrentText(ctype_rt)

        # Digital Trigger Checkboxes
        self.chk_dig_lt.setChecked(config.getboolean("settings", "digital_lt", False))
        self.chk_dig_rt.setChecked(config.getboolean("settings", "digital_rt", False))

    def show_circularity_info(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Circularity Compensation Modes")
        msg.setText(
            "• before: Polar grid transformation applied before response curve math.\n"
            "• after: Polar grid transformation applied after response curve math.\n"
            "• disabled: No circularity transformation applied.\n\n"
            "Recommended: 'before' for smooth diagonal stick response."
        )
        msg.exec()

    def update_state(self, controller_state):
        if not controller_state:
            return

        lx = controller_state.lx or 0.0
        ly = controller_state.ly or 0.0
        rx = controller_state.rx or 0.0
        ry = controller_state.ry or 0.0
        lt = controller_state.lt or 0.0
        rt = controller_state.rt or 0.0

        # Compute tuned stick outputs using math_utils
        dz_l = self.slider_l_dz.value() / 100.0
        adz_l = self.slider_l_adz.value() / 100.0
        warp_l = self.slider_l_warp.value() / 100.0
        ctype_l = self.combo_l_ctype.currentText()
        cf_l = self.slider_l_cf.value() / 10.0
        custom_l = self.edit_l_custom_eq.text()

        mod_lx, mod_ly = math_utils.process_analog_stick(
            lx, ly, dz_l, adz_l, warp_l, ctype_l, cf_l, custom_l
        )

        dz_r = self.slider_r_dz.value() / 100.0
        adz_r = self.slider_r_adz.value() / 100.0
        warp_r = self.slider_r_warp.value() / 100.0
        ctype_r = self.combo_r_ctype.currentText()
        cf_r = self.slider_r_cf.value() / 10.0
        custom_r = self.edit_r_custom_eq.text()

        mod_rx, mod_ry = math_utils.process_analog_stick(
            rx, ry, dz_r, adz_r, warp_r, ctype_r, cf_r, custom_r
        )

        dz_lt = self.slider_lt_dz.value() / 100.0
        adz_lt = self.slider_lt_adz.value() / 100.0
        rdz_lt = self.slider_lt_rdz.value() / 100.0
        exp_lt = self.slider_lt_exp.value() / 10.0
        sens_lt = self.slider_lt_sens.value() / 10.0
        ctype_lt = self.combo_lt_ctype.currentText()
        mod_lt = math_utils.process_trigger(lt, dz_lt, adz_lt, ctype_lt, exp_lt, rest_dz=rdz_lt, sensitivity=sens_lt)
        if self.chk_dig_lt.isChecked() and mod_lt > 0:
            mod_lt = 1.0

        dz_rt = self.slider_rt_dz.value() / 100.0
        adz_rt = self.slider_rt_adz.value() / 100.0
        rdz_rt = self.slider_rt_rdz.value() / 100.0
        exp_rt = self.slider_rt_exp.value() / 10.0
        sens_rt = self.slider_rt_sens.value() / 10.0
        ctype_rt = self.combo_rt_ctype.currentText()
        mod_rt = math_utils.process_trigger(rt, dz_rt, adz_rt, ctype_rt, exp_rt, rest_dz=rdz_rt, sensitivity=sens_rt)
        if self.chk_dig_rt.isChecked() and mod_rt > 0:
            mod_rt = 1.0

        # Update Position Radars
        self.radar_left.set_stick_position(mod_lx, mod_ly, raw_x=lx, raw_y=ly)
        self.curve_graph_left.set_live_input_output(math.hypot(lx, ly), math.hypot(mod_lx, mod_ly))

        self.radar_right.set_stick_position(mod_rx, mod_ry, raw_x=rx, raw_y=ry)
        self.curve_graph_right.set_live_input_output(math.hypot(rx, ry), math.hypot(mod_rx, mod_ry))

        # Update Trigger Pull Vertical Bars
        self.bar_lt.set_values(lt, mod_lt)
        self.curve_graph_lt.set_live_input_output(lt, mod_lt)

        self.bar_rt.set_values(rt, mod_rt)
        self.curve_graph_rt.set_live_input_output(rt, mod_rt)

    def copy_to_clipboard(self, text, label):
        QApplication.clipboard().setText(text)
        msg = QMessageBox(self)
        msg.setWindowTitle("Export Math")
        msg.setText(f"✓ Copied {label} string to clipboard!\n\n{text}")
        msg.exec()

    def launch_circularity(self, title, section):
        dlg = CircularityCalibrationDialog(self.app, title=title, section=section)
        dlg.exec()
