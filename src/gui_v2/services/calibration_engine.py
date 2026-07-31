"""
CalibrationEngine Service (calibration_engine.py)
Decoupled calibration engine porting the exact state machine, step sequence,
baseline re-synchronization, byte filtering, 3-click confirmations, axis candidate sorting,
trigger 2s sampling, and D-Pad Hat switch rules from legacy calibration.py (lines 630-1065).
"""

import os
import sys
import json
import time
import logging
from typing import Dict, Any, Optional, List, Tuple, Set

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

logger = logging.getLogger("CalibrationEngine")
if not logger.handlers:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("[%(asctime)s][CALIB-ENGINE][%(levelname)s] %(message)s"))
    logger.addHandler(h)
    logger.setLevel(logging.DEBUG)


def get_layout_labels(layout_type: str) -> Dict[str, str]:
    if layout_type == "playstation":
        return {
            "a": "Cross (X) (Bottom)", "b": "Circle (O) (Right)", "x": "Square (■) (Left)", "y": "Triangle (▲) (Top)",
            "lb": "L1", "rb": "R1", "lt": "L2", "rt": "R2", "l3": "L3", "r3": "R3", "select": "Share", "start": "Options"
        }
    elif layout_type == "nintendo":
        return {
            "a": "B (Bottom)", "b": "A (Right)", "x": "Y (Left)", "y": "X (Top)",
            "lb": "L", "rb": "R", "lt": "ZL", "rt": "ZR", "l3": "LS", "r3": "RS", "select": "-", "start": "+"
        }
    else:
        return {
            "a": "A (Bottom)", "b": "B (Right)", "x": "X (Left)", "y": "Y (Top)",
            "lb": "LB", "rb": "RB", "lt": "LT", "rt": "RT", "l3": "LS", "r3": "RS", "select": "Select/Back", "start": "Start"
        }


class CalibrationEngine(QObject):
    """
    Decoupled state machine engine matching src/calibration.py algorithms 1:1.
    Emits Qt Signals to communicate state updates to any GUI view/dialog.
    """
    prompt_changed = Signal(str, str, str, int, int)  # (key, category, prompt_text, step_index, total_steps)
    status_updated = Signal(str, str)  # (message, color_hex)
    input_mapped = Signal(str, dict)  # (key, input_config)
    calibration_finished = Signal(dict)  # (profile_data)
    stick_position_updated = Signal(str, float, float)  # (stick_name, norm_x, norm_y)

    def __init__(self, device_info: dict, layout_type: str = "xbox", extra_buttons: Optional[List[str]] = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.device_info = device_info
        self.layout_type = layout_type
        self.extra_buttons = extra_buttons or []

        self.baselines: Dict[str, List[int]] = {}  # { full_id ("iface_reportid"): data_list }
        self.latest_reports: Dict[str, List[int]] = {}  # { full_id: data_list }

        self.profile: Dict[str, Any] = {
            "name": device_info.get("product_string") or "Custom Gamepad",
            "vid": f"{device_info.get('vendor_id', 0):04X}",
            "pid": f"{device_info.get('product_id', 0):04X}",
            "layout": layout_type,
            "has_report_id": True,
            "reports": {}
        }

        # Build step list matching calibration.py lines 631-667
        labels = get_layout_labels(self.layout_type)
        self.steps: List[Tuple[str, str, str]] = [
            ("a", "buttons", f"Press the '{labels['a']}' button"),
            ("b", "buttons", f"Press the '{labels['b']}' button"),
            ("x", "buttons", f"Press the '{labels['x']}' button"),
            ("y", "buttons", f"Press the '{labels['y']}' button"),
            ("lb", "buttons", f"Press the '{labels['lb']}' bumper"),
            ("rb", "buttons", f"Press the '{labels['rb']}' bumper"),
            ("select", "buttons", f"Press the '{labels['select']}' button"),
            ("start", "buttons", f"Press the '{labels['start']}' button"),
            ("home", "buttons", "Press the Home/Guide button"),
            ("lx", "axes", "Move the Left Stick RIGHT"),
            ("ly", "axes", "Move the Left Stick UP"),
            ("verify_ls", "verify_stick", "Verify Left Stick Telemetry"),
            ("rx", "axes", "Move the Right Stick RIGHT"),
            ("ry", "axes", "Move the Right Stick UP"),
            ("verify_rs", "verify_stick", "Verify Right Stick Telemetry"),
            ("l3", "stick_clicks", f"Press the Left Stick button ({labels['l3']}) 3 TIMES"),
            ("r3", "stick_clicks", f"Press the Right Stick button ({labels['r3']}) 3 TIMES"),
            ("lt", "triggers", f"Press the Left Trigger ({labels['lt']})"),
            ("rt", "triggers", f"Press the Right Trigger ({labels['rt']})"),
            ("dpad", "hat", "Press the D-Pad UP (Assuming standard Hat switch)")
        ]

        for extra in self.extra_buttons:
            self.steps.append((extra, "buttons", f"Press the '{extra.upper()}' extra button"))

        self.current_step_idx: int = 0
        self.step_in_progress: bool = False
        self.ignore_until_time: float = 0.0

        # State tracking per step (matching calibration.py reset lines 674-676)
        self.click_counts: Dict[Tuple[str, int, int], int] = {}
        self.byte_history: Dict[Tuple[str, int], Set[int]] = {}
        self.button_byte_history: Dict[Tuple[str, int], Set[int]] = {}
        self.last_click_time: float = 0.0

        # Trigger sampling state (calibration.py lines 847-978)
        self.trigger_start_time: float = 0.0
        self.trigger_samples: List[Tuple[str, List[int]]] = []

    def reconfigure(self, layout_type: str, extra_buttons: Optional[List[str]] = None) -> None:
        self.layout_type = layout_type
        self.extra_buttons = extra_buttons or []
        self.profile["layout"] = layout_type
        if self.extra_buttons:
            self.profile["extra_buttons"] = {eb.lower(): {} for eb in self.extra_buttons}

        labels = get_layout_labels(self.layout_type)
        self.steps = [
            ("a", "buttons", f"Press the '{labels['a']}' button"),
            ("b", "buttons", f"Press the '{labels['b']}' button"),
            ("x", "buttons", f"Press the '{labels['x']}' button"),
            ("y", "buttons", f"Press the '{labels['y']}' button"),
            ("lb", "buttons", f"Press the '{labels['lb']}' bumper"),
            ("rb", "buttons", f"Press the '{labels['rb']}' bumper"),
            ("select", "buttons", f"Press the '{labels['select']}' button"),
            ("start", "buttons", f"Press the '{labels['start']}' button"),
            ("home", "buttons", "Press the Home/Guide button"),
            ("lx", "axes", "Move the Left Stick RIGHT"),
            ("ly", "axes", "Move the Left Stick UP"),
            ("verify_ls", "verify_stick", "Verify Left Stick Telemetry"),
            ("rx", "axes", "Move the Right Stick RIGHT"),
            ("ry", "axes", "Move the Right Stick UP"),
            ("verify_rs", "verify_stick", "Verify Right Stick Telemetry"),
            ("l3", "stick_clicks", f"Press the Left Stick button ({labels['l3']}) 3 TIMES"),
            ("r3", "stick_clicks", f"Press the Right Stick button ({labels['r3']}) 3 TIMES"),
            ("lt", "triggers", f"Press the Left Trigger ({labels['lt']})"),
            ("rt", "triggers", f"Press the Right Trigger ({labels['rt']})"),
            ("dpad", "hat", "Press the D-Pad UP (Assuming standard Hat switch)")
        ]
        for extra in self.extra_buttons:
            self.steps.append((extra, "buttons", f"Press the '{extra.upper()}' extra button"))

    def start(self) -> None:
        self.current_step_idx = 0
        self.ignore_until_time = 0.0
        if self.extra_buttons:
            self.profile["extra_buttons"] = {eb.lower(): {} for eb in self.extra_buttons}
        self._emit_current_prompt()

    def _emit_current_prompt(self) -> None:
        self.button_byte_history.clear()
        if self.current_step_idx < len(self.steps):
            name, cat, prompt = self.steps[self.current_step_idx]
            self.prompt_changed.emit(name, cat, prompt, self.current_step_idx, len(self.steps))
            self.status_updated.emit(f"Listening for '{name.upper()}' input...", "#FFFFFF")
        else:
            self.status_updated.emit("✅ Calibration Complete!", "#55FF55")
            self.calibration_finished.emit(self.profile)

    def capture_rest_baseline(self, report_payloads: Dict[str, List[int]]) -> None:
        """Capture rest baseline payloads across all report IDs/interfaces."""
        for full_id, data in report_payloads.items():
            self.baselines[full_id] = list(data)
            self.latest_reports[full_id] = list(data)
        self.status_updated.emit("✅ Rest state baselines established!", "#55FF55")

    def process_report(self, iface_num: int, report_id: int, payload: List[int]) -> None:
        """
        Process incoming raw HID payload. Verbatim port of calibration.py lines 713-1044.
        """
        if self.current_step_idx >= len(self.steps):
            return

        if time.time() < self.ignore_until_time:
            rem = self.ignore_until_time - time.time()
            logger.debug(f"[COOLDOWN] Report {iface_num}_{report_id} suppressed ({rem:.2f}s remaining)")
            return

        full_id = f"{iface_num}_{report_id}"
        self.latest_reports[full_id] = list(payload)

        if full_id not in self.baselines:
            logger.info(f"[BASELINE] First report received for {full_id}. Storing rest baseline.")
            self.baselines[full_id] = list(payload)
            return

        base = self.baselines[full_id]
        curr = payload
        if len(curr) != len(base):
            logger.warning(f"[PAYLOAD-MISMATCH] Report {full_id} length {len(curr)} != baseline length {len(base)}")
            return

        name, cat, prompt = self.steps[self.current_step_idx]

        # Gather all diffs across latest reports
        diffs = []
        for fid, latest_data in list(self.latest_reports.items()):
            if fid not in self.baselines:
                self.baselines[fid] = list(latest_data)
                continue
            b_data = self.baselines[fid]
            if len(latest_data) != len(b_data):
                continue
            for b_idx in range(len(latest_data)):
                if latest_data[b_idx] != b_data[b_idx]:
                    diffs.append((fid, b_idx, latest_data[b_idx], b_data[b_idx]))

        if diffs:
            logger.debug(f"[DIFFS-DETECTED] Step {self.current_step_idx+1}/{len(self.steps)} ('{name}' | {cat}): {diffs}")

        if not diffs and cat != "triggers":
            return

        # -------------------------------------------------------------------
        # CATEGORY 1: STICK CLICKS (3-Click Confirmation with 0.4s debounce)
        # calibration.py lines 730-790
        # -------------------------------------------------------------------
        if cat == "stick_clicks":
            for fid, b_idx, curr_val, base_val in diffs:
                byte_key = (fid, b_idx)
                if byte_key not in self.byte_history:
                    self.byte_history[byte_key] = {base_val}
                self.byte_history[byte_key].add(curr_val)

            # Exclude bytes mapped to axis, trigger, hat, or button
            known_mapped_bytes = set()
            for r_id, r_data in self.profile.get("reports", {}).items():
                for in_name, in_cfg in r_data.get("inputs", {}).items():
                    t = in_cfg.get("type")
                    if t in ("axis", "trigger", "hat"):
                        known_mapped_bytes.add((r_id, in_cfg.get("byte")))
                        if in_cfg.get("length", 1) == 2:
                            known_mapped_bytes.add((r_id, in_cfg.get("byte") + 1))

            for fid, b_idx, curr_val, base_val in diffs:
                byte_key = (fid, b_idx)
                if byte_key in known_mapped_bytes:
                    continue
                if len(self.byte_history[byte_key]) > 3:
                    continue

                changed_bits = curr_val ^ base_val
                for bit in range(8):
                    bitmask = 1 << bit
                    if changed_bits & bitmask:
                        is_known = False
                        for rep_data in self.profile.get("reports", {}).values():
                            for in_cfg in rep_data.get("inputs", {}).values():
                                if in_cfg.get("type") == "button" and in_cfg.get("byte") == b_idx and in_cfg.get("bitmask") == bitmask:
                                    is_known = True
                        if is_known:
                            continue

                        click_key = (fid, b_idx, bitmask)
                        if time.time() - self.last_click_time > 0.4:
                            if click_key not in self.click_counts:
                                self.click_counts[click_key] = 0
                            self.click_counts[click_key] += 1
                            self.last_click_time = time.time()

                            count = self.click_counts[click_key]
                            if count < 3:
                                self.status_updated.emit(f"  Click {count}/3 detected for {name.upper()}!", "#FFFF55")
                                return
                            else:
                                if fid not in self.profile["reports"]:
                                    self.profile["reports"][fid] = {"inputs": {}}
                                cfg = {"type": "button", "byte": b_idx, "bitmask": bitmask}
                                self.profile["reports"][fid]["inputs"][name] = cfg
                                self.status_updated.emit(f"Confirmed {name.upper()} at {fid}, byte {b_idx}, mask {bitmask}", "#55FF55")
                                self.input_mapped.emit(name, cfg)
                                self._advance_step(name)
                                return

        # -------------------------------------------------------------------
        # CATEGORY 2: BUTTONS (Bitmask isolation & byte noise filtering)
        # calibration.py lines 791-846
        # -------------------------------------------------------------------
        elif cat == "buttons":
            changed_bytes = []
            for fid, b_idx, curr_val, base_val in diffs:
                byte_key = (fid, b_idx)
                if byte_key not in self.button_byte_history:
                    self.button_byte_history[byte_key] = {base_val}
                self.button_byte_history[byte_key].add(curr_val)

                changed_bits = curr_val ^ base_val
                if changed_bits != 0:
                    changed_bytes.append((fid, b_idx, changed_bits))

            known_axis_bytes = set()
            for r_id, r_data in self.profile.get("reports", {}).items():
                for in_name, in_cfg in r_data.get("inputs", {}).items():
                    if in_cfg.get("type") in ("axis", "trigger", "hat"):
                        known_axis_bytes.add((r_id, in_cfg.get("byte")))
                        if in_cfg.get("length", 1) == 2:
                            known_axis_bytes.add((r_id, in_cfg.get("byte") + 1))

            known_bits = set()
            for r_id, r_data in self.profile.get("reports", {}).items():
                for in_name, in_cfg in r_data.get("inputs", {}).items():
                    if in_cfg.get("type") == "button":
                        known_bits.add((r_id, in_cfg.get("byte"), in_cfg.get("bitmask")))

            clean_changed = []
            for fid, b_idx, changed_bits in changed_bytes:
                byte_key = (fid, b_idx)
                if byte_key in known_axis_bytes:
                    continue
                if len(self.button_byte_history.get(byte_key, [])) > 3:
                    continue

                for bit in range(8):
                    bitmask = 1 << bit
                    if changed_bits & bitmask:
                        if (fid, b_idx, bitmask) not in known_bits:
                            clean_changed.append((fid, b_idx, bitmask))

            if clean_changed:
                fid, b_idx, bit_mask = clean_changed[0]
                if fid not in self.profile["reports"]:
                    self.profile["reports"][fid] = {"inputs": {}}
                cfg = {"type": "button", "byte": b_idx, "bitmask": bit_mask}
                self.profile["reports"][fid]["inputs"][name] = cfg
                self.status_updated.emit(f"Detected {name.upper()} at {fid}, byte {b_idx}, mask {bit_mask}", "#55FF55")
                self.input_mapped.emit(name, cfg)
                self._advance_step(name)
                return

        # -------------------------------------------------------------------
        # CATEGORY 3: TRIGGERS (2.0s Sampling & Digital Fallback)
        # calibration.py lines 847-979
        # -------------------------------------------------------------------
        elif cat == "triggers":
            if self.trigger_start_time == 0:
                self.trigger_start_time = time.time()
                self.trigger_samples = []

            for fid, latest_data in list(self.latest_reports.items()):
                self.trigger_samples.append((fid, list(latest_data)))

            elapsed = time.time() - self.trigger_start_time
            if elapsed < 2.0:
                self.status_updated.emit(f"Collecting 2.0s trigger data for {name.upper()} ({elapsed:.1f}s/2.0s)...", "#FFFF55")
                return

            # Analyze Trigger Samples (calibration.py lines 860-955)
            unique_counts: Dict[str, List[Set[int]]] = {}
            base_state: Dict[str, List[int]] = dict(self.baselines)

            for fid, data in self.trigger_samples:
                if fid not in unique_counts:
                    unique_counts[fid] = [set() for _ in range(len(data))]
                    if fid in base_state:
                        for byte_idx, b_val in enumerate(base_state[fid]):
                            if byte_idx < len(unique_counts[fid]):
                                unique_counts[fid][byte_idx].add(b_val)
                for byte_idx, val in enumerate(data):
                    if byte_idx < len(unique_counts[fid]):
                        unique_counts[fid][byte_idx].add(val)

            known_axis_bytes = set()
            for r_id, r_data in self.profile.get("reports", {}).items():
                for in_name, in_cfg in r_data.get("inputs", {}).items():
                    if in_cfg.get("type") in ("axis", "trigger", "hat", "button"):
                        known_axis_bytes.add((r_id, in_cfg.get("byte")))
                        if in_cfg.get("length", 1) == 2:
                            known_axis_bytes.add((r_id, in_cfg.get("byte") + 1))

            best_full_id = None
            best_byte = -1
            max_uniques = 0

            for fid, counts in unique_counts.items():
                for byte_idx, u_set in enumerate(counts):
                    if (fid, byte_idx) in known_axis_bytes:
                        continue

                    if len(u_set) > max_uniques:
                        max_uniques = len(u_set)
                        best_full_id = fid
                        best_byte = byte_idx

            if max_uniques > 2 and best_full_id:
                if best_full_id not in self.profile["reports"]:
                    self.profile["reports"][best_full_id] = {"inputs": {}}
                cfg = {
                    "type": "trigger", "byte": best_byte, "length": 1, "center": False, "is_analog": True,
                    "range_confidence": round(min(1.0, max_uniques / 40.0), 3)
                }
                self.profile["reports"][best_full_id]["inputs"][name] = cfg
                self.status_updated.emit(f"Detected Analog {name.upper()} at {best_full_id}, byte {best_byte} ({max_uniques} uniques)", "#55FF55")
                self.input_mapped.emit(name, cfg)
                self.trigger_start_time = 0
                self._advance_step(name)
                return
            else:
                # Digital Trigger Fallback (calibration.py lines 906-950)
                known_bits = set()
                known_axis_bytes = set()
                for r_id, r_data in self.profile.get("reports", {}).items():
                    for in_name, in_cfg in r_data.get("inputs", {}).items():
                        if in_cfg.get("type") == "button":
                            known_bits.add((r_id, in_cfg.get("byte"), in_cfg.get("bitmask")))
                        elif in_cfg.get("type") in ("axis", "trigger", "hat"):
                            known_axis_bytes.add((r_id, in_cfg.get("byte")))

                found = False
                for fid, counts in unique_counts.items():
                    if found: break
                    for byte_idx, u_set in enumerate(counts):
                        if found: break
                        if (fid, byte_idx) in known_axis_bytes: continue
                        if len(u_set) > 3: continue

                        for val in u_set:
                            base_val = base_state.get(fid, [])[byte_idx] if byte_idx < len(base_state.get(fid, [])) else 0
                            changed_bits = val ^ base_val
                            if changed_bits == 0: continue
                            for bit in range(8):
                                bitmask = 1 << bit
                                if changed_bits & bitmask:
                                    if (fid, byte_idx, bitmask) not in known_bits:
                                        best_full_id = fid
                                        best_byte = byte_idx
                                        best_mask = bitmask
                                        found = True
                                        break
                                if found: break

                if found and best_full_id:
                    if best_full_id not in self.profile["reports"]:
                        self.profile["reports"][best_full_id] = {"inputs": {}}
                    cfg = {"type": "button", "byte": best_byte, "bitmask": best_mask, "is_analog": False}
                    self.profile["reports"][best_full_id]["inputs"][name] = cfg
                    self.status_updated.emit(f"Detected Digital {name.upper()} Fallback at {best_full_id}, byte {best_byte}, mask {best_mask}", "#55FF55")
                    self.input_mapped.emit(name, cfg)
                    self.trigger_start_time = 0
                    self._advance_step(name)
                    return

        # -------------------------------------------------------------------
        # CATEGORY 4: AXES (Candidate sorting & signed/invert math)
        # calibration.py lines 980-1031
        # -------------------------------------------------------------------
        elif cat == "axes":
            known_axis_bytes = set()
            for r_id, r_data in self.profile.get("reports", {}).items():
                for in_name, in_cfg in r_data.get("inputs", {}).items():
                    if in_cfg.get("type") in ("axis", "trigger", "hat", "button"):
                        known_axis_bytes.add((r_id, in_cfg.get("byte")))
                        if in_cfg.get("length", 1) == 2:
                            known_axis_bytes.add((r_id, in_cfg.get("byte") + 1))

            candidates = []
            for fid, b_idx, curr_val, base_val in diffs:
                if (fid, b_idx) in known_axis_bytes:
                    continue
                amp8 = abs(curr_val - base_val)
                if amp8 > 40:
                    candidates.append({'full_id': fid, 'byte': b_idx, 'norm_amp': amp8 / 255.0, 'amp': amp8, 'curr': curr_val, 'base': base_val})

            if candidates:
                candidates.sort(reverse=True, key=lambda x: x['norm_amp'])
                top = candidates[0]
                fid = top['full_id']
                best_idx = top['byte']

                cfg = {"type": "axis", "byte": best_idx, "length": 1, "center": True}

                base_val = top['base']
                if base_val < 15 or base_val > 240:
                    cfg["signed"] = True

                curr_val = top['curr']
                def get_signed_val(val):
                    if not cfg.get("signed", False): return val
                    return val - 256 if val >= 128 else val

                delta = get_signed_val(curr_val) - get_signed_val(base_val)
                if name in ("lx", "rx") and delta < 0:
                    cfg["invert"] = True
                elif name in ("ly", "ry") and delta > 0:
                    cfg["invert"] = True

                if not cfg.get("signed", False):
                    centeredness = 1.0 - (abs(base_val - 127.5) / 127.5)
                else:
                    centeredness = 1.0 - (abs(get_signed_val(base_val)) / 128.0)

                cfg["centeredness"] = round(max(0.0, min(1.0, centeredness)), 3)
                cfg["range_confidence"] = round(min(1.0, top['amp'] / 127.0), 3)

                if fid not in self.profile["reports"]:
                    self.profile["reports"][fid] = {"inputs": {}}
                self.profile["reports"][fid]["inputs"][name] = cfg
                self.status_updated.emit(f"Detected {name.upper()} at {fid}, byte {best_idx}", "#55FF55")
                self.input_mapped.emit(name, cfg)
                self._advance_step(name)
                return

        # -------------------------------------------------------------------
        # CATEGORY 4.5: VERIFY STICK (Live telemetry stream)
        # -------------------------------------------------------------------
        elif cat == "verify_stick":
            stick_prefix = "left" if name == "verify_ls" else "right"
            x_key = "lx" if stick_prefix == "left" else "rx"
            y_key = "ly" if stick_prefix == "left" else "ry"

            x_cfg = None
            y_cfg = None
            rep_id = None
            for r_id, r_data in self.profile.get("reports", {}).items():
                inputs = r_data.get("inputs", {})
                if x_key in inputs and y_key in inputs:
                    x_cfg = inputs[x_key]
                    y_cfg = inputs[y_key]
                    rep_id = r_id
                    break

            if x_cfg and y_cfg and rep_id in self.latest_reports:
                latest = self.latest_reports[rep_id]
                base = self.baselines.get(rep_id, latest)
                b_x = x_cfg.get("byte", 0)
                b_y = y_cfg.get("byte", 0)
                if b_x < len(latest) and b_y < len(latest):
                    raw_x = latest[b_x]
                    raw_y = latest[b_y]
                    base_x = base[b_x] if b_x < len(base) else 128
                    base_y = base[b_y] if b_y < len(base) else 128

                    def decode_norm(val, base_val, cfg, is_y=False):
                        if cfg.get("signed", False):
                            s_val = val - 256 if val >= 128 else val
                            s_base = base_val - 256 if base_val >= 128 else base_val
                            delta = s_val - s_base
                        else:
                            delta = val - base_val
                        norm = delta / 128.0
                        if cfg.get("invert", False):
                            norm = -norm
                        if is_y:
                            norm = -norm
                        return max(-1.0, min(1.0, norm))

                    nx = decode_norm(raw_x, base_x, x_cfg)
                    ny = decode_norm(raw_y, base_y, y_cfg, is_y=True)
                    self.stick_position_updated.emit(stick_prefix, nx, ny)

        # -------------------------------------------------------------------
        # CATEGORY 5: HAT (4-bit nibble D-Pad switch)
        # calibration.py lines 1032-1042
        # -------------------------------------------------------------------
        elif cat == "hat":
            clean_hat_bytes = [d for d in diffs if ((d[2] & 0x0F) <= 7) and ((d[3] & 0x0F) > 7)]
            if len(clean_hat_bytes) == 1:
                fid, b_idx, _, _ = clean_hat_bytes[0]
                if fid not in self.profile["reports"]:
                    self.profile["reports"][fid] = {"inputs": {}}
                cfg = {"type": "hat", "byte": b_idx}
                self.profile["reports"][fid]["inputs"]["dpad"] = cfg
                self.status_updated.emit(f"Detected D-Pad Hat Switch at {fid}, byte {b_idx}", "#55FF55")
                self.input_mapped.emit("dpad", cfg)
                self._advance_step("dpad")
                return

    def _advance_step(self, released_name: str = "") -> None:
        """
        Prompt user to release button, wait until input returns to baseline,
        pause 0.8s for rest state settling, re-baseline, and advance to next step.
        """
        curr_step_name = self.steps[self.current_step_idx][0] if self.current_step_idx < len(self.steps) else "END"
        logger.info(f"[ADVANCE-START] Step {self.current_step_idx+1}/{len(self.steps)} ('{curr_step_name}') | released='{released_name}'")

        if released_name and self.current_step_idx < len(self.steps):
            name, cat, prompt = self.steps[self.current_step_idx]
            rel_upper = released_name.upper()
            self.status_updated.emit(f"✅ Registered {rel_upper}! RELEASE the button...", "#FFAA00")
            self.prompt_changed.emit(name, cat, f"RELEASE {rel_upper}...", self.current_step_idx, len(self.steps))
            try:
                QApplication.processEvents()
            except Exception:
                pass

            # Wait for button to be physically released (up to 1.5s)
            start_wait = time.time()
            while time.time() - start_wait < 1.5:
                time.sleep(0.04)
                try:
                    QApplication.processEvents()
                except Exception:
                    pass

                diff_count = 0
                for fid, latest_data in list(self.latest_reports.items()):
                    if fid in self.baselines:
                        b_data = self.baselines[fid]
                        if len(latest_data) == len(b_data):
                            for b_idx in range(len(latest_data)):
                                if latest_data[b_idx] != b_data[b_idx]:
                                    diff_count += 1
                if diff_count == 0:
                    logger.info(f"[RELEASE-CONFIRMED] Input '{released_name}' returned to baseline in {time.time()-start_wait:.2f}s")
                    break

        # Post-release rest settling delay (0.8s)
        logger.info(f"[SETTLING-START] Pausing 0.8s for rest state settling...")
        start_rest = time.time()
        while time.time() - start_rest < 0.8:
            time.sleep(0.04)
            try:
                QApplication.processEvents()
            except Exception:
                pass
        logger.info(f"[SETTLING-COMPLETE] Rest state settled.")

        # Re-baseline ONLY if rest state is clean to prevent dirty state contamination
        final_diff_count = 0
        for fid, latest_data in list(self.latest_reports.items()):
            if fid in self.baselines:
                b_data = self.baselines[fid]
                if len(latest_data) == len(b_data):
                    for b_idx in range(len(latest_data)):
                        if latest_data[b_idx] != b_data[b_idx]:
                            final_diff_count += 1

        if final_diff_count == 0:
            for fid, latest_data in list(self.latest_reports.items()):
                self.baselines[fid] = list(latest_data)
                logger.debug(f"[RE-BASELINE] {fid} clean rest baseline updated: {latest_data[:12]}")
        else:
            logger.warning(f"[RE-BASELINE-PRESERVED] Rest state dirty ({final_diff_count} diffs). Retaining original clean rest baseline!")

        # Clear per-step history
        self.click_counts.clear()
        self.byte_history.clear()
        self.button_byte_history.clear()
        self.trigger_start_time = 0
        self.trigger_samples.clear()

        self.current_step_idx += 1
        cooldown_sec = 0.8 if released_name in ("lx", "rx") else 0.5
        self.ignore_until_time = time.time() + cooldown_sec
        next_step_name = self.steps[self.current_step_idx][0] if self.current_step_idx < len(self.steps) else "DONE"
        logger.info(f"[ADVANCE-COMPLETE] Now on Step {self.current_step_idx+1}/{len(self.steps)} ('{next_step_name}') | Cooldown set to {cooldown_sec:.1f}s")
        self._emit_current_prompt()
        try:
            QApplication.processEvents()
        except Exception:
            pass

    def skip_step(self) -> None:
        logger.info(f"[USER-SKIP] Skiped step index {self.current_step_idx+1}")
        self.ignore_until_time = time.time() + 0.8
        self.status_updated.emit(f"Skipped step {self.current_step_idx + 1}.", "#FFFF55")
        self._advance_step()

    def undo_step(self) -> None:
        logger.info(f"[USER-UNDO] Called on step index {self.current_step_idx+1}")
        if self.current_step_idx > 0:
            self.ignore_until_time = time.time() + 0.8
            self.current_step_idx -= 1
            prev_name, _, _ = self.steps[self.current_step_idx]

            # Re-baseline ONLY if current rest state is clean to eliminate stale diffs
            final_diff_count = 0
            for fid, latest_data in list(self.latest_reports.items()):
                if fid in self.baselines:
                    b_data = self.baselines[fid]
                    if len(latest_data) == len(b_data):
                        for b_idx in range(len(latest_data)):
                            if latest_data[b_idx] != b_data[b_idx]:
                                final_diff_count += 1

            if final_diff_count == 0:
                for fid, latest_data in list(self.latest_reports.items()):
                    self.baselines[fid] = list(latest_data)
                    logger.debug(f"[UNDO-REBASELINE] {fid} reset to: {latest_data[:12]}")
            else:
                logger.warning(f"[UNDO-REBASELINE-PRESERVED] Rest state dirty ({final_diff_count} diffs). Retaining original clean rest baseline!")

            # Revert from profile
            for rep_data in self.profile.get("reports", {}).values():
                if "inputs" in rep_data and prev_name in rep_data["inputs"]:
                    del rep_data["inputs"][prev_name]
                    logger.info(f"[UNDO-REVERT] Deleted mapped input '{prev_name}' from profile")

            # Clear all per-step history
            self.click_counts.clear()
            self.byte_history.clear()
            self.button_byte_history.clear()
            self.trigger_start_time = 0
            self.trigger_samples.clear()

            logger.info(f"[UNDO-COMPLETE] Now rewound to step index {self.current_step_idx+1} ('{prev_name}')")
            self._emit_current_prompt()
            self.status_updated.emit(f"Undid step. Re-mapping '{prev_name.upper()}'...", "#FFFF55")
            try:
                QApplication.processEvents()
            except Exception:
                pass

    def redo_stick(self, stick_name: str) -> None:
        """
        Rewinds step index to the first step of the target stick ('left' or 'right'),
        deletes stick entries from profile, re-baselines, and re-engages listening.
        """
        target_key = "lx" if stick_name == "left" else "rx"
        target_idx = -1
        for idx, (s_key, _, _) in enumerate(self.steps):
            if s_key == target_key:
                target_idx = idx
                break

        if target_idx != -1:
            self.ignore_until_time = time.time() + 0.8
            self.current_step_idx = target_idx

            remove_keys = ["lx", "ly"] if stick_name == "left" else ["rx", "ry"]
            for rep_data in self.profile.get("reports", {}).values():
                if "inputs" in rep_data:
                    for r_key in remove_keys:
                        if r_key in rep_data["inputs"]:
                            del rep_data["inputs"][r_key]

            for fid, latest_data in list(self.latest_reports.items()):
                self.baselines[fid] = list(latest_data)

            self.click_counts.clear()
            self.byte_history.clear()
            self.button_byte_history.clear()
            self.trigger_start_time = 0
            self.trigger_samples.clear()

            self._emit_current_prompt()
            self.status_updated.emit(f"Rewound to '{target_key.upper()}'. Re-mapping {stick_name.upper()} stick...", "#FFFF55")
            try:
                QApplication.processEvents()
            except Exception:
                pass

    def confirm_stick(self) -> None:
        """User confirmed stick radar response on verification step."""
        if self.current_step_idx < len(self.steps):
            name, cat, _ = self.steps[self.current_step_idx]
            if cat == "verify_stick":
                self.ignore_until_time = time.time() + 0.5
                self.current_step_idx += 1
                self._emit_current_prompt()
                try:
                    QApplication.processEvents()
                except Exception:
                    pass
