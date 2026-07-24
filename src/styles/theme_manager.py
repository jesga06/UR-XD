"""
Theme Manager module for PySide6 GUI (theme_manager.py)
Handles dynamic QSS stylesheet generation, theme presets (Purple, Blue, Green, Red, Yellow, Orange, White),
accent RGBA glow calculation, system dark/light contrast auto-detection, font family overrides,
and sleek thin borders across all interactive buttons, dropdowns, spinboxes, and text inputs.
"""

import os
import json
import configparser
from PySide6.QtGui import QGuiApplication, QColor
from PySide6.QtCore import Qt

THEME_PRESETS = {
    "purple": {
        "name": "Purple (Default)",
        "base_bg": "#0c0914",
        "card_bg": "rgba(22, 16, 36, 0.85)",
        "card_border": "rgba(168, 85, 247, 0.35)",
        "card_hover_border": "rgba(168, 85, 247, 0.75)",
        "primary": "#7500ab",
        "primary_hover": "#8e00cf",
        "glow": "#a855f7",
        "accent_green": "#00f5a0",
        "text_main": "#f3e8ff",
        "text_muted": "#a992cb"
    },
    "blue": {
        "name": "Ocean Blue",
        "base_bg": "#08101e",
        "card_bg": "rgba(15, 28, 48, 0.85)",
        "card_border": "rgba(56, 189, 248, 0.35)",
        "card_hover_border": "rgba(56, 189, 248, 0.75)",
        "primary": "#0284c7",
        "primary_hover": "#0369a1",
        "glow": "#38bdf8",
        "accent_green": "#00f5a0",
        "text_main": "#e0f2fe",
        "text_muted": "#88aabf"
    },
    "green": {
        "name": "Cyber Green",
        "base_bg": "#08140c",
        "card_bg": "rgba(16, 36, 22, 0.85)",
        "card_border": "rgba(74, 222, 128, 0.35)",
        "card_hover_border": "rgba(74, 222, 128, 0.75)",
        "primary": "#16a34a",
        "primary_hover": "#15803d",
        "glow": "#4ade80",
        "accent_green": "#00f5a0",
        "text_main": "#dcfce7",
        "text_muted": "#86af94"
    },
    "red": {
        "name": "Crimson Red",
        "base_bg": "#140809",
        "card_bg": "rgba(36, 16, 18, 0.85)",
        "card_border": "rgba(248, 113, 113, 0.35)",
        "card_hover_border": "rgba(248, 113, 113, 0.75)",
        "primary": "#dc2626",
        "primary_hover": "#b91c1c",
        "glow": "#f87171",
        "accent_green": "#00f5a0",
        "text_main": "#fee2e2",
        "text_muted": "#b98e8e"
    },
    "yellow": {
        "name": "Solar Yellow",
        "base_bg": "#141208",
        "card_bg": "rgba(36, 32, 16, 0.85)",
        "card_border": "rgba(250, 204, 21, 0.35)",
        "card_hover_border": "rgba(250, 204, 21, 0.75)",
        "primary": "#ca8a04",
        "primary_hover": "#a16207",
        "glow": "#facc15",
        "accent_green": "#00f5a0",
        "text_main": "#fef9c3",
        "text_muted": "#b9ad78"
    },
    "orange": {
        "name": "Neon Orange",
        "base_bg": "#140c08",
        "card_bg": "rgba(36, 22, 16, 0.85)",
        "card_border": "rgba(251, 146, 60, 0.35)",
        "card_hover_border": "rgba(251, 146, 60, 0.75)",
        "primary": "#ea580c",
        "primary_hover": "#c2410c",
        "glow": "#fb923c",
        "accent_green": "#00f5a0",
        "text_main": "#ffedd5",
        "text_muted": "#b99480"
    },
    "white": {
        "name": "Monochrome Light Dark",
        "base_bg": "#111318",
        "card_bg": "rgba(30, 35, 45, 0.85)",
        "card_border": "rgba(226, 232, 240, 0.35)",
        "card_hover_border": "rgba(226, 232, 240, 0.75)",
        "primary": "#64748b",
        "primary_hover": "#475569",
        "glow": "#e2e8f0",
        "accent_green": "#00f5a0",
        "text_main": "#f8fafc",
        "text_muted": "#94a3b8"
    }
}


class ThemeManager:
    """Manages active QSS themes, RGBA glow calculations, OS system contrast detection, and fonts."""

    def __init__(self, config_path='config.ini'):
        self.config_path = config_path
        self.active_theme_key = "purple"
        self.font_family = "Inter"
        self.load_config()

    def load_config(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_path):
            try:
                config.read(self.config_path, encoding='utf-8')
                if 'UI' in config:
                    self.active_theme_key = config.get('UI', 'theme', fallback='purple').lower()
                    self.font_family = config.get('UI', 'font', fallback='Inter')
            except Exception:
                pass
        if self.active_theme_key == 'system':
            self.active_theme_key = self.detect_system_theme()
        elif self.active_theme_key not in THEME_PRESETS:
            self.active_theme_key = "purple"

    def detect_system_theme(self) -> str:
        """Detect OS system dark/light contrast mode."""
        try:
            app = QGuiApplication.instance()
            if app and hasattr(app, 'styleHints'):
                scheme = app.styleHints().colorScheme()
                if scheme == Qt.ColorScheme.Light:
                    return "white"
        except Exception:
            pass
        return "purple"

    def get_accent_glow_rgba(self, hex_color: str, alpha: float = 0.5) -> str:
        """Dynamically compute RGBA glow string from hex color."""
        c = QColor(hex_color)
        return f"rgba({c.red()}, {c.green()}, {c.blue()}, {alpha:.2f})"

    def get_active_theme(self):
        return THEME_PRESETS.get(self.active_theme_key, THEME_PRESETS["purple"])

    def generate_qss(self, theme_key=None, font_family=None):
        if theme_key is None:
            theme_key = self.active_theme_key
        if font_family is None:
            font_family = self.font_family

        if theme_key == "system":
            theme_key = self.detect_system_theme()

        theme = THEME_PRESETS.get(theme_key, THEME_PRESETS["purple"])

        qss = f"""
        /* Next-Gen Built Tomorrow Theme: {theme['name']} */
        QMainWindow, QDialog {{
            background-color: {theme['base_bg']};
            color: {theme['text_main']};
            font-family: "{font_family}", "Outfit", "Segoe UI", sans-serif;
        }}

        QWidget {{
            color: {theme['text_main']};
            font-family: "{font_family}", "Outfit", "Segoe UI", sans-serif;
        }}

        QFrame#GlassCard {{
            background-color: {theme['card_bg']};
            border: 1px solid {theme['card_border']};
            border-radius: 12px;
        }}

        QFrame#GlassCard:hover {{
            border: 1px solid {theme['card_hover_border']};
        }}

        QFrame#HeaderBar {{
            background-color: {theme['card_bg']};
            border-bottom: 1px solid {theme['card_border']};
            border-radius: 0px;
        }}

        /* Buttons with Sleek Thin Outlines */
        QPushButton {{
            border: 1px solid {theme['card_border']};
            border-radius: 8px;
            padding: 6px 14px;
            font-weight: 600;
            background-color: rgba(255, 255, 255, 0.05);
            color: {theme['text_main']};
        }}

        QPushButton:hover {{
            border: 1px solid {theme['card_hover_border']};
            background-color: rgba(255, 255, 255, 0.12);
        }}

        QPushButton#PrimaryBtn {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme['primary']}, stop:1 {theme['glow']});
            color: #ffffff;
            border: 1px solid {theme['card_hover_border']};
            border-radius: 8px;
            padding: 7px 16px;
            font-weight: 700;
            font-size: 13px;
        }}

        QPushButton#PrimaryBtn:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme['primary_hover']}, stop:1 {theme['primary']});
            border: 1px solid #ffffff;
        }}

        QPushButton#SecondaryBtn {{
            background-color: rgba(255, 255, 255, 0.06);
            color: {theme['text_main']};
            border: 1px solid {theme['card_border']};
            border-radius: 8px;
            padding: 7px 16px;
            font-weight: 600;
        }}

        QPushButton#SecondaryBtn:hover {{
            background-color: rgba(255, 255, 255, 0.12);
            border: 1px solid {theme['card_hover_border']};
        }}

        /* Dropdown Menus (QComboBox) with Thin Outlines */
        QComboBox {{
            background-color: rgba(16, 12, 28, 0.95);
            border: 1px solid {theme['card_border']};
            border-radius: 6px;
            padding: 5px 10px;
            color: {theme['text_main']};
            font-weight: 600;
        }}

        QComboBox:hover, QComboBox:focus {{
            border: 1px solid {theme['card_hover_border']};
            background-color: rgba(22, 16, 36, 0.95);
        }}

        QComboBox QAbstractItemView {{
            background-color: {theme['base_bg']};
            border: 1px solid {theme['card_hover_border']};
            selection-background-color: {theme['primary']};
            selection-color: #ffffff;
            color: {theme['text_main']};
            outline: none;
        }}

        /* Mandatory 1.5px Outlines Across EVERY Typable Text Box in the GUI */
        QLineEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{
            background-color: rgba(10, 7, 18, 0.95);
            border: 1.5px solid {theme['card_hover_border']};
            border-radius: 6px;
            padding: 6px 10px;
            color: {theme['text_main']};
            selection-background-color: {theme['primary']};
            selection-color: #ffffff;
        }}

        QLineEdit#OutlinedEdit {{
            background-color: rgba(0, 0, 0, 0.55);
            border: 1.5px solid {theme['card_hover_border']};
            border-radius: 6px;
            padding: 5px 8px;
            color: {theme['text_main']};
            selection-background-color: {theme['primary']};
            selection-color: #ffffff;
        }}

        QLineEdit:focus, QLineEdit:hover, QPlainTextEdit:focus, QPlainTextEdit:hover,
        QSpinBox:focus, QSpinBox:hover, QDoubleSpinBox:focus, QDoubleSpinBox:hover,
        QLineEdit#OutlinedEdit:focus, QLineEdit#OutlinedEdit:hover {{
            border: 1.5px solid {theme['glow']};
            background-color: rgba(0, 0, 0, 0.75);
        }}

        /* Table Cells and Cell Editors High-Contrast Outlines */
        QTableWidget QLineEdit {{
            background-color: rgba(12, 9, 20, 0.98);
            color: {theme['text_main']};
            border: 1.5px solid {theme['card_hover_border']};
            selection-background-color: {theme['primary']};
            selection-color: #ffffff;
        }}

        QTableWidget::item {{
            background-color: transparent;
            color: {theme['text_main']};
            selection-background-color: {theme['primary']};
            selection-color: #ffffff;
        }}

        /* Dynamic Theme QLabel Semantic Classes */
        QLabel#CardHeader {{
            font-weight: bold;
            font-size: 14px;
            color: {theme['text_main']};
        }}

        QLabel#AccentLabel {{
            font-weight: bold;
            color: {theme['glow']};
        }}

        QLabel#MutedLabel {{
            font-weight: 600;
            color: {theme['text_muted']};
        }}

        QLabel#SectionHeader {{
            font-weight: bold;
            font-size: 16px;
            color: {theme['text_main']};
        }}

        /* Sidebar Navigation List Items */
        QListWidget#SidebarNav {{
            background-color: transparent;
            border: none;
            outline: none;
        }}

        QListWidget#SidebarNav::item {{
            height: 48px;
            border-radius: 10px;
            padding-left: 12px;
            margin: 4px 8px;
            color: {theme['text_muted']};
            font-weight: 600;
            font-size: 14px;
            border: 1px solid transparent;
        }}

        QListWidget#SidebarNav::item:hover {{
            background-color: rgba(255, 255, 255, 0.05);
            color: {theme['text_main']};
            border: 1px solid {theme['card_border']};
        }}

        QListWidget#SidebarNav::item:selected {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme['primary']}, stop:1 {theme['glow']});
            color: #ffffff;
            font-weight: 700;
            border: 1px solid {theme['card_hover_border']};
        }}

        /* Sliders */
        QSlider::groove:horizontal {{
            height: 6px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
        }}

        QSlider::sub-page:horizontal {{
            background: {theme['primary']};
            border-radius: 3px;
        }}

        QSlider::handle:horizontal {{
            background: {theme['accent_green']};
            width: 18px;
            height: 18px;
            margin-top: -6px;
            margin-bottom: -6px;
            border-radius: 9px;
            border: 1px solid #ffffff;
        }}

        /* Tables (QTableWidget) with Thin Outlines */
        QTableWidget {{
            background-color: rgba(10, 7, 18, 0.85);
            border: 1px solid {theme['card_border']};
            border-radius: 8px;
            gridline-color: rgba(168, 85, 247, 0.2);
            color: {theme['text_main']};
        }}

        QHeaderView::section {{
            background-color: rgba(22, 16, 36, 0.95);
            color: {theme['text_muted']};
            font-weight: bold;
            border: 1px solid {theme['card_border']};
            padding: 6px;
        }}

        QProgressBar#TriggerBar {{
            background-color: rgba(255, 255, 255, 0.08);
            border: 1px solid {theme['card_border']};
            border-radius: 6px;
            text-align: center;
            color: #ffffff;
            font-weight: bold;
        }}

        QProgressBar#TriggerBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme['primary']}, stop:1 {theme['accent_green']});
            border-radius: 5px;
        }}

        QPlainTextEdit#LogConsole {{
            background-color: #07050b;
            color: {theme['text_muted']};
            font-family: "Fira Code", "Consolas", "JetBrains Mono", monospace;
            font-size: 12px;
            border: 1px solid {theme['card_border']};
            border-radius: 8px;
            padding: 8px;
        }}

        QToolTip {{
            background-color: {theme['base_bg']};
            color: {theme['text_main']};
            border: 1px solid {theme['glow']};
            border-radius: 6px;
            padding: 6px;
        }}
        """
        return qss
