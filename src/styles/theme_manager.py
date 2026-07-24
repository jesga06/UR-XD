"""
Theme Manager module for PySide6 GUI (theme_manager.py)
Handles dynamic QSS stylesheet generation, theme presets (Purple, Blue, Green, Red, Yellow, Orange, White),
accent color customization, and font family overrides.
"""

import os
import json
import configparser

THEME_PRESETS = {
    "purple": {
        "name": "Purple (Default)",
        "base_bg": "#0c0914",
        "card_bg": "rgba(22, 16, 36, 0.85)",
        "card_border": "rgba(168, 85, 247, 0.25)",
        "card_hover_border": "rgba(168, 85, 247, 0.55)",
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
        "card_border": "rgba(56, 189, 248, 0.25)",
        "card_hover_border": "rgba(56, 189, 248, 0.55)",
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
        "card_border": "rgba(74, 222, 128, 0.25)",
        "card_hover_border": "rgba(74, 222, 128, 0.55)",
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
        "card_border": "rgba(248, 113, 113, 0.25)",
        "card_hover_border": "rgba(248, 113, 113, 0.55)",
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
        "card_border": "rgba(250, 204, 21, 0.25)",
        "card_hover_border": "rgba(250, 204, 21, 0.55)",
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
        "card_border": "rgba(251, 146, 60, 0.25)",
        "card_hover_border": "rgba(251, 146, 60, 0.55)",
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
        "card_border": "rgba(226, 232, 240, 0.25)",
        "card_hover_border": "rgba(226, 232, 240, 0.55)",
        "primary": "#64748b",
        "primary_hover": "#475569",
        "glow": "#e2e8f0",
        "accent_green": "#00f5a0",
        "text_main": "#f8fafc",
        "text_muted": "#94a3b8"
    }
}


class ThemeManager:
    """Manages active QSS themes, font families, and dynamic palette generation for PySide6."""

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
        if self.active_theme_key not in THEME_PRESETS:
            self.active_theme_key = "purple"

    def get_active_theme(self):
        return THEME_PRESETS.get(self.active_theme_key, THEME_PRESETS["purple"])

    def generate_qss(self, theme_key=None, font_family=None):
        if theme_key is None:
            theme_key = self.active_theme_key
        if font_family is None:
            font_family = self.font_family

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

        QPushButton#PrimaryBtn {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme['primary']}, stop:1 {theme['glow']});
            color: #ffffff;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 700;
            font-size: 13px;
        }}

        QPushButton#PrimaryBtn:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme['primary_hover']}, stop:1 {theme['primary']});
        }}

        QPushButton#SecondaryBtn {{
            background-color: rgba(255, 255, 255, 0.06);
            color: {theme['text_main']};
            border: 1px solid {theme['card_border']};
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 600;
        }}

        QPushButton#SecondaryBtn:hover {{
            background-color: rgba(255, 255, 255, 0.12);
            border: 1px solid {theme['card_hover_border']};
        }}

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
        }}

        QListWidget#SidebarNav::item:hover {{
            background-color: rgba(255, 255, 255, 0.05);
            color: {theme['text_main']};
        }}

        QListWidget#SidebarNav::item:selected {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme['primary']}, stop:1 {theme['glow']});
            color: #ffffff;
            font-weight: 700;
        }}

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
