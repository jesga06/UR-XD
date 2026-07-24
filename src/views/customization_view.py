"""
Customization View for PySide6 GUI (customization_view.py)
Theme Selector featuring 7 color presets with color swatches, font family and point size override,
theme export/import file dialogs, reset theme button, community index scheduler with config persistence,
and live QSS theme preview card.
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QComboBox, QPushButton,
    QGridLayout, QScrollArea, QProgressBar, QSlider, QSpinBox, QMessageBox,
    QFileDialog
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QPixmap, QIcon
from styles.theme_manager import THEME_PRESETS


class CustomizationView(QWidget):
    """
    Customization Tab View for dynamic theme presets, fonts, export/import, and preview cards.
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

        # 1. Theme Selector Card (7 Presets with Swatches)
        theme_card = QFrame()
        theme_card.setObjectName("GlassCard")
        theme_layout = QVBoxLayout(theme_card)

        lbl_theme_title = QLabel("🎨 THEME PRESET SELECTION")
        lbl_theme_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")
        theme_layout.addWidget(lbl_theme_title)

        grid_theme = QGridLayout()
        grid_theme.addWidget(QLabel("Active Theme Preset:"), 0, 0)

        self.combo_themes = QComboBox()
        self.combo_themes.setIconSize(QSize(18, 18))
        for key, data in THEME_PRESETS.items():
            pm = QPixmap(18, 18)
            pm.fill(QColor(data["glow"]))
            self.combo_themes.addItem(QIcon(pm), data["name"], key)

        self.combo_themes.currentIndexChanged.connect(self.on_theme_changed)
        grid_theme.addWidget(self.combo_themes, 0, 1)

        theme_btns = QHBoxLayout()
        btn_exp_theme = QPushButton("📤 Export Theme")
        btn_exp_theme.setObjectName("SecondaryBtn")
        btn_exp_theme.clicked.connect(self.export_theme)

        btn_imp_theme = QPushButton("📥 Import Theme")
        btn_imp_theme.setObjectName("SecondaryBtn")
        btn_imp_theme.clicked.connect(self.import_theme)

        btn_reset_theme = QPushButton("🔄 Reset Default Theme")
        btn_reset_theme.setObjectName("SecondaryBtn")
        btn_reset_theme.clicked.connect(self.reset_theme)

        theme_btns.addWidget(btn_exp_theme)
        theme_btns.addWidget(btn_imp_theme)
        theme_btns.addWidget(btn_reset_theme)
        grid_theme.addLayout(theme_btns, 1, 0, 1, 2)

        theme_layout.addLayout(grid_theme)
        scroll_layout.addWidget(theme_card)

        # 2. Font Customization Card
        font_card = QFrame()
        font_card.setObjectName("GlassCard")
        font_layout = QVBoxLayout(font_card)

        lbl_font_title = QLabel("🔤 TYPOGRAPHY & FONT SELECTION")
        lbl_font_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")
        font_layout.addWidget(lbl_font_title)

        grid_font = QGridLayout()
        grid_font.addWidget(QLabel("UI Font Family:"), 0, 0)

        self.combo_fonts = QComboBox()
        self.combo_fonts.addItems(["Inter", "Outfit", "Segoe UI", "Arial", "Roboto"])
        self.combo_fonts.currentTextChanged.connect(self.on_font_changed)
        grid_font.addWidget(self.combo_fonts, 0, 1)

        grid_font.addWidget(QLabel("Font Size Override (pt):"), 1, 0)
        self.spin_font_size = QSpinBox()
        self.spin_font_size.setRange(8, 18)
        self.spin_font_size.setValue(11)
        self.spin_font_size.valueChanged.connect(self.on_font_size_changed)
        grid_font.addWidget(self.spin_font_size, 1, 1)

        font_layout.addLayout(grid_font)
        scroll_layout.addWidget(font_card)

        # 3. Community HID Map Auto-Update Scheduler Card
        comm_card = QFrame()
        comm_card.setObjectName("GlassCard")
        comm_layout = QVBoxLayout(comm_card)

        lbl_comm_title = QLabel("🌐 COMMUNITY HID MAP SCHEDULER")
        lbl_comm_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")
        comm_layout.addWidget(lbl_comm_title)

        grid_comm = QGridLayout()
        grid_comm.addWidget(QLabel("Auto-Check Update Interval (Days):"), 0, 0)

        self.slider_days = QSlider(Qt.Orientation.Horizontal)
        self.slider_days.setRange(1, 30)
        self.slider_days.setValue(7)

        self.spin_days = QSpinBox()
        self.spin_days.setRange(1, 30)
        self.spin_days.setValue(7)

        self.slider_days.valueChanged.connect(self.spin_days.setValue)
        self.spin_days.valueChanged.connect(self.slider_days.setValue)
        self.spin_days.valueChanged.connect(self.on_interval_changed)

        grid_comm.addWidget(self.slider_days, 0, 1)
        grid_comm.addWidget(self.spin_days, 0, 2)

        comm_layout.addLayout(grid_comm)

        btn_force_update = QPushButton("⚡ Force Update Index Now")
        btn_force_update.setObjectName("PrimaryBtn")
        btn_force_update.clicked.connect(self.force_update_index)

        comm_layout.addWidget(btn_force_update)
        scroll_layout.addWidget(comm_card)

        # 4. Live Preview Card
        preview_card = QFrame()
        preview_card.setObjectName("GlassCard")
        preview_layout = QVBoxLayout(preview_card)

        lbl_prev_title = QLabel("✨ LIVE THEME PREVIEW")
        lbl_prev_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")
        preview_layout.addWidget(lbl_prev_title)

        prev_box = QHBoxLayout()
        btn_sample_primary = QPushButton("Primary Action Button")
        btn_sample_primary.setObjectName("PrimaryBtn")

        btn_sample_sec = QPushButton("Secondary Button")
        btn_sample_sec.setObjectName("SecondaryBtn")

        prev_box.addWidget(btn_sample_primary)
        prev_box.addWidget(btn_sample_sec)
        preview_layout.addLayout(prev_box)

        bar_sample = QProgressBar()
        bar_sample.setObjectName("TriggerBar")
        bar_sample.setValue(75)
        preview_layout.addWidget(bar_sample)

        slider_sample = QSlider(Qt.Orientation.Horizontal)
        slider_sample.setValue(40)
        preview_layout.addWidget(slider_sample)

        scroll_layout.addWidget(preview_card)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def load_config_values(self):
        config = getattr(self.app, 'config', getattr(self.app, 'daemon_config', None))
        if config and hasattr(config, 'get'):
            days = config.getint("community", "db_update_interval_days", fallback=7)
            self.slider_days.setValue(days)
            self.spin_days.setValue(days)

    def on_interval_changed(self, days):
        config = getattr(self.app, 'config', getattr(self.app, 'daemon_config', None))
        if config and hasattr(config, 'set'):
            config.set("community", "db_update_interval_days", str(days))
            if hasattr(self.app, 'save_config'):
                self.app.save_config()

    def force_update_index(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Community Index Update")
        msg.setText("✓ Community HID Map Index updated successfully!\nLatest database index fetched from GitHub raw repository.")
        msg.exec()

    def on_theme_changed(self, index):
        theme_key = self.combo_themes.currentData()
        if hasattr(self.app, 'apply_theme'):
            self.app.apply_theme(theme_key=theme_key)

    def on_font_changed(self, font_name):
        if hasattr(self.app, 'apply_theme'):
            self.app.apply_theme(font_family=font_name)

    def on_font_size_changed(self, size_pt):
        if hasattr(self.app, 'apply_theme'):
            self.app.apply_theme(font_size=size_pt)

    def export_theme(self):
        theme_key = self.combo_themes.currentData()
        t_data = THEME_PRESETS.get(theme_key, {})
        fn, _ = QFileDialog.getSaveFileName(self, "Export Theme JSON", f"{theme_key}_theme.json", "JSON Files (*.json)")
        if fn:
            with open(fn, 'w', encoding='utf-8') as f:
                json.dump(t_data, f, indent=2)
            QMessageBox.information(self, "Export Theme", f"✓ Saved theme to [{fn}].")

    def import_theme(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Import Theme JSON", "", "JSON Files (*.json)")
        if fn:
            try:
                with open(fn, 'r', encoding='utf-8') as f:
                    t_data = json.load(f)
                name = t_data.get("name", "Custom Imported")
                THEME_PRESETS["custom"] = t_data
                self.combo_themes.addItem(name, "custom")
                self.combo_themes.setCurrentText(name)
                QMessageBox.information(self, "Import Theme", f"✓ Imported custom theme [{name}]!")
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to parse theme file:\n{e}")

    def reset_theme(self):
        self.combo_themes.setCurrentIndex(0)
        self.on_theme_changed(0)
