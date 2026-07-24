"""
Advanced View for PySide6 GUI (advanced_view.py)
ViGEmBus virtual XInput controller options, Hardware Chords Engine Table with config binding,
Macro Sequence Builder & Recorder, Haptic Feedback Engine UI & Waveform Canvas, and test vibration runner.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QCheckBox, QComboBox,
    QPushButton, QSpinBox, QGridLayout, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QLineEdit
)
from PySide6.QtCore import Qt
from components.haptic_waveform_widget import HapticWaveformWidget
import haptic_engine


class AdvancedView(QWidget):
    """
    Advanced Tab View handling hardware chords, macro manager, haptics, and ViGEmBus settings.
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

        # 1. Hardware Chords Engine Manager Card
        chords_card = QFrame()
        chords_card.setObjectName("GlassCard")
        chords_layout = QVBoxLayout(chords_card)

        chords_header = QHBoxLayout()
        lbl_chords = QLabel("⚡ HARDWARE CHORDS ENGINE MANAGER")
        lbl_chords.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")

        btn_add_chord = QPushButton("+ Add Hardware Chord")
        btn_add_chord.setObjectName("PrimaryBtn")
        btn_add_chord.clicked.connect(lambda: self.add_chord_row("LB + START", "Virtual Paddle M1", True))

        chords_header.addWidget(lbl_chords)
        chords_header.addStretch()
        chords_header.addWidget(btn_add_chord)
        chords_layout.addLayout(chords_header)

        self.table_chords = QTableWidget(0, 4)
        self.table_chords.setHorizontalHeaderLabels(["Trigger Combo", "Target Action / Button", "Suppress Physical", "Actions"])
        self.table_chords.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_chords.setMinimumHeight(140)
        self.table_chords.itemChanged.connect(self.save_hardware_chords)
        chords_layout.addWidget(self.table_chords)

        scroll_layout.addWidget(chords_card)

        # 2. Standalone Macro Manager Card
        macro_card = QFrame()
        macro_card.setObjectName("GlassCard")
        macro_layout = QVBoxLayout(macro_card)

        macro_header = QHBoxLayout()
        lbl_macro_title = QLabel("📜 MACRO SEQUENCE BUILDER & RECORDER")
        lbl_macro_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")
        macro_header.addWidget(lbl_macro_title)
        macro_header.addStretch()
        macro_layout.addLayout(macro_header)

        grid_macro = QGridLayout()
        grid_macro.addWidget(QLabel("Select Macro Sequence:"), 0, 0)
        self.combo_macros = QComboBox()
        self.combo_macros.addItems(["FastCombo (A, B, X)", "SuperJump (LB, A)", "Custom Sequence 1"])
        grid_macro.addWidget(self.combo_macros, 0, 1)

        grid_macro.addWidget(QLabel("Step Delay (ms):"), 0, 2)
        self.spin_macro_delay = QSpinBox()
        self.spin_macro_delay.setRange(1, 1000)
        self.spin_macro_delay.setValue(50)
        grid_macro.addWidget(self.spin_macro_delay, 0, 3)

        macro_layout.addLayout(grid_macro)

        macro_btns = QHBoxLayout()
        btn_rec_macro = QPushButton("⏺️ Record Macro")
        btn_rec_macro.setObjectName("PrimaryBtn")
        btn_rec_macro.clicked.connect(self.record_macro)

        btn_del_macro = QPushButton("❌ Delete Macro")
        btn_del_macro.setObjectName("SecondaryBtn")
        btn_del_macro.clicked.connect(self.delete_macro)

        macro_btns.addWidget(btn_rec_macro)
        macro_btns.addWidget(btn_del_macro)
        macro_btns.addStretch()
        macro_layout.addLayout(macro_btns)

        scroll_layout.addWidget(macro_card)

        # 3. Haptic Layer Vibration Feedback & Waveform Builder Card
        haptic_card = QFrame()
        haptic_card.setObjectName("GlassCard")
        haptic_layout = QVBoxLayout(haptic_card)

        lbl_haptic_title = QLabel("📳 SHIFT LAYER HAPTIC FEEDBACK ENGINE")
        lbl_haptic_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")
        haptic_layout.addWidget(lbl_haptic_title)

        self.chk_haptic_enable = QCheckBox("Enable Asynchronous Shift Transition Vibration Feedback")
        self.chk_haptic_enable.setChecked(True)
        self.chk_haptic_enable.stateChanged.connect(lambda s: self.save_opt("haptics", "enabled", s == Qt.CheckState.Checked.value))
        haptic_layout.addWidget(self.chk_haptic_enable)

        # Vibration Waveform Preview Canvas Widget
        lbl_wave = QLabel("Visual Vibration Waveform Timeline Preview:")
        lbl_wave.setStyleSheet("font-weight: bold; color: #a992cb;")
        haptic_layout.addWidget(lbl_wave)

        self.waveform_widget = HapticWaveformWidget()
        haptic_layout.addWidget(self.waveform_widget)

        # Building Block Controls
        hap_controls = QHBoxLayout()
        hap_controls.addWidget(QLabel("Motor:"))
        self.combo_motor = QComboBox()
        self.combo_motor.addItems(["BOTH (Left Heavy + Right Soft)", "LM (Left Heavy)", "RM (Right Soft)"])
        self.combo_motor.currentTextChanged.connect(self.on_haptic_params_changed)
        hap_controls.addWidget(self.combo_motor)

        hap_controls.addWidget(QLabel("Intensity (%):"))
        self.spin_int = QSpinBox()
        self.spin_int.setRange(0, 100)
        self.spin_int.setValue(80)
        self.spin_int.valueChanged.connect(self.on_haptic_params_changed)
        hap_controls.addWidget(self.spin_int)

        hap_controls.addWidget(QLabel("Duration (ms):"))
        self.spin_dur = QSpinBox()
        self.spin_dur.setRange(10, 2000)
        self.spin_dur.setValue(150)
        self.spin_dur.valueChanged.connect(self.on_haptic_params_changed)
        hap_controls.addWidget(self.spin_dur)

        btn_test_vib = QPushButton("📳 Test Vibration")
        btn_test_vib.setObjectName("PrimaryBtn")
        btn_test_vib.clicked.connect(self.test_vibration)

        hap_controls.addWidget(btn_test_vib)
        haptic_layout.addLayout(hap_controls)

        scroll_layout.addWidget(haptic_card)

        # 4. ViGEmBus Settings Card
        vigem_card = QFrame()
        vigem_card.setObjectName("GlassCard")
        vigem_layout = QVBoxLayout(vigem_card)

        lbl_vigem = QLabel("🎮 VIGEMBUS VIRTUAL CONTROLLER CONFIGURATION")
        lbl_vigem.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")
        vigem_layout.addWidget(lbl_vigem)

        grid_vigem = QGridLayout()
        grid_vigem.addWidget(QLabel("Target Virtual Slot:"), 0, 0)
        self.combo_target_slot = QComboBox()
        self.combo_target_slot.addItems(["Slot 1 (Auto-Assign)", "Slot 2", "Slot 3", "Slot 4"])
        self.combo_target_slot.currentTextChanged.connect(lambda t: self.save_opt("vigem", "slot", t))
        grid_vigem.addWidget(self.combo_target_slot, 0, 1)

        grid_vigem.addWidget(QLabel("Xbox Guide Button Remap Action:"), 1, 0)
        self.combo_guide_action = QComboBox()
        self.combo_guide_action.addItems(["Open Game Bar", "Take Screenshot", "Toggle Mute", "Disabled"])
        self.combo_guide_action.currentTextChanged.connect(lambda t: self.save_opt("vigem", "guide_action", t))
        grid_vigem.addWidget(self.combo_guide_action, 1, 1)

        vigem_layout.addLayout(grid_vigem)

        self.chk_rumble = QCheckBox("Enable Dual-Rumble Passthrough")
        self.chk_rumble.setChecked(True)
        self.chk_rumble.stateChanged.connect(lambda s: self.save_opt("vigem", "rumble_passthrough", s == Qt.CheckState.Checked.value))
        vigem_layout.addWidget(self.chk_rumble)

        scroll_layout.addWidget(vigem_card)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def on_haptic_params_changed(self):
        motor_str = self.combo_motor.currentText()
        lm = 1.0 if "LM" in motor_str or "BOTH" in motor_str else 0.0
        rm = 1.0 if "RM" in motor_str or "BOTH" in motor_str else 0.0
        intensity = self.spin_int.value() / 100.0
        duration = self.spin_dur.value()
        self.waveform_widget.set_haptic_waveform(lm * intensity, rm * intensity, duration)
        self.save_opt("haptics", "motor", motor_str)
        self.save_opt("haptics", "intensity", str(intensity))
        self.save_opt("haptics", "duration", str(duration))

    def add_chord_row(self, trigger="LB + SELECT", target="Virtual Paddle M1", suppress=True):
        row = self.table_chords.rowCount()
        self.table_chords.insertRow(row)

        self.table_chords.setItem(row, 0, QTableWidgetItem(trigger))
        self.table_chords.setItem(row, 1, QTableWidgetItem(target))

        chk = QCheckBox()
        chk.setChecked(suppress)
        chk.stateChanged.connect(self.save_hardware_chords)
        self.table_chords.setCellWidget(row, 2, chk)

        btn_del = QPushButton("❌ Delete")
        btn_del.setObjectName("SecondaryBtn")
        btn_del.clicked.connect(lambda ch=False, r=row: self.delete_chord_row(r))
        self.table_chords.setCellWidget(row, 3, btn_del)
        self.save_hardware_chords()

    def delete_chord_row(self, row):
        self.table_chords.removeRow(row)
        self.save_hardware_chords()

    def save_hardware_chords(self):
        chords_list = []
        for r in range(self.table_chords.rowCount()):
            t_item = self.table_chords.item(r, 0)
            a_item = self.table_chords.item(r, 1)
            chk_widget = self.table_chords.cellWidget(r, 2)
            if t_item and a_item:
                chords_list.append({
                    "trigger": t_item.text(),
                    "action": a_item.text(),
                    "suppress": chk_widget.isChecked() if chk_widget else True
                })
        config = getattr(self.app, 'daemon_config', None)
        if config:
            config.data["hardware_chords"] = chords_list
            self.app.save_config()

    def record_macro(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Record Macro")
        msg.setText("⏺️ Listening for macro key sequence... Press buttons in order, then click Stop.")
        msg.exec()

    def delete_macro(self):
        curr = self.combo_macros.currentText()
        if self.combo_macros.count() > 1:
            self.combo_macros.removeItem(self.combo_macros.currentIndex())
            QMessageBox.information(self, "Delete Macro", f"✓ Removed macro [{curr}].")

    def save_opt(self, section, option, val):
        config = getattr(self.app, 'daemon_config', None)
        if config:
            config.set(section, option, str(val))
            self.app.save_config()

    def load_config_values(self):
        config = getattr(self.app, 'daemon_config', None)
        if not config:
            return

        self.chk_haptic_enable.setChecked(config.getboolean("haptics", "enabled", True))
        self.chk_rumble.setChecked(config.getboolean("vigem", "rumble_passthrough", True))

        chords = config.data.get("hardware_chords", [])
        if chords:
            self.table_chords.setRowCount(0)
            for c in chords:
                self.add_chord_row(c.get("trigger", ""), c.get("action", ""), c.get("suppress", True))

    def test_vibration(self):
        lm = 1.0 if "LM" in self.combo_motor.currentText() or "BOTH" in self.combo_motor.currentText() else 0.0
        rm = 1.0 if "RM" in self.combo_motor.currentText() or "BOTH" in self.combo_motor.currentText() else 0.0
        intensity = self.spin_int.value() / 100.0
        duration = self.spin_dur.value()

        # Trigger real pattern if pad available
        vpad = getattr(self.app, 'virtual_pad', None)
        if vpad:
            haptic_engine.play_pattern(vpad, [(lm * intensity, rm * intensity, duration)])

        msg = QMessageBox(self)
        msg.setWindowTitle("Haptic Test")
        msg.setText(f"📳 Played Haptic Pulse: LM={lm*intensity:.2f}, RM={rm*intensity:.2f}, Duration={duration}ms")
        msg.exec()
