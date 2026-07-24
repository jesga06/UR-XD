"""
Tuning View for PySide6 GUI (tuning_view.py)
Analog stick deadzones, anti-deadzones, response curve presets, interactive curve editor,
trigger min/max deadzones, and CircularityCalibrationDialog launcher.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSlider, QSpinBox,
    QComboBox, QPushButton, QGridLayout, QScrollArea
)
from PySide6.QtCore import Qt
from components.circularity_modal_qt import CircularityCalibrationDialog


class TuningView(QWidget):
    """
    Tuning Tab View handling stick & trigger analog response parameters.
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
        lbl_left_title = QLabel("🎯 LEFT STICK TUNING & DEADZONES")
        lbl_left_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")

        btn_left_circ = QPushButton("🎯 Circularity Calibration")
        btn_left_circ.setObjectName("PrimaryBtn")
        btn_left_circ.clicked.connect(lambda: self.launch_circularity("Left Stick", "Stick_Left"))

        left_header.addWidget(lbl_left_title)
        left_header.addStretch()
        left_header.addWidget(btn_left_circ)
        left_layout.addLayout(left_header)

        # Left Deadzone Controls
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

        grid_left.addWidget(QLabel("Response Curve Preset:"), 2, 0)
        combo_l_curve = QComboBox()
        combo_l_curve.addItems(["Linear", "Aggressive", "Smooth", "S-Curve", "Custom"])
        grid_left.addWidget(combo_l_curve, 2, 1, 1, 2)

        left_layout.addLayout(grid_left)
        scroll_layout.addWidget(left_card)

        # 2. Right Stick Card
        right_card = QFrame()
        right_card.setObjectName("GlassCard")
        right_layout = QVBoxLayout(right_card)

        right_header = QHBoxLayout()
        lbl_right_title = QLabel("🎯 RIGHT STICK TUNING & DEADZONES")
        lbl_right_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")

        btn_right_circ = QPushButton("🎯 Circularity Calibration")
        btn_right_circ.setObjectName("PrimaryBtn")
        btn_right_circ.clicked.connect(lambda: self.launch_circularity("Right Stick", "Stick_Right"))

        right_header.addWidget(lbl_right_title)
        right_header.addStretch()
        right_header.addWidget(btn_right_circ)
        right_layout.addLayout(right_header)

        grid_right = QGridLayout()
        grid_right.addWidget(QLabel("Inner Deadzone (%):"), 0, 0)
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

        grid_right.addWidget(QLabel("Response Curve Preset:"), 2, 0)
        combo_r_curve = QComboBox()
        combo_r_curve.addItems(["Linear", "Aggressive", "Smooth", "S-Curve", "Custom"])
        grid_right.addWidget(combo_r_curve, 2, 1, 1, 2)

        right_layout.addLayout(grid_right)
        scroll_layout.addWidget(right_card)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def launch_circularity(self, title, section):
        dlg = CircularityCalibrationDialog(self.app, title=title, section=section)
        dlg.exec()
