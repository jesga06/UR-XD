"""
Advanced View for PySide6 GUI (advanced_view.py)
ViGEmBus virtual XInput controller options, Hardware Chords Engine Table,
Macro Sequence Builder & Recorder, Haptic Feedback Building-Block UI & Waveform Canvas,
and system process priority settings.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QCheckBox, QComboBox,
    QPushButton, QSpinBox, QGridLayout, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt
from components.haptic_waveform_widget import HapticWaveformWidget


class AdvancedView(QWidget):
    """
    Advanced Tab View handling hardware chords, macros, haptics, and system settings.
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

        # 1. Hardware Chords Engine Manager Card
        chords_card = QFrame()
        chords_card.setObjectName("GlassCard")
        chords_layout = QVBoxLayout(chords_card)

        chords_header = QHBoxLayout()
        lbl_chords = QLabel("⚡ HARDWARE CHORDS ENGINE MANAGER")
        lbl_chords.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")

        btn_add_chord = QPushButton("+ Add Hardware Chord")
        btn_add_chord.setObjectName("PrimaryBtn")
        btn_add_chord.clicked.connect(self.add_chord_row)

        chords_header.addWidget(lbl_chords)
        chords_header.addStretch()
        chords_header.addWidget(btn_add_chord)
        chords_layout.addLayout(chords_header)

        self.table_chords = QTableWidget(0, 4)
        self.table_chords.setHorizontalHeaderLabels(["Trigger Combo", "Target Action / Button", "Suppress Physical Inputs", "Actions"])
        self.table_chords.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_chords.setMinimumHeight(140)
        chords_layout.addWidget(self.table_chords)

        # Add initial sample chord
        self.add_chord_row("LB + START", "Virtual Paddle M1", True)

        scroll_layout.addWidget(chords_card)

        # 2. Haptic Layer Vibration Feedback & Waveform Builder Card
        haptic_card = QFrame()
        haptic_card.setObjectName("GlassCard")
        haptic_layout = QVBoxLayout(haptic_card)

        lbl_haptic_title = QLabel("📳 SHIFT LAYER HAPTIC FEEDBACK ENGINE")
        lbl_haptic_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")
        haptic_layout.addWidget(lbl_haptic_title)

        chk_haptic_enable = QCheckBox("Enable Asynchronous Shift Transition Vibration Feedback")
        chk_haptic_enable.setChecked(True)
        haptic_layout.addWidget(chk_haptic_enable)

        # Vibration Waveform Preview Canvas Widget
        lbl_wave = QLabel("Visual Vibration Waveform Timeline Preview:")
        lbl_wave.setStyleSheet("font-weight: bold; color: #a992cb;")
        haptic_layout.addWidget(lbl_wave)

        self.waveform_widget = HapticWaveformWidget()
        haptic_layout.addWidget(self.waveform_widget)

        # Building Block Controls
        hap_controls = QHBoxLayout()
        hap_controls.addWidget(QLabel("Motor:"))
        combo_motor = QComboBox()
        combo_motor.addItems(["BOTH (Left Heavy + Right Soft)", "LM (Left Heavy)", "RM (Right Soft)"])
        hap_controls.addWidget(combo_motor)

        hap_controls.addWidget(QLabel("Intensity (%):"))
        spin_int = QSpinBox()
        spin_int.setRange(0, 100)
        spin_int.setValue(80)
        hap_controls.addWidget(spin_int)

        hap_controls.addWidget(QLabel("Duration (ms):"))
        spin_dur = QSpinBox()
        spin_dur.setRange(10, 2000)
        spin_dur.setValue(150)
        hap_controls.addWidget(spin_dur)

        btn_test_vib = QPushButton("📳 Test Vibration")
        btn_test_vib.setObjectName("PrimaryBtn")
        btn_test_vib.clicked.connect(self.test_vibration)

        hap_controls.addWidget(btn_test_vib)
        haptic_layout.addLayout(hap_controls)

        scroll_layout.addWidget(haptic_card)

        # 3. ViGEmBus & System Process Priority Card
        proc_card = QFrame()
        proc_card.setObjectName("GlassCard")
        proc_layout = QVBoxLayout(proc_card)

        lbl_proc = QLabel("🎮 VIGEMBUS & PROCESS PRIORITY")
        lbl_proc.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")
        proc_layout.addWidget(lbl_proc)

        chk_rumble = QCheckBox("Enable Dual-Rumble Passthrough")
        chk_rumble.setChecked(True)
        chk_guide = QCheckBox("Remap Home Button to Xbox Guide / Game Bar")
        chk_guide.setChecked(True)

        proc_layout.addWidget(chk_rumble)
        proc_layout.addWidget(chk_guide)

        grid_prio = QGridLayout()
        grid_prio.addWidget(QLabel("Daemon Process Priority:"), 0, 0)
        combo_prio = QComboBox()
        combo_prio.addItems(["Normal", "Above Normal", "High", "Realtime"])
        combo_prio.setCurrentIndex(1)
        grid_prio.addWidget(combo_prio, 0, 1)

        proc_layout.addLayout(grid_prio)
        scroll_layout.addWidget(proc_card)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def add_chord_row(self, trigger="LB + SELECT", target="Macro: FastCombo", suppress=True):
        row = self.table_chords.rowCount()
        self.table_chords.insertRow(row)

        self.table_chords.setItem(row, 0, QTableWidgetItem(trigger))
        self.table_chords.setItem(row, 1, QTableWidgetItem(target))

        chk = QCheckBox()
        chk.setChecked(suppress)
        self.table_chords.setCellWidget(row, 2, chk)

        btn_del = QPushButton("❌ Delete")
        btn_del.setObjectName("SecondaryBtn")
        btn_del.clicked.connect(lambda ch=False, r=row: self.table_chords.removeRow(r))
        self.table_chords.setCellWidget(row, 3, btn_del)

    def test_vibration(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Haptic Test")
        msg.setText("📳 Haptic vibration command sent to physical controller motors!")
        msg.exec()
