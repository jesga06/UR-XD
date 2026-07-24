"""
Advanced View for PySide6 GUI (advanced_view.py)
ViGEmBus virtual XInput controller options, backend parameters, process priority,
system startup settings, and single-instance socket port controls.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QCheckBox, QComboBox,
    QPushButton, QSpinBox, QGridLayout, QScrollArea
)
from PySide6.QtCore import Qt


class AdvancedView(QWidget):
    """
    Advanced Tab View for system, driver, and process configuration.
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

        # 1. ViGEmBus Virtual Controller Card
        vigem_card = QFrame()
        vigem_card.setObjectName("GlassCard")
        vigem_layout = QVBoxLayout(vigem_card)

        lbl_vigem = QLabel("🎮 VIGEMBUS VIRTUAL PAD SETTINGS")
        lbl_vigem.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")
        vigem_layout.addWidget(lbl_vigem)

        chk_rumble = QCheckBox("Enable Dual-Rumble Passthrough")
        chk_rumble.setChecked(True)
        chk_guide = QCheckBox("Remap Home Button to Xbox Guide / Game Bar")
        chk_guide.setChecked(True)

        vigem_layout.addWidget(chk_rumble)
        vigem_layout.addWidget(chk_guide)

        grid_slot = QGridLayout()
        grid_slot.addWidget(QLabel("Target Xbox Controller Slot:"), 0, 0)
        combo_slot = QComboBox()
        combo_slot.addItems(["Auto (Slot 1)", "Slot 2", "Slot 3", "Slot 4"])
        grid_slot.addWidget(combo_slot, 0, 1)

        vigem_layout.addLayout(grid_slot)
        scroll_layout.addWidget(vigem_card)

        # 2. Process & Single Instance Lock Card
        proc_card = QFrame()
        proc_card.setObjectName("GlassCard")
        proc_layout = QVBoxLayout(proc_card)

        lbl_proc = QLabel("⚙️ SYSTEM & PROCESS SETTINGS")
        lbl_proc.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")
        proc_layout.addWidget(lbl_proc)

        chk_autostart = QCheckBox("Launch Wrapper Daemon on System Startup")
        chk_single = QCheckBox("Enforce Single Instance Port Guard (Port 65433)")
        chk_single.setChecked(True)

        proc_layout.addWidget(chk_autostart)
        proc_layout.addWidget(chk_single)

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
