"""
Tuning View for PySide6 GUI (tuning_view.py)
Left & Right stick deadzones, anti-deadzones, response curve selector,
interactive CurveGraphWidget with draggable points and LaTeX/JSON export,
trigger min/max deadzones & sensitivity sliders, digital trigger toggles,
circularity mode selectors (disabled, before, after), info popup, bounds reset, and wizard launcher.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSlider, QSpinBox,
    QComboBox, QPushButton, QGridLayout, QScrollArea, QCheckBox, QMessageBox, QApplication
)
from PySide6.QtCore import Qt
from components.circularity_modal_qt import CircularityCalibrationDialog
from components.curve_graph_widget import CurveGraphWidget


class TuningView(QWidget):
    """
    Tuning Tab View providing comprehensive stick & trigger response tuning tools.
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

        # 1. Left Stick Card
        left_card = QFrame()
        left_card.setObjectName("GlassCard")
        left_layout = QVBoxLayout(left_card)

        left_header = QHBoxLayout()
        lbl_left_title = QLabel("🎯 LEFT STICK TUNING & CURVES")
        lbl_left_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")

        btn_left_circ = QPushButton("🎯 Circularity Calibration Wizard")
        btn_left_circ.setObjectName("PrimaryBtn")
        btn_left_circ.clicked.connect(lambda: self.launch_circularity("Left Stick", "Stick_Left"))

        left_header.addWidget(lbl_left_title)
        left_header.addStretch()
        left_header.addWidget(btn_left_circ)
        left_layout.addLayout(left_header)

        # Left Stick Deadzone & Circularity Settings
        grid_left = QGridLayout()
        grid_left.addWidget(QLabel("Inner Deadzone (%):"), 0, 0)
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

        grid_left.addWidget(QLabel("Circularity Compensation Mode:"), 2, 0)
        combo_l_circ_mode = QComboBox()
        combo_l_circ_mode.addItems(["Disabled", "Before Curves", "After Curves"])
        grid_left.addWidget(combo_l_circ_mode, 2, 1, 1, 2)

        grid_left.addWidget(QLabel("Response Curve Preset:"), 3, 0)
        combo_l_curve = QComboBox()
        combo_l_curve.addItems(["Linear", "Aggressive", "Smooth", "S-Curve", "Custom"])
        grid_left.addWidget(combo_l_curve, 3, 1, 1, 2)

        left_layout.addLayout(grid_left)

        # Interactive Response Curve Graph Editor Widget
        lbl_graph_l = QLabel("Interactive Response Curve Editor (Drag points to customize):")
        lbl_graph_l.setStyleSheet("font-weight: bold; color: #a992cb;")
        left_layout.addWidget(lbl_graph_l)

        self.curve_graph_l = CurveGraphWidget()
        combo_l_curve.currentTextChanged.connect(self.curve_graph_l.set_preset)
        left_layout.addWidget(self.curve_graph_l)

        # Math Export Buttons
        math_box_l = QHBoxLayout()
        btn_copy_latex_l = QPushButton("LaTeX Formula 📋")
        btn_copy_latex_l.setObjectName("SecondaryBtn")
        btn_copy_latex_l.clicked.connect(lambda: self.copy_to_clipboard(self.curve_graph_l.export_latex(), "LaTeX"))

        btn_copy_json_l = QPushButton("JSON Points 📋")
        btn_copy_json_l.setObjectName("SecondaryBtn")
        btn_copy_json_l.clicked.connect(lambda: self.copy_to_clipboard(self.curve_graph_l.export_json(), "JSON"))

        math_box_l.addWidget(btn_copy_latex_l)
        math_box_l.addWidget(btn_copy_json_l)
        math_box_l.addStretch()
        left_layout.addLayout(math_box_l)

        scroll_layout.addWidget(left_card)

        # 2. Trigger Sensitivity & Digital Step-Function Tuning Card
        trig_card = QFrame()
        trig_card.setObjectName("GlassCard")
        trig_layout = QVBoxLayout(trig_card)

        lbl_trig_title = QLabel("⚡ ANALOG TRIGGER TUNING & DIGITAL STEP-FUNCTIONS")
        lbl_trig_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")
        trig_layout.addWidget(lbl_trig_title)

        grid_trig = QGridLayout()
        grid_trig.addWidget(QLabel("LT Min Deadzone (%):"), 0, 0)
        spin_lt_min = QSpinBox()
        spin_lt_min.setValue(2)
        grid_trig.addWidget(spin_lt_min, 0, 1)

        grid_trig.addWidget(QLabel("LT Max Threshold (%):"), 0, 2)
        spin_lt_max = QSpinBox()
        spin_lt_max.setValue(98)
        grid_trig.addWidget(spin_lt_max, 0, 3)

        grid_trig.addWidget(QLabel("RT Min Deadzone (%):"), 1, 0)
        spin_rt_min = QSpinBox()
        spin_rt_min.setValue(2)
        grid_trig.addWidget(spin_rt_min, 1, 1)

        grid_trig.addWidget(QLabel("RT Max Threshold (%):"), 1, 2)
        spin_rt_max = QSpinBox()
        spin_rt_max.setValue(98)
        grid_trig.addWidget(spin_rt_max, 1, 3)

        trig_layout.addLayout(grid_trig)

        chk_dig_lt = QCheckBox("Enable Digital Hair-Trigger Mode for LT")
        chk_dig_rt = QCheckBox("Enable Digital Hair-Trigger Mode for RT")
        trig_layout.addWidget(chk_dig_lt)
        trig_layout.addWidget(chk_dig_rt)

        scroll_layout.addWidget(trig_card)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def copy_to_clipboard(self, text, label):
        QApplication.clipboard().setText(text)
        msg = QMessageBox(self)
        msg.setWindowTitle("Export Math")
        msg.setText(f"✓ Copied {label} string to clipboard!\n\n{text}")
        msg.exec()

    def launch_circularity(self, title, section):
        dlg = CircularityCalibrationDialog(self.app, title=title, section=section)
        dlg.exec()
