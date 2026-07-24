"""
Customization View for PySide6 GUI (customization_view.py)
Theme Selector featuring 7 color presets (Purple, Blue, Green, Red, Yellow, Orange, White),
accent color picker, font family selector, and live QSS theme preview card.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QComboBox, QPushButton,
    QGridLayout, QScrollArea, QProgressBar
)
from PySide6.QtCore import Qt
from styles.theme_manager import THEME_PRESETS


class CustomizationView(QWidget):
    """
    Customization Tab View for dynamic theme preset switching and UI styling.
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

        # 1. Theme Selector Card (7 Presets)
        theme_card = QFrame()
        theme_card.setObjectName("GlassCard")
        theme_layout = QVBoxLayout(theme_card)

        lbl_theme_title = QLabel("🎨 THEME PRESET SELECTION")
        lbl_theme_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")
        theme_layout.addWidget(lbl_theme_title)

        grid_theme = QGridLayout()
        grid_theme.addWidget(QLabel("Active Theme Preset:"), 0, 0)

        self.combo_themes = QComboBox()
        for key, data in THEME_PRESETS.items():
            self.combo_themes.addItem(data["name"], key)

        self.combo_themes.currentIndexChanged.connect(self.on_theme_changed)
        grid_theme.addWidget(self.combo_themes, 0, 1)

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

        font_layout.addLayout(grid_font)
        scroll_layout.addWidget(font_card)

        # 3. Live Preview Card
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

        scroll_layout.addWidget(preview_card)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def on_theme_changed(self, index):
        theme_key = self.combo_themes.currentData()
        if hasattr(self.app, 'apply_theme'):
            self.app.apply_theme(theme_key=theme_key)

    def on_font_changed(self, font_name):
        if hasattr(self.app, 'apply_theme'):
            self.app.apply_theme(font_family=font_name)
