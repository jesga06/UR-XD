"""
Dynamic Theme Engine and Color Token Manager for PySide6 UI.
Manages active exposed base colors (window_bg, accent_1, accent_2, text),
theme behavior toggles (button_color_source, widget_bg_source, outline_source),
brightness sliders (widget_brightness, graph_brightness), dynamic HSV brightness recalculation,
QSS generation, JSON theme import/export, preset theme discovery, theme CRUD, and config.ini sync.
"""

import os
import json
import re
import configparser
import logging
from typing import Dict, Any, Optional

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtGui import QColor

logger = logging.getLogger("theme_manager")

DEFAULT_BASE_COLORS: Dict[str, str] = {
    "window_bg": "#0C0914FF",   # Application Frame & Main Canvas Background
    "accent_1": "#A855F7FF",   # Primary Input Color (Physical/hardware visualizers)
    "accent_2": "#00F5A0FF",   # Secondary Output Color (Virtual/emulated output visualizers)
    "text": "#FFFFFFFF"        # Global Text Color
}

DEFAULT_SOURCES: Dict[str, str] = {
    "button_color_source": "accent_1",   # accent_1 | accent_2
    "widget_bg_source": "accent_1",     # window_bg | accent_1 | accent_2
    "outline_source": "accent_2",        # accent_1 | accent_2
    "graph_axis_source": "accent_2"      # window_bg | accent_1 | accent_2
}

DEFAULT_BRIGHTNESS: Dict[str, int] = {
    "widget_brightness": 15,            # Absolute HSV Value percentage (0 to 20)
    "graph_brightness": 5,              # Absolute HSV Value percentage (0 to 20)
    "graph_axis_brightness": 50         # Absolute HSV Value percentage (0 to 100)
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


def color_to_hex6(color: QColor) -> str:
    """
    Converts a PySide6 QColor object to a 6-character uppercase hex string (#RRGGBB).
    Required for valid Qt QSS stylesheet color formatting.
    """
    return f"#{color.red():02X}{color.green():02X}{color.blue():02X}"


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
    Emits staging_changed(dict) for local sandbox editing, and theme_changed(dict)
    when themes are saved/committed for app-wide QSS styling.
    """
    theme_changed = Signal(dict)
    staging_changed = Signal(dict)
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

        self.base_colors: Dict[str, str] = DEFAULT_BASE_COLORS.copy()
        self.sources: Dict[str, str] = DEFAULT_SOURCES.copy()
        self.brightness: Dict[str, int] = DEFAULT_BRIGHTNESS.copy()

        self.committed_base_colors: Dict[str, str] = DEFAULT_BASE_COLORS.copy()
        self.committed_sources: Dict[str, str] = DEFAULT_SOURCES.copy()
        self.committed_brightness: Dict[str, int] = DEFAULT_BRIGHTNESS.copy()

        self.tokens: Dict[str, str] = {}
        self.current_tokens: Dict[str, str] = {}
        self.active_theme_name: str = "Neon Purple"
        self._themes_cache: Optional[Dict[str, Dict[str, Any]]] = None

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._on_save_timer_timeout)

        self._ensure_theme_directories()
        self._load_saved_theme()
        self.committed_base_colors = self.base_colors.copy()
        self.committed_sources = self.sources.copy()
        self.committed_brightness = self.brightness.copy()
        self.recalculate_theme()

    def _on_save_timer_timeout(self) -> None:
        """Executed 300ms after editing stops to persist session state to disk."""
        self._save_custom_theme()
        self._sync_config_ini()

    def _ensure_theme_directories(self):
        """Creates themes, themes/presets, and themes/user directories if missing."""
        os.makedirs("themes", exist_ok=True)
        os.makedirs(PRESETS_DIR, exist_ok=True)
        os.makedirs(USER_THEMES_DIR, exist_ok=True)

    def adjust_brightness(self, color_hex: str, percent_delta: float) -> str:
        """
        Adjusts the HSV value/brightness of a color by percent_delta (-1.0 to 1.0).
        Returns 8-character Hex string (#RRGGBBAA).
        """
        color = hex8_to_color(color_hex)
        h, s, v, a = color.getHsvF()
        new_v = max(0.0, min(1.0, v + percent_delta))
        color.setHsvF(h, s, new_v, a)
        return color_to_hex8(color)

    def set_hsv_value(self, color_hex: str, abs_value: float) -> str:
        """
        Sets the absolute HSV Value/brightness (0.0 to 1.0) of a color,
        preserving its Hue, Saturation, and Alpha.
        Returns 8-character Hex string (#RRGGBBAA).
        """
        color = hex8_to_color(color_hex)
        h, s, v, a = color.getHsvF()
        new_v = max(0.0, min(1.0, float(abs_value)))
        color.setHsvF(h, s, new_v, a)
        return color_to_hex8(color)

    def recalculate_theme(self) -> None:
        """
        Calculates derived tokens based on live staging base_colors, sources, and brightness.
        Emits staging_changed signal instantly for local Customization tab & preview panel (0ms latency).
        """
        tokens = dict(self.base_colors)

        # 1. Widget Background (Absolute HSV Value)
        wb_src = self.sources.get("widget_bg_source", "window_bg")
        base_wbg = self.base_colors.get(wb_src, self.base_colors.get("window_bg", "#0C0914FF"))
        w_val = self.brightness.get("widget_brightness", 0) / 100.0
        tokens["widget_bg"] = self.set_hsv_value(base_wbg, w_val)

        # Backward compatibility alias
        tokens["background"] = tokens["widget_bg"]

        # 2. Graph Background (Absolute HSV Value)
        g_val = self.brightness.get("graph_brightness", 0) / 100.0
        tokens["graph_bg"] = self.set_hsv_value(tokens["widget_bg"], g_val)

        # 3. Graph Axis (Absolute HSV Value from graph_axis_source, 0% to 100%)
        axis_src_key = self.sources.get("graph_axis_source", "accent_1")
        base_axis = self.base_colors.get(axis_src_key, self.base_colors.get("accent_1", "#A855F7FF"))
        axis_val = self.brightness.get("graph_axis_brightness", 50) / 100.0
        tokens["graph_axis"] = self.set_hsv_value(base_axis, axis_val)

        # 4. Outline Color
        outline_src_key = self.sources.get("outline_source", "accent_1")
        base_outline = self.base_colors.get(outline_src_key, self.base_colors.get("accent_1", "#A855F7FF"))
        tokens["outline"] = base_outline

        # 5. Button Colors
        btn_src_key = self.sources.get("button_color_source", "accent_1")
        base_btn = self.base_colors.get(btn_src_key, self.base_colors.get("accent_1", "#A855F7FF"))
        tokens["button_bg"] = base_btn
        tokens["button_hover"] = self.adjust_brightness(base_btn, 0.15)
        tokens["button_pressed"] = self.adjust_brightness(base_btn, -0.15)

        # 6. Tab Active & Inactive
        tokens["tab_active"] = self.adjust_brightness(self.base_colors.get("accent_1", "#A855F7FF"), 0.20)
        tokens["tab_inactive"] = self.adjust_brightness(self.base_colors.get("window_bg", "#0C0914FF"), 0.05)

        self.tokens = tokens
        self.current_tokens = tokens
        self.staging_changed.emit(self.tokens.copy())

    def commit_staging_theme(self, theme_name: Optional[str] = None) -> None:
        """
        Commits current staging tokens to app-wide committed state and emits theme_changed signal.
        """
        self.committed_base_colors = self.base_colors.copy()
        self.committed_sources = self.sources.copy()
        self.committed_brightness = self.brightness.copy()
        if theme_name:
            self.active_theme_name = theme_name

        self._save_custom_theme()
        self._sync_config_ini()
        self.theme_changed.emit(self.tokens.copy())

    def discard_staging_theme(self) -> None:
        """Restores staging tokens back to match active committed theme."""
        self.base_colors = self.committed_base_colors.copy()
        self.sources = self.committed_sources.copy()
        self.brightness = self.committed_brightness.copy()
        self.recalculate_theme()

    def theme_exists(self, name_or_file: str) -> tuple[bool, bool, str]:
        """
        Checks if a theme with specified display name or sanitized filename exists.
        Returns Tuple[exists: bool, is_preset: bool, path: str].
        """
        if not name_or_file or not name_or_file.strip():
            return False, False, ""

        clean = name_or_file.strip()
        sanitized = sanitize_filename(clean)
        available = self.get_available_themes()

        # Check by display name
        if clean in available:
            meta = available[clean]
            return True, meta["is_preset"], meta["path"]

        # Check by sanitized filename match
        for display_name, meta in available.items():
            if sanitize_filename(display_name) == sanitized or os.path.basename(meta["path"]) == f"{sanitized}.json":
                return True, meta["is_preset"], meta["path"]

        return False, False, ""

    def invalidate_theme_cache(self) -> None:
        """Invalidates theme discovery cache."""
        self._themes_cache = None

    def get_color(self, key: str, alpha_override: Optional[float] = None) -> QColor:
        """Returns a QColor object for specified token key."""
        hex_val = self.get_token(key)
        color = hex8_to_color(hex_val)
        if alpha_override is not None:
            a_int = int(max(0.0, min(1.0, float(alpha_override))) * 255)
            color.setAlpha(a_int)
        return color

    def get_rgba_str(self, key: str, alpha_override: Optional[float] = None) -> str:
        """Returns CSS rgba(R, G, B, A) string for specified key."""
        color = self.get_color(key)
        return color_to_rgba_str(color, alpha_override=alpha_override)

    def get_all_tokens(self) -> Dict[str, str]:
        """Returns a copy of all current active theme tokens (base & derived)."""
        return self.tokens.copy()

    def get_token(self, key: str) -> str:
        """Returns normalized 8-character hex string for specified key."""
        if key in self.tokens:
            return self.tokens[key]
        if key in self.base_colors:
            return self.base_colors[key]
        return DEFAULT_BASE_COLORS.get(key, "#FFFFFFFF")

    def set_token(self, key: str, hex_color: str) -> None:
        """Updates a single base color token and recalculates theme."""
        normalized = normalize_hex8(hex_color, default=self.base_colors.get(key, "#FFFFFFFF"))
        if key == "background":
            self.base_colors["window_bg"] = normalized
        else:
            self.base_colors[key] = normalized
        self.recalculate_theme()

    def set_source(self, source_key: str, source_val: str) -> None:
        """Updates a theme behavior source selector and recalculates theme."""
        if self.sources.get(source_key) != source_val:
            self.sources[source_key] = source_val
            self.recalculate_theme()

    def set_brightness(self, slider_key: str, value: int) -> None:
        """Updates a brightness slider percentage and recalculates theme."""
        if self.brightness.get(slider_key) != int(value):
            self.brightness[slider_key] = int(value)
            self.recalculate_theme()

    def reset_defaults(self) -> None:
        """Switches active theme to Neon Purple preset."""
        if not self.apply_theme_by_name("Neon Purple"):
            self.base_colors = DEFAULT_BASE_COLORS.copy()
            self.sources = DEFAULT_SOURCES.copy()
            self.brightness = DEFAULT_BRIGHTNESS.copy()
            self.active_theme_name = "Neon Purple"
            self.recalculate_theme()

    def get_available_themes(self, invalidate_cache: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Discovers all available system presets and user themes.
        Caches results to eliminate disk scanning overhead on token changes.
        """
        if not invalidate_cache and self._themes_cache is not None:
            return self._themes_cache

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
                            "base_colors": parsed["base_colors"],
                            "sources": parsed["sources"],
                            "brightness": parsed["brightness"]
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
                            "base_colors": parsed["base_colors"],
                            "sources": parsed["sources"],
                            "brightness": parsed["brightness"]
                        }

        self._themes_cache = themes
        return themes

    def _read_theme_file(self, fpath: str) -> Optional[Dict[str, Any]]:
        """Reads a theme file and extracts valid base colors, sources, and sliders."""
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                base_colors = DEFAULT_BASE_COLORS.copy()
                sources = DEFAULT_SOURCES.copy()
                brightness = DEFAULT_BRIGHTNESS.copy()

                if "base_colors" in data and isinstance(data["base_colors"], dict):
                    for k in DEFAULT_BASE_COLORS.keys():
                        if k in data["base_colors"]:
                            base_colors[k] = normalize_hex8(str(data["base_colors"][k]))
                else:
                    for k in DEFAULT_BASE_COLORS.keys():
                        if k in data:
                            base_colors[k] = normalize_hex8(str(data[k]))
                    if "background" in data and "window_bg" not in data:
                        base_colors["window_bg"] = normalize_hex8(str(data["background"]))

                if "sources" in data and isinstance(data["sources"], dict):
                    sources.update(data["sources"])
                if "brightness" in data and isinstance(data["brightness"], dict):
                    brightness.update(data["brightness"])

                name = data.get("name", os.path.basename(fpath).replace(".json", ""))
                return {
                    "name": name,
                    "base_colors": base_colors,
                    "sources": sources,
                    "brightness": brightness
                }
        except Exception as e:
            logger.warning(f"Could not read theme file {fpath}: {e}")
        return None

    def apply_theme_by_name(self, theme_name: str) -> bool:
        """Applies a theme by display name from available presets or user themes."""
        available = self.get_available_themes()
        if theme_name in available:
            meta = available[theme_name]
            self.base_colors = meta["base_colors"].copy()
            self.sources = meta["sources"].copy()
            self.brightness = meta["brightness"].copy()
            self.recalculate_theme()
            self.commit_staging_theme(theme_name)
            self._sync_config_ini(custom_path=meta["path"])
            logger.info(f"Applied theme '{theme_name}'")
            return True
        return False

    def save_user_theme(self, name: str) -> bool:
        """Saves current active base colors, toggles, and sliders as a user custom theme."""
        if not name or not name.strip():
            return False

        clean_name = name.strip()
        filename = f"{sanitize_filename(clean_name)}.json"
        fpath = os.path.join(USER_THEMES_DIR, filename)

        payload = {
            "name": clean_name,
            "base_colors": self.base_colors,
            "sources": self.sources,
            "brightness": self.brightness
        }
        payload.update(self.base_colors)

        try:
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4)
            self.invalidate_theme_cache()
            self.recalculate_theme()
            self.commit_staging_theme(clean_name)
            self._sync_config_ini(custom_path=fpath)
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

        payload = {
            "name": clean_new_name,
            "base_colors": meta["base_colors"],
            "sources": meta["sources"],
            "brightness": meta["brightness"]
        }
        payload.update(meta["base_colors"])

        try:
            with open(new_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4)

            if os.path.exists(old_path) and os.path.abspath(old_path) != os.path.abspath(new_path):
                os.remove(old_path)

            if self.active_theme_name == old_name:
                self.active_theme_name = clean_new_name

            self.invalidate_theme_cache()
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

        meta = available[source_name]
        clean_new_name = new_name.strip()
        new_filename = f"{sanitize_filename(clean_new_name)}.json"
        new_path = os.path.join(USER_THEMES_DIR, new_filename)

        payload = {
            "name": clean_new_name,
            "base_colors": meta["base_colors"],
            "sources": meta["sources"],
            "brightness": meta["brightness"]
        }
        payload.update(meta["base_colors"])

        try:
            with open(new_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4)

            self.base_colors = meta["base_colors"].copy()
            self.sources = meta["sources"].copy()
            self.brightness = meta["brightness"].copy()
            self.active_theme_name = clean_new_name
            self.invalidate_theme_cache()
            self.recalculate_theme()
            self._sync_config_ini(custom_path=new_path)
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
            self.invalidate_theme_cache()

            if self.active_theme_name == name:
                self.apply_theme_by_name("Default Neon Purple")
            else:
                self.theme_changed.emit(self.tokens.copy())
            return True
        except Exception as e:
            logger.error(f"Failed to delete theme '{name}': {e}")
            return False

    def export_theme_json(self, filepath: str) -> bool:
        """Exports base colors, toggles, and sliders to JSON."""
        return self.export_theme(filepath)

    def export_theme(self, json_path: str) -> bool:
        """Exports active theme tokens to a JSON file."""
        try:
            dir_name = os.path.dirname(json_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            payload = {
                "name": self.active_theme_name,
                "base_colors": self.base_colors,
                "sources": self.sources,
                "brightness": self.brightness
            }
            payload.update(self.base_colors)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4)
            logger.info(f"Successfully exported theme to {json_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export theme to {json_path}: {e}")
            return False

    def import_theme_json(self, filepath: str) -> bool:
        """Imports theme JSON and triggers recalculate_theme()."""
        return self.import_theme(filepath)

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

            if "base_colors" in data and isinstance(data["base_colors"], dict):
                for k, v in data["base_colors"].items():
                    if k in self.base_colors:
                        self.base_colors[k] = normalize_hex8(str(v), default=self.base_colors[k])
                if "sources" in data and isinstance(data["sources"], dict):
                    self.sources.update(data["sources"])
                if "brightness" in data and isinstance(data["brightness"], dict):
                    self.brightness.update(data["brightness"])
            else:
                for k in DEFAULT_BASE_COLORS.keys():
                    if k in data:
                        self.base_colors[k] = normalize_hex8(str(data[k]), default=self.base_colors[k])
                if "background" in data and "window_bg" not in data:
                    self.base_colors["window_bg"] = normalize_hex8(str(data["background"]), default=self.base_colors["window_bg"])

            name = data.get("name", os.path.basename(json_path).replace(".json", ""))
            self.active_theme_name = name
            self.recalculate_theme()
            logger.info(f"Successfully imported theme from {json_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to import theme from {json_path}: {e}")
            return False

    def generate_qss(self) -> str:
        """Generates dynamic application-wide QSS stylesheet from calculated tokens."""
        window_bg_color = self.get_color("window_bg")
        widget_bg_color = self.get_color("widget_bg")
        accent_1 = self.get_color("accent_1")
        accent_2 = self.get_color("accent_2")
        outline_color = self.get_color("outline")
        btn_color = self.get_color("button_bg")
        btn_hover_color = self.get_color("button_hover")
        btn_pressed_color = self.get_color("button_pressed")
        text_color = self.get_color("text")

        window_bg_solid = color_to_rgba_str(window_bg_color, alpha_override=1.0)
        widget_bg_glass = color_to_rgba_str(widget_bg_color, alpha_override=0.85)
        widget_bg_solid = color_to_rgba_str(widget_bg_color, alpha_override=1.0)

        border_outline = color_to_rgba_str(outline_color, alpha_override=0.45)
        border_hover = color_to_rgba_str(outline_color, alpha_override=0.75)

        accent_1_hex = color_to_hex6(accent_1)
        accent_1_rgba = color_to_rgba_str(accent_1, alpha_override=1.0)
        accent_1_subtle = color_to_rgba_str(accent_1, alpha_override=0.20)

        accent_2_hex = color_to_hex6(accent_2)
        accent_2_rgba = color_to_rgba_str(accent_2, alpha_override=1.0)

        btn_bg_rgba = color_to_rgba_str(btn_color, alpha_override=0.80)
        btn_hover_rgba = color_to_rgba_str(btn_hover_color, alpha_override=0.90)
        btn_pressed_rgba = color_to_rgba_str(btn_pressed_color, alpha_override=1.0)

        text_hex = color_to_hex6(text_color)

        return f"""
/* Global Base Window & Viewport Background */
QMainWindow, QDialog, QWidget#main_container, QTabWidget, QTabWidget::pane, QStackedWidget, QScrollArea, QAbstractScrollArea, QAbstractScrollArea::viewport, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {{
    background-color: {window_bg_solid};
    color: {text_hex};
    font-family: "Inter", "Outfit", "Segoe UI", sans-serif;
}}

/* QTabWidget & Tab Bar Styling */
QTabWidget::pane {{
    border: 1px solid {border_outline};
    background-color: {window_bg_solid};
}}

QTabBar::tab {{
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid {border_outline};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 8px 16px;
    color: {color_to_rgba_str(text_color, alpha_override=0.7)};
    font-weight: bold;
}}

QTabBar::tab:selected {{
    background-color: {accent_1_subtle};
    border-bottom: 2px solid {accent_1_hex};
    color: {text_hex};
}}

QTabBar::tab:hover:!selected {{
    background-color: rgba(255, 255, 255, 0.10);
    color: {text_hex};
}}

/* Glassmorphic Card Containers & GroupBoxes */
QFrame.glass-card, QFrame#glass_card, QFrame.theme-card {{
    background-color: {widget_bg_glass};
    border: 1px solid {border_outline};
    border-radius: 12px;
}}

QGroupBox {{
    background-color: {widget_bg_glass};
    border: 1px solid {border_outline};
    border-radius: 10px;
    margin-top: 12px;
    color: {text_hex};
    font-weight: bold;
    font-size: 11px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: {text_hex};
    font-weight: bold;
}}

/* Dynamic High-Contrast Text Fields & Inputs */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background-color: {widget_bg_glass};
    border: 1.5px solid {border_outline};
    color: {text_hex};
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: {accent_1_subtle};
}}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border: 2px solid {accent_2_rgba};
}}

QLineEdit::placeholder {{
    color: {color_to_rgba_str(text_color, alpha_override=0.55)};
    font-style: italic;
}}

QComboBox QAbstractItemView {{
    background-color: {widget_bg_solid};
    border: 1px solid {border_outline};
    color: {text_hex};
    selection-background-color: {accent_1_subtle};
}}

/* Interactive Buttons */
QPushButton, QPushButton.accent-btn, QPushButton#action_btn {{
    background-color: {btn_bg_rgba};
    border: 1px solid {border_outline};
    color: {text_hex};
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: bold;
}}

QPushButton:hover, QPushButton.accent-btn:hover, QPushButton#action_btn:hover {{
    background-color: {btn_hover_rgba};
    border: 1px solid #ffffff;
}}

QPushButton:pressed, QPushButton.accent-btn:pressed, QPushButton#action_btn:pressed {{
    background-color: {btn_pressed_rgba};
}}

QPushButton.secondary-btn {{
    background-color: rgba(255, 255, 255, 0.08);
    border: 1px solid {border_outline};
    color: {text_hex};
    border-radius: 6px;
    padding: 6px 12px;
}}

QPushButton.secondary-btn:hover {{
    background-color: {btn_hover_rgba};
}}

/* Checkboxes */
QCheckBox {{
    color: {text_hex};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1.5px solid {border_hover};
    background-color: {color_to_rgba_str(widget_bg_color, alpha_override=0.6)};
}}

QCheckBox::indicator:checked {{
    background-color: {accent_1_rgba};
    border: 1.5px solid {accent_1_hex};
}}

/* Horizontal Sliders */
QSlider::groove:horizontal {{
    height: 6px;
    background: {color_to_rgba_str(widget_bg_color, alpha_override=0.6)};
    border: 1px solid {border_outline};
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
    color: {text_hex};
}}

QLabel.muted {{
    color: {color_to_rgba_str(text_color, alpha_override=0.65)};
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
                    if "base_colors" in data and isinstance(data["base_colors"], dict):
                        for k, v in data["base_colors"].items():
                            if k in self.base_colors:
                                self.base_colors[k] = normalize_hex8(str(v), default=DEFAULT_BASE_COLORS[k])
                    else:
                        for k in DEFAULT_BASE_COLORS.keys():
                            if k in data:
                                self.base_colors[k] = normalize_hex8(str(data[k]), default=DEFAULT_BASE_COLORS[k])
                    if "sources" in data and isinstance(data["sources"], dict):
                        self.sources.update(data["sources"])
                    if "brightness" in data and isinstance(data["brightness"], dict):
                        self.brightness.update(data["brightness"])
                    if "name" in data:
                        self.active_theme_name = data["name"]
            except Exception as e:
                logger.warning(f"Could not load custom theme from {CUSTOM_THEME_RELATIVE_PATH}: {e}")

    def _save_custom_theme(self) -> None:
        """Saves current theme configuration to themes/custom_theme.json."""
        try:
            os.makedirs("themes", exist_ok=True)
            payload = {
                "name": self.active_theme_name,
                "base_colors": self.base_colors,
                "sources": self.sources,
                "brightness": self.brightness
            }
            payload.update(self.base_colors)
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
        config.set("UI", "accent_1", self.base_colors.get("accent_1", "#A855F7FF"))
        config.set("UI", "accent_2", self.base_colors.get("accent_2", "#00F5A0FF"))
        config.set("UI", "window_bg", self.base_colors.get("window_bg", "#0C0914FF"))
        config.set("UI", "text", self.base_colors.get("text", "#FFFFFFFF"))
        config.set("UI", "button_color_source", self.sources.get("button_color_source", "accent_1"))
        config.set("UI", "widget_bg_source", self.sources.get("widget_bg_source", "window_bg"))
        config.set("UI", "outline_source", self.sources.get("outline_source", "accent_1"))
        config.set("UI", "widget_brightness", str(self.brightness.get("widget_brightness", 0)))
        config.set("UI", "graph_brightness", str(self.brightness.get("graph_brightness", 0)))

        try:
            with open(CONFIG_INI_PATH, "w", encoding="utf-8") as f:
                config.write(f)
        except Exception as e:
            logger.error(f"Failed to sync config.ini with theme settings: {e}")
