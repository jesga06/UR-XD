"""
Dynamic Theme Engine and Color Token Manager for PySide6 UI.
Manages active theme tokens (accent_1, accent_2, background), dynamic QSS generation,
hex with alpha parsing, JSON theme import/export, and persistence sync with config.ini.
"""

import os
import json
import re
import configparser
import logging
from typing import Dict, Any, Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor

logger = logging.getLogger("theme_manager")

DEFAULT_TOKENS: Dict[str, str] = {
    "accent_1": "#A855F7FF",   # Input Color (Physical/hardware visualizers)
    "accent_2": "#00F5A0FF",   # Output Color (Virtual/emulated output visualizers)
    "background": "#0C0914FF"  # Base Background (Window base, card fill, containers)
}

CUSTOM_THEME_RELATIVE_PATH = os.path.join("themes", "custom_theme.json")
CONFIG_INI_PATH = "config.ini"


def normalize_hex8(hex_str: str, default: str = "#FFFFFFFF") -> str:
    """
    Normalizes a color string to a valid 8-character uppercase hex string formatted as #RRGGBBAA.
    Supports #RGB, #RGBA, #RRGGBB, and #RRGGBBAA formats.
    """
    if not isinstance(hex_str, str):
        return default

    cleaned = hex_str.strip().lstrip("#").upper()

    if len(cleaned) == 3:  # RGB -> RRGGBBFF
        cleaned = "".join([c * 2 for c in cleaned]) + "FF"
    elif len(cleaned) == 4:  # RGBA -> RRGGBBAA
        cleaned = "".join([c * 2 for c in cleaned])
    elif len(cleaned) == 6:  # RRGGBB -> RRGGBBFF
        cleaned = cleaned + "FF"
    elif len(cleaned) == 8:  # RRGGBBAA
        pass
    else:
        return default

    if not re.match(r"^[0-9A-F]{8}$", cleaned):
        return default

    return f"#{cleaned}"


def hex8_to_color(hex_str: str) -> QColor:
    """
    Converts an 8-character hex string (#RRGGBBAA) to a PySide6 QColor object.
    """
    normalized = normalize_hex8(hex_str)
    r = int(normalized[1:3], 16)
    g = int(normalized[3:5], 16)
    b = int(normalized[5:7], 16)
    a = int(normalized[7:9], 16)
    return QColor(r, g, b, a)


def color_to_hex8(color: QColor) -> str:
    """
    Converts a PySide6 QColor object to an 8-character uppercase hex string (#RRGGBBAA).
    """
    return f"#{color.red():02X}{color.green():02X}{color.blue():02X}{color.alpha():02X}"


def color_to_rgba_str(color: QColor, alpha_override: Optional[float] = None) -> str:
    """
    Formats a QColor as a CSS rgba(R, G, B, A) string.
    alpha_override (0.0 to 1.0) can override the color's native alpha channel.
    """
    alpha = alpha_override if alpha_override is not None else color.alphaF()
    alpha = max(0.0, min(1.0, float(alpha)))
    return f"rgba({color.red()}, {color.green()}, {color.blue()}, {alpha:.2f})"


class ThemeManager(QObject):
    """
    Central singleton service for dynamic UI color tokens and QSS generation.
    Emits theme_changed(dict) whenever theme tokens are updated.
    """
    theme_changed = Signal(dict)
    _instance: Optional["ThemeManager"] = None

    @classmethod
    def get_instance(cls) -> "ThemeManager":
        """Returns the shared singleton instance of ThemeManager."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        # Prevent multiple instance binding if singleton accessed
        if ThemeManager._instance is None:
            ThemeManager._instance = self

        self.tokens: Dict[str, str] = DEFAULT_TOKENS.copy()
        self._load_saved_theme()

    def get_color(self, key: str, alpha_override: Optional[float] = None) -> QColor:
        """
        Returns a PySide6 QColor object for the specified token key.
        Falls back to default token if key is missing.
        """
        hex_val = self.tokens.get(key, DEFAULT_TOKENS.get(key, "#FFFFFFFF"))
        color = hex8_to_color(hex_val)
        if alpha_override is not None:
            a_int = int(max(0.0, min(1.0, float(alpha_override))) * 255)
            color.setAlpha(a_int)
        return color

    def get_rgba_str(self, key: str, alpha_override: Optional[float] = None) -> str:
        """
        Returns a CSS rgba(R, G, B, A) string for the specified token key.
        """
        color = self.get_color(key)
        return color_to_rgba_str(color, alpha_override=alpha_override)

    def get_token(self, key: str) -> str:
        """
        Returns the normalized 8-character hex string for the specified token key.
        """
        return self.tokens.get(key, DEFAULT_TOKENS.get(key, "#FFFFFFFF"))

    def set_token(self, key: str, hex_color: str) -> None:
        """
        Updates a single theme token and notifies subscribers via theme_changed signal.
        Automatically saves persistent theme and syncs with config.ini.
        """
        normalized = normalize_hex8(hex_color, default=self.tokens.get(key, "#FFFFFFFF"))
        self.tokens[key] = normalized
        self._save_custom_theme()
        self._sync_config_ini()
        self.theme_changed.emit(self.tokens.copy())

    def reset_defaults(self) -> None:
        """
        Restores default system theme tokens (#A855F7FF, #00F5A0FF, #0C0914FF).
        """
        self.tokens = DEFAULT_TOKENS.copy()
        self._save_custom_theme()
        self._sync_config_ini()
        self.theme_changed.emit(self.tokens.copy())

    def import_theme(self, json_path: str) -> bool:
        """
        Imports theme tokens from a JSON file.
        Backward compatible: if missing keys, keeps existing or default values.
        """
        if not os.path.exists(json_path):
            logger.error(f"Cannot import theme: file does not exist ({json_path})")
            return False

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                logger.error(f"Invalid theme format in {json_path}")
                return False

            updated = False
            for k in DEFAULT_TOKENS.keys():
                if k in data:
                    self.tokens[k] = normalize_hex8(str(data[k]), default=self.tokens[k])
                    updated = True

            if updated:
                self._save_custom_theme()
                self._sync_config_ini(custom_path=json_path)
                self.theme_changed.emit(self.tokens.copy())
                logger.info(f"Successfully imported theme from {json_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to import theme from {json_path}: {e}")
            return False

    def export_theme(self, json_path: str) -> bool:
        """
        Exports active theme tokens to a JSON file.
        """
        try:
            dir_name = os.path.dirname(json_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(self.tokens, f, indent=4)
            logger.info(f"Successfully exported theme to {json_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export theme to {json_path}: {e}")
            return False

    def generate_qss(self) -> str:
        """
        Generates application-wide QSS style sheet dynamically based on current color tokens.
        Card background uses background with ~85% alpha.
        Borders and accents use accent_1 with 35% opacity or full accent_1.
        Accent #2 is used for output highlights, success states, and secondary glowing elements.
        """
        bg_color = self.get_color("background")
        accent_1 = self.get_color("accent_1")
        accent_2 = self.get_color("accent_2")

        bg_solid = color_to_rgba_str(bg_color, alpha_override=1.0)
        bg_glass = color_to_rgba_str(bg_color, alpha_override=0.85)
        bg_card_inner = color_to_rgba_str(bg_color, alpha_override=0.60)

        border_glass = color_to_rgba_str(accent_1, alpha_override=0.35)
        border_hover = color_to_rgba_str(accent_1, alpha_override=0.70)

        accent_1_hex = color_to_hex8(accent_1)
        accent_1_rgba = color_to_rgba_str(accent_1, alpha_override=1.0)
        accent_1_subtle = color_to_rgba_str(accent_1, alpha_override=0.20)

        accent_2_hex = color_to_hex8(accent_2)
        accent_2_rgba = color_to_rgba_str(accent_2, alpha_override=1.0)

        return f"""
/* Global Base Window & Widgets */
QMainWindow, QDialog, QWidget#main_container {{
    background-color: {bg_solid};
    color: #ffffff;
    font-family: "Inter", "Outfit", "Segoe UI", sans-serif;
}}

/* Glassmorphic Card Containers */
QFrame.glass-card, QFrame#glass_card, QFrame.theme-card {{
    background-color: {bg_glass};
    border: 1px solid {border_glass};
    border-radius: 12px;
}}

/* Dynamic High-Contrast Text Fields & Inputs */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background-color: {bg_glass};
    border: 1.5px solid {accent_1_rgba};
    color: #ffffff;
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: {accent_1_subtle};
}}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border: 2px solid {accent_2_rgba};
}}

QLineEdit::placeholder {{
    color: rgba(255, 255, 255, 0.55);
    font-style: italic;
}}

/* Interactive Buttons */
QPushButton.accent-btn, QPushButton#action_btn {{
    background-color: {accent_1_subtle};
    border: 1px solid {border_hover};
    color: #ffffff;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: bold;
}}

QPushButton.accent-btn:hover, QPushButton#action_btn:hover {{
    background-color: {color_to_rgba_str(accent_1, alpha_override=0.40)};
    border: 1px solid {accent_1_hex};
}}

QPushButton.accent-btn:pressed, QPushButton#action_btn:pressed {{
    background-color: {color_to_rgba_str(accent_1, alpha_override=0.60)};
}}

QPushButton.secondary-btn {{
    background-color: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.20);
    color: #ffffff;
    border-radius: 6px;
    padding: 6px 12px;
}}

QPushButton.secondary-btn:hover {{
    background-color: rgba(255, 255, 255, 0.15);
}}

/* Checkboxes */
QCheckBox {{
    color: #ffffff;
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1.5px solid {border_hover};
    background-color: {bg_card_inner};
}}

QCheckBox::indicator:checked {{
    background-color: {accent_1_rgba};
    border: 1.5px solid {accent_1_hex};
}}

/* Horizontal Sliders */
QSlider::groove:horizontal {{
    height: 6px;
    background: {bg_card_inner};
    border: 1px solid {border_glass};
    border-radius: 3px;
}}

QSlider::sub-page:horizontal {{
    background: {accent_2_rgba};
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background: {accent_2_rgba};
    border: 2px solid #ffffff;
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}}

QSlider::handle:horizontal:hover {{
    background: #ffffff;
    border: 2px solid {accent_2_rgba};
}}

/* Labels & Headers */
QLabel {{
    color: #ffffff;
}}

QLabel.muted {{
    color: rgba(255, 255, 255, 0.65);
}}

QLabel.accent-header {{
    color: {accent_1_hex};
    font-weight: bold;
}}

QLabel.output-header {{
    color: {accent_2_hex};
    font-weight: bold;
}}
"""

    def _load_saved_theme(self) -> None:
        """Loads persistent custom theme if available."""
        if os.path.exists(CUSTOM_THEME_RELATIVE_PATH):
            try:
                with open(CUSTOM_THEME_RELATIVE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    for k in DEFAULT_TOKENS.keys():
                        if k in data:
                            self.tokens[k] = normalize_hex8(str(data[k]), default=DEFAULT_TOKENS[k])
            except Exception as e:
                logger.warning(f"Could not load custom theme from {CUSTOM_THEME_RELATIVE_PATH}: {e}")

    def _save_custom_theme(self) -> None:
        """Saves current tokens to themes/custom_theme.json."""
        try:
            os.makedirs("themes", exist_ok=True)
            with open(CUSTOM_THEME_RELATIVE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.tokens, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save custom theme: {e}")

    def _sync_config_ini(self, custom_path: Optional[str] = None) -> None:
        """Syncs active theme settings with config.ini under [UI] section."""
        config = configparser.ConfigParser()
        if os.path.exists(CONFIG_INI_PATH):
            try:
                config.read(CONFIG_INI_PATH, encoding="utf-8")
            except Exception as e:
                logger.warning(f"Could not read config.ini: {e}")

        if "UI" not in config.sections():
            config.add_section("UI")

        config.set("UI", "theme_path", custom_path or CUSTOM_THEME_RELATIVE_PATH)
        config.set("UI", "accent_1", self.tokens.get("accent_1", "#A855F7FF"))
        config.set("UI", "accent_2", self.tokens.get("accent_2", "#00F5A0FF"))
        config.set("UI", "background", self.tokens.get("background", "#0C0914FF"))

        try:
            with open(CONFIG_INI_PATH, "w", encoding="utf-8") as f:
                config.write(f)
        except Exception as e:
            logger.error(f"Failed to sync config.ini with theme settings: {e}")
