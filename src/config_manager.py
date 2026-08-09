import json
import os
import re
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger('config_manager')


def get_sanitized_filename(name: str, mode: Optional[str] = None) -> str:
    """
    Sanitizes a string to be a safe JSON filename.
    Replaces non-alphanumeric chars, converts spaces to underscores, and lowercases.
    """
    cleaned = re.sub(r'[^a-zA-Z0-9_\- ]', '', name)
    cleaned = cleaned.replace(' ', '_').lower()
    if mode:
        return f"{cleaned}_{mode}.json"
    return f"{cleaned}.json"


class ControllerConfig:
    """
    Manages JSON configuration profiles for controller mappings,
    deadzones, response curves, and macro settings.
    """

    def __init__(self, filepath: Optional[str] = None):
        self.filepath: Optional[str] = filepath
        self.data: Dict[str, Any] = {}
        if filepath and os.path.exists(filepath):
            self.load()
        else:
            self._init_defaults()

    def _init_defaults(self) -> None:
        self.data = {
            "settings": {
                "layout": "xbox",
                "digital_lt": "false",
                "digital_rt": "false"
            },
            "hidhide": {
                "enabled": True,
                "auto_cloak": True,
                "cli_path": ""
            },
            "extra_buttons": {},
            "block_xinput": {},
            "shift_layer": {
                "mode": "hold",
                "trigger_button": ""
            },
            "shift_mappings": {},
            "shift_block_xinput": {},
            "shift_layers": [
                {
                    "id": "layer_base",
                    "name": "Base Layer",
                    "trigger_button": "",
                    "modifier_button": "",
                    "mode": "hold",
                    "mappings": {},
                    "block_xinput": {}
                },
                {
                    "id": "shift_1",
                    "name": "Shift Layer 1",
                    "trigger_button": "",
                    "modifier_button": "",
                    "mode": "hold",
                    "mappings": {},
                    "block_xinput": {}
                }
            ],
            "chords": {},
            "hardware_chords": {},
            "backend": {
                "mode": "auto"
            },
            "analog": {
                "deadzone": "0.08",
                "anti_deadzone": "0.0",
                "curve": "linear",
                "exp_factor": "2.0"
            },
            "analog_left": {
                "deadzone": "0.05",
                "anti_deadzone": "0.0",
                "curve": "linear",
                "exp_factor": "2.0"
            },
            "analog_right": {
                "deadzone": "0.05",
                "anti_deadzone": "0.0",
                "curve": "linear",
                "exp_factor": "2.0"
            },
            "trigger_left": {
                "deadzone": "0.05",
                "anti_deadzone": "0.0",
                "curve": "linear",
                "exp_factor": "2.0"
            },
            "trigger_right": {
                "deadzone": "0.05",
                "anti_deadzone": "0.0",
                "curve": "linear",
                "exp_factor": "2.0"
            }
        }

    def load(self) -> None:
        if not self.filepath:
            self._init_defaults()
            return
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            self._migrate_shift_layers()
        except Exception as e:
            print(f"Error loading {self.filepath}: {e}")
            logger.error(f"Error loading {self.filepath}: {e}", exc_info=True)
            self._init_defaults()

    def _migrate_shift_layers(self) -> None:
        if "shift_layers" not in self.data or not isinstance(self.data.get("shift_layers"), list):
            trigger_button = self.get("shift_layer", "trigger_button", fallback="") or ""
            if trigger_button.strip().lower() in ("none", "null", "false", "0"):
                trigger_button = ""
            mode = self.get("shift_layer", "mode", fallback="hold") or "hold"
            mappings = self.data.get("shift_mappings", {})
            block_xinput = self.data.get("shift_block_xinput", {})
            self.data["shift_layers"] = [
                {
                    "id": "shift_1",
                    "name": "Shift Layer 1",
                    "trigger_button": trigger_button,
                    "modifier_button": "",
                    "mode": mode,
                    "mappings": dict(mappings) if isinstance(mappings, dict) else {},
                    "block_xinput": dict(block_xinput) if isinstance(block_xinput, dict) else {}
                }
            ]
        else:
            layers = self.data["shift_layers"]
            seen_ids = set()
            has_duplicates = False
            for l in layers:
                if isinstance(l, dict):
                    trig = (l.get("trigger_button") or "").strip().lower()
                    if trig in ("none", "null", "false", "0"):
                        l["trigger_button"] = ""
                    mod = (l.get("modifier_button") or "").strip().lower()
                    if mod in ("none", "null", "false", "0"):
                        l["modifier_button"] = ""
                    
                    lid = l.get("id")
                    if not lid or not isinstance(lid, str) or lid in seen_ids:
                        has_duplicates = True
                    else:
                        seen_ids.add(lid)
                else:
                    has_duplicates = True

            if has_duplicates:
                logger.warning("Duplicate or invalid shift layer IDs detected in configuration; algorithmically repairing layer IDs.")
                valid_layers = []
                for idx, l in enumerate(layers, start=1):
                    if isinstance(l, dict):
                        l["id"] = f"shift_{idx}"
                        valid_layers.append(l)
                self.data["shift_layers"] = valid_layers

        self._sync_legacy_shift_fields()

    def _sync_legacy_shift_fields(self) -> None:
        layers = self.data.get("shift_layers", [])
        if layers and isinstance(layers, list) and len(layers) > 0:
            first = layers[0]
            if isinstance(first, dict):
                self.data["shift_layer"] = {
                    "mode": first.get("mode", "hold"),
                    "trigger_button": first.get("trigger_button", "")
                }
                self.data["shift_mappings"] = dict(first.get("mappings", {}))
                self.data["shift_block_xinput"] = dict(first.get("block_xinput", {}))

    def get_shift_layers(self) -> List[Dict[str, Any]]:
        if "shift_layers" not in self.data or not isinstance(self.data.get("shift_layers"), list):
            self._migrate_shift_layers()
        return self.data["shift_layers"]

    def set_shift_layers(self, layers: List[Dict[str, Any]]) -> None:
        self.data["shift_layers"] = layers
        self._migrate_shift_layers()

    def add_shift_layer(self, name: str = "", trigger_button: str = "", modifier_button: str = "", mode: str = "hold", haptic_profile: str = "") -> Dict[str, Any]:
        layers = self.get_shift_layers()
        existing_indices = []
        for l in layers:
            if isinstance(l, dict):
                lid = l.get("id", "")
                if isinstance(lid, str) and lid.startswith("shift_"):
                    try:
                        existing_indices.append(int(lid.split("_", 1)[1]))
                    except ValueError:
                        pass

        next_idx = (max(existing_indices) + 1) if existing_indices else (len(layers) + 1)
        layer_id = f"shift_{next_idx}"

        existing_ids = {l.get("id") for l in layers if isinstance(l, dict)}
        while layer_id in existing_ids:
            next_idx += 1
            layer_id = f"shift_{next_idx}"

        layer_name = name if name else f"Shift Layer {next_idx}"
        new_layer = {
            "id": layer_id,
            "name": layer_name,
            "trigger_button": trigger_button,
            "modifier_button": modifier_button,
            "mode": mode,
            "haptic_profile": haptic_profile,
            "mappings": {},
            "block_xinput": {}
        }
        layers.append(new_layer)
        self.set_shift_layers(layers)
        return new_layer

    def remove_shift_layer(self, layer_id: str) -> None:
        layers = self.get_shift_layers()
        if len(layers) <= 1:
            return
        layers = [l for l in layers if l.get("id") != layer_id]
        self.set_shift_layers(layers)

    def get_global_haptic_profile(self) -> str:
        h_cfg = self.data.get("haptics", {})
        if isinstance(h_cfg, dict):
            return h_cfg.get("global_default", "RM[30% @ 0ms, dur=1500ms]")
        return "RM[30% @ 0ms, dur=1500ms]"

    def set_global_haptic_profile(self, profile: str) -> None:
        if "haptics" not in self.data or not isinstance(self.data.get("haptics"), dict):
            self.data["haptics"] = {}
        self.data["haptics"]["global_default"] = profile.strip()

    def get_haptic_enabled(self) -> bool:
        h_cfg = self.data.get("haptics", {})
        if isinstance(h_cfg, dict):
            return bool(h_cfg.get("enabled", True))
        return True

    def set_haptic_enabled(self, enabled: bool) -> None:
        if "haptics" not in self.data or not isinstance(self.data.get("haptics"), dict):
            self.data["haptics"] = {}
        self.data["haptics"]["enabled"] = bool(enabled)

    def get_effective_layer_haptic_profile(self, layer_id: str) -> str:
        layers = self.get_shift_layers()
        for l in layers:
            if l.get("id") == layer_id:
                prof = (l.get("haptic_profile") or "").strip()
                if prof:
                    return prof
                break
        return self.get_global_haptic_profile()

    def save(self) -> None:
        if not self.filepath:
            return
        try:
            dirname = os.path.dirname(self.filepath)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"Error saving {self.filepath}: {e}")
            logger.error(f"Error saving {self.filepath}: {e}", exc_info=True)

    def has_section(self, section: str) -> bool:
        return section in self.data

    def add_section(self, section: str) -> None:
        if section not in self.data:
            self.data[section] = {}

    def remove_section(self, section: str) -> None:
        if section in self.data:
            del self.data[section]

    def has_option(self, section: str, option: str) -> bool:
        return section in self.data and isinstance(self.data[section], dict) and option in self.data[section]

    def remove_option(self, section: str, option: str) -> None:
        if section in self.data and isinstance(self.data[section], dict) and option in self.data[section]:
            del self.data[section][option]

    def get(self, section: str, option: str, fallback: Optional[str] = None) -> Optional[str]:
        if section in self.data and isinstance(self.data[section], dict) and option in self.data[section]:
            return str(self.data[section][option])
        return fallback

    def getboolean(self, section: str, option: str, fallback: Optional[bool] = None) -> Optional[bool]:
        val = self.get(section, option)
        if val is None:
            return fallback
        return val.lower() in ('true', 'yes', 'on', '1')

    def getfloat(self, section: str, option: str, fallback: Optional[float] = None) -> Optional[float]:
        val = self.get(section, option)
        if val is None:
            return fallback
        try:
            return float(val)
        except ValueError:
            return fallback

    def set(self, section: str, option: str, value: Any) -> None:
        if section not in self.data or not isinstance(self.data[section], dict):
            self.data[section] = {}
        self.data[section][option] = str(value)

    def items(self, section: str) -> List[Tuple[str, Any]]:
        if section in self.data and isinstance(self.data[section], dict):
            return list(self.data[section].items())
        return []

    def options(self, section: str) -> List[str]:
        if section in self.data and isinstance(self.data[section], dict):
            return list(self.data[section].keys())
        return []


