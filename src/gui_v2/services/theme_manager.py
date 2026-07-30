"""
Dynamic Theme Engine and Color Token Manager for PySide6 UI.
Manages active theme tokens (accent_1, accent_2, background), dynamic QSS generation,
hex with alpha parsing, JSON theme import/export, preset theme discovery, theme CRUD,
and persistence sync with config.ini.
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
    "background": "#0C0914FF", # Widget/Card Base Background
    "window_bg": "#000000FF"   # Window Canvas Base Background (Pure Black)
}

CUSTOM_THEME_RELATIVE_PATH = os.path.join("themes", "custom_theme.json")
PRESETS_DIR = os.path.join("themes", "presets")
USER_THEMES_DIR = os.path.join("themes", "user")
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


def sanitize_filename(name: str) -> str:
    """Sanitizes a string to be a safe filename."""
    cleaned = re.sub(r'[^a-zA-Z0-9_\- ]', '', name).strip()
    cleaned = cleaned.replace(' ', '_').lower()
    return cleaned or "custom_theme"


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
        if ThemeManager._instance is None:
            ThemeManager._instance = self

        self.tokens: Dict[str, str] = DEFAULT_TOKENS.copy()
        self.active_theme_name: str = "Default Neon Purple"
        self._ensure_theme_directories()
        self._load_saved_theme()

    def _ensure_theme_directories(self):
        """Creates themes, themes/presets, and themes/user directories if missing."""
        os.makedirs("themes", exist_ok=True)
        os.makedirs(PRESETS_DIR, exist_ok=True)
        os.makedirs(USER_THEMES_DIR, exist_ok=True)

    def get_color(self, key: str, alpha_override: Optional[float] = None) -> QColor:
        """Returns a QColor object for specified key."""
        hex_val = self.tokens.get(key, DEFAULT_TOKENS.get(key, "#FFFFFFFF"))
        color = hex8_to_color(hex_val)
        if alpha_override is not None:
            a_int = int(max(0.0, min(1.0, float(alpha_override))) * 255)
            color.setAlpha(a_int)
        return color

    def get_rgba_str(self, key: str, alpha_override: Optional[float] = None) -> str:
        """Returns CSS rgba(R, G, B, A) string for specified key."""
        color = self.get_color(key)
        return color_to_rgba_str(color, alpha_override=alpha_override)

    def get_token(self, key: str) -> str:
        """Returns normalized 8-character hex string for specified key."""
        return self.tokens.get(key, DEFAULT_TOKENS.get(key, "#FFFFFFFF"))

    def set_token(self, key: str, hex_color: str) -> None:
        """Updates a single token and notifies subscribers."""
        normalized = normalize_hex8(hex_color, default=self.tokens.get(key, "#FFFFFFFF"))
        self.tokens[key] = normalized
        self._save_custom_theme()
        self._sync_config_ini()
        self.theme_changed.emit(self.tokens.copy())

    def reset_defaults(self) -> None:
        """Restores default system theme tokens (#A855F7FF, #00F5A0FF, #0C0914FF)."""
        self.tokens = DEFAULT_TOKENS.copy()
        self.active_theme_name = "Default Neon Purple"
        self._save_custom_theme()
        self._sync_config_ini()
        self.theme_changed.emit(self.tokens.copy())

    def get_available_themes(self) -> Dict[str, Dict[str, Any]]:
        """
        Discovers all available system presets and user themes.
        Returns dict mapping theme display name to metadata:
        {"is_preset": bool, "path": str, "tokens": dict}
        """
        themes: Dict[str, Dict[str, Any]] = {}

        # 1. System Presets (themes/presets/)
        if os.path.exists(PRESETS_DIR):
            for fname in sorted(os.listdir(PRESETS_DIR)):
                if fname.endswith(".json"):
                    fpath = os.path.join(PRESETS_DIR, fname)
                    parsed = self._read_theme_file(fpath)
                    if parsed:
                        display_name = parsed.get("name", fname.replace(".json", "").replace("_", " ").title())
                        themes[display_name] = {
                            "is_preset": True,
                            "path": fpath,
                            "tokens": parsed["tokens"]
                        }

        # 2. User Themes (themes/user/)
        if os.path.exists(USER_THEMES_DIR):
            for fname in sorted(os.listdir(USER_THEMES_DIR)):
                if fname.endswith(".json"):
                    fpath = os.path.join(USER_THEMES_DIR, fname)
                    parsed = self._read_theme_file(fpath)
                    if parsed:
                        display_name = parsed.get("name", fname.replace(".json", "").replace("_", " ").title())
                        themes[display_name] = {
                            "is_preset": False,
                            "path": fpath,
                            "tokens": parsed["tokens"]
                        }

        return themes

    def _read_theme_file(self, fpath: str) -> Optional[Dict[str, Any]]:
        """Reads a theme file and extracts valid tokens."""
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                tokens = {}
                for k in DEFAULT_TOKENS.keys():
                    if k in data:
                        tokens[k] = normalize_hex8(str(data[k]))
                    else:
                        tokens[k] = DEFAULT_TOKENS[k]
                name = data.get("name", os.path.basename(fpath).replace(".json", ""))
                return {"name": name, "tokens": tokens}
        except Exception as e:
            logger.warning(f"Could not read theme file {fpath}: {e}")
        return None

    def apply_theme_by_name(self, theme_name: str) -> bool:
        """Applies a theme by display name from available presets or user themes."""
        available = self.get_available_themes()
        if theme_name in available:
            meta = available[theme_name]
            self.tokens = meta["tokens"].copy()
            self.active_theme_name = theme_name
            self._save_custom_theme()
            self._sync_config_ini(custom_path=meta["path"])
            self.theme_changed.emit(self.tokens.copy())
            logger.info(f"Applied theme '{theme_name}'")
            return True
        return False

    def save_user_theme(self, name: str) -> bool:
        """Saves current active tokens as a user custom theme."""
        if not name or not name.strip():
            return False

        clean_name = name.strip()
        filename = f"{sanitize_filename(clean_name)}.json"
        fpath = os.path.join(USER_THEMES_DIR, filename)

        payload = {"name": clean_name}
        payload.update(self.tokens)

        try:
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4)
            self.active_theme_name = clean_name
            self._save_custom_theme()
            self._sync_config_ini(custom_path=fpath)
            self.theme_changed.emit(self.tokens.copy())
            logger.info(f"Saved custom theme '{clean_name}' to {fpath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save user theme '{clean_name}': {e}")
            return False

    def rename_user_theme(self, old_name: str, new_name: str) -> bool:
        """Renames an existing user custom theme."""
        available = self.get_available_themes()
        if old_name not in available:
            return False

        meta = available[old_name]
        if meta["is_preset"]:
            logger.warning("Cannot rename system pre-built theme.")
            return False

        old_path = meta["path"]
        clean_new_name = new_name.strip()
        new_filename = f"{sanitize_filename(clean_new_name)}.json"
        new_path = os.path.join(USER_THEMES_DIR, new_filename)

        payload = {"name": clean_new_name}
        payload.update(meta["tokens"])

        try:
            with open(new_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4)

            if os.path.exists(old_path) and os.path.abspath(old_path) != os.path.abspath(new_path):
                os.remove(old_path)

            if self.active_theme_name == old_name:
                self.active_theme_name = clean_new_name

            self._save_custom_theme()
            self._sync_config_ini(custom_path=new_path)
            self.theme_changed.emit(self.tokens.copy())
            logger.info(f"Renamed theme '{old_name}' to '{clean_new_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to rename theme '{old_name}': {e}")
            return False

    def copy_theme(self, source_name: str, new_name: str) -> bool:
        """Duplicates a theme and saves it as a new user custom theme."""
        available = self.get_available_themes()
        if source_name not in available:
            return False

        source_tokens = available[source_name]["tokens"]
        clean_new_name = new_name.strip()
        new_filename = f"{sanitize_filename(clean_new_name)}.json"
        new_path = os.path.join(USER_THEMES_DIR, new_filename)

        payload = {"name": clean_new_name}
        payload.update(source_tokens)

        try:
            with open(new_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4)

            self.tokens = source_tokens.copy()
            self.active_theme_name = clean_new_name
            self._save_custom_theme()
            self._sync_config_ini(custom_path=new_path)
            self.theme_changed.emit(self.tokens.copy())
            logger.info(f"Copied theme '{source_name}' to '{clean_new_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to copy theme '{source_name}': {e}")
            return False

    def delete_user_theme(self, name: str) -> bool:
        """Deletes a user custom theme file (presets are protected)."""
        available = self.get_available_themes()
        if name not in available:
            return False

        meta = available[name]
        if meta["is_preset"]:
            logger.warning("Cannot delete system pre-built theme.")
            return False

        try:
            if os.path.exists(meta["path"]):
                os.remove(meta["path"])

            logger.info(f"Deleted user theme '{name}'")

            # If deleted theme was active, revert to Default Neon Purple
            if self.active_theme_name == name:
                self.apply_theme_by_name("Default Neon Purple")
            else:
                self.theme_changed.emit(self.tokens.copy())
            return True
        except Exception as e:
            logger.error(f"Failed to delete theme '{name}': {e}")
            return False

    def import_theme(self, json_path: str) -> bool:
        """Imports theme tokens from a JSON file."""
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
                name = data.get("name", os.path.basename(json_path).replace(".json", ""))
                self.active_theme_name = name
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
        """Exports active theme tokens to a JSON file."""
        try:
            dir_name = os.path.dirname(json_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            payload = {"name": self.active_theme_name}
            payload.update(self.tokens)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4)
            logger.info(f"Successfully exported theme to {json_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export theme to {json_path}: {e}")
            return False

    def generate_qss(self) -> str:
        """Generates dynamic application-wide QSS stylesheet."""
        bg_color = self.get_color("background")
        window_bg_color = self.get_color("window_bg")
        accent_1 = self.get_color("accent_1")
        accent_2 = self.get_color("accent_2")

        window_bg_solid = color_to_rgba_str(window_bg_color, alpha_override=1.0)
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
/* Global Base Window & Viewport Background */
QMainWindow, QDialog, QWidget#main_container, QTabWidget, QTabWidget::pane, QStackedWidget, QScrollArea, QAbstractScrollArea, QAbstractScrollArea::viewport, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {{
    background-color: {window_bg_solid};
    color: #ffffff;
    font-family: "Inter", "Outfit", "Segoe UI", sans-serif;
}}

/* QTabWidget & Tab Bar Styling */
QTabWidget::pane {{
    border: 1px solid {border_glass};
    background-color: {window_bg_solid};
}}

QTabBar::tab {{
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid {border_glass};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 8px 16px;
    color: rgba(255, 255, 255, 0.7);
    font-weight: bold;
}}

QTabBar::tab:selected {{
    background-color: {accent_1_subtle};
    border-bottom: 2px solid {accent_1_hex};
    color: #ffffff;
}}

QTabBar::tab:hover:!selected {{
    background-color: rgba(255, 255, 255, 0.10);
    color: #ffffff;
}}

/* Glassmorphic Card Containers & GroupBoxes */
QFrame.glass-card, QFrame#glass_card, QFrame.theme-card {{
    background-color: {bg_glass};
    border: 1px solid {border_glass};
    border-radius: 12px;
}}

QGroupBox {{
    background-color: {bg_glass};
    border: 1px solid {border_glass};
    border-radius: 10px;
    margin-top: 12px;
    color: #ffffff;
    font-weight: bold;
    font-size: 11px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #ffffff;
    font-weight: bold;
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

QComboBox QAbstractItemView {{
    background-color: {bg_solid};
    border: 1px solid {border_glass};
    color: #ffffff;
    selection-background-color: {accent_1_subtle};
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
    background: {accent_1_rgba};
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background: #ffffff;
    border: 1.5px solid {accent_1_hex};
    width: 14px;
    height: 14px;
    margin: -4px 0;
    border-radius: 7px;
}}

QSlider::handle:horizontal:hover {{
    background: {accent_1_hex};
    border: 1.5px solid #ffffff;
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
                    if "name" in data:
                        self.active_theme_name = data["name"]
            except Exception as e:
                logger.warning(f"Could not load custom theme from {CUSTOM_THEME_RELATIVE_PATH}: {e}")

    def _save_custom_theme(self) -> None:
        """Saves current tokens to themes/custom_theme.json."""
        try:
            os.makedirs("themes", exist_ok=True)
            payload = {"name": self.active_theme_name}
            payload.update(self.tokens)
            with open(CUSTOM_THEME_RELATIVE_PATH, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4)
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

        config.set("UI", "theme_name", self.active_theme_name)
        config.set("UI", "theme_path", custom_path or CUSTOM_THEME_RELATIVE_PATH)
        config.set("UI", "accent_1", self.tokens.get("accent_1", "#A855F7FF"))
        config.set("UI", "accent_2", self.tokens.get("accent_2", "#00F5A0FF"))
        config.set("UI", "background", self.tokens.get("background", "#0C0914FF"))

        try:
            with open(CONFIG_INI_PATH, "w", encoding="utf-8") as f:
                config.write(f)
        except Exception as e:
            logger.error(f"Failed to sync config.ini with theme settings: {e}")
