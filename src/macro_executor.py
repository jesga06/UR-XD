import json
import threading
import time
import os
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger('macro_executor')


class MacroExecutor:
    """
    Executes sequence macros (key press, release, wait) in a background thread.
    Supports toggle on/off execution and graceful sequence interruption.
    """

    def __init__(self, mapper: Any, filepath: str = 'macros.json'):
        self.mapper = mapper
        self.filepath = filepath
        self.macros: Dict[str, Any] = {}
        self.active_macro: Optional[str] = None
        self.stop_event = threading.Event()
        self.worker_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        self.load_macros()
        
    def load_macros(self, filepath: Optional[str] = None, clear_existing: bool = True) -> None:
        target = filepath or self.filepath
        try:
            if target and os.path.exists(target):
                with open(target, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        with self.lock:
                            if clear_existing:
                                self.macros.clear()
                            for k, v in loaded.items():
                                self.macros[k] = v
        except Exception as e:
            print(f"Error loading {target}: {e}")
            logger.error(f"Error loading {target}: {e}", exc_info=True)

    def stop_active_macro(self) -> None:
        with self.lock:
            self.stop_event.set()
            self.active_macro = None

    def on_button_release(self, macro_name: str) -> None:
        with self.lock:
            if self.active_macro == macro_name:
                macro_data = self.macros.get(macro_name)
                mode = "one_shot"
                if isinstance(macro_data, dict):
                    mode = str(macro_data.get("mode", "one_shot")).lower()
                if mode == "hold":
                    self.stop_event.set()
                    self.active_macro = None

    def execute_or_toggle(self, macro_name: str) -> None:
        if macro_name not in self.macros:
            self.load_macros()
        with self.lock:
            if self.active_macro == macro_name:
                # Toggle off if pressed again
                self.stop_event.set()
                self.active_macro = None
                return
            elif self.active_macro is not None:
                # Stop existing, start new
                self.stop_event.set()
                if self.worker_thread:
                    self.worker_thread.join(timeout=0.1)
            
            macro_data = self.macros.get(macro_name)
            if not macro_data:
                logger.warning(f"Macro '{macro_name}' not found in macros config.")
                return
                
            self.stop_event.clear()
            self.active_macro = macro_name
            self.worker_thread = threading.Thread(
                target=self._run_macro,
                args=(macro_name, macro_data,),
                daemon=True
            )
            self.worker_thread.start()

    def _sleep_ms(self, ms: float) -> None:
        if ms <= 0:
            return
        end_time = time.time() + (ms / 1000.0)
        while time.time() < end_time:
            if self.stop_event.is_set():
                break
            time.sleep(0.005)

    def _execute_string_step(self, step_str: str) -> None:
        s = step_str.strip()
        if not s:
            return

        s_lower = s.lower()
        if s_lower.startswith('wait:') or s_lower.startswith('wait '):
            val_part = s.split(':', 1)[1] if ':' in s else s.split(' ', 1)[1]
            val_clean = val_part.strip().lower()
            try:
                if 'ms' in val_clean:
                    ms = float(val_clean.replace('ms', '').strip())
                elif 's' in val_clean:
                    ms = float(val_clean.replace('s', '').strip()) * 1000.0
                else:
                    ms = float(val_clean)
            except ValueError:
                ms = 50.0
            self._sleep_ms(ms)
        elif s_lower.startswith('press:'):
            key = s.split(':', 1)[1].strip()
            if key:
                self.mapper._press(key)
        elif s_lower.startswith('release:'):
            key = s.split(':', 1)[1].strip()
            if key:
                self.mapper._release(key)
        else:
            # Standalone mapping step e.g. "keyboard:shift+a", "mouse:left", "a"
            self.mapper._press(s)
            self._sleep_ms(30.0)
            self.mapper._release(s)

    def _execute_step(self, step: Any) -> None:
        if self.stop_event.is_set():
            return

        if isinstance(step, dict):
            action = str(step.get('action', '')).strip().lower()
            if action == 'press':
                key = step.get('key') or step.get('mapping')
                if key:
                    self.mapper._press(str(key))
            elif action == 'release':
                key = step.get('key') or step.get('mapping')
                if key:
                    self.mapper._release(str(key))
            elif action == 'wait':
                try:
                    ms = float(step.get('ms', 0))
                except (ValueError, TypeError):
                    ms = 0.0
                self._sleep_ms(ms)
            else:
                act_str = step.get('action') or step.get('mapping') or step.get('key')
                if act_str:
                    self._execute_string_step(str(act_str))
        elif isinstance(step, str):
            self._execute_string_step(step)

    def _run_macro(self, macro_name: str, macro_data: Any) -> None:
        steps: List[Any] = []
        mode: str = "one_shot"

        if isinstance(macro_data, dict):
            mode = str(macro_data.get("mode", "one_shot")).lower()
            raw_steps = macro_data.get("steps", [])
            if isinstance(raw_steps, list):
                steps = raw_steps
            elif isinstance(raw_steps, str):
                steps = [s.strip() for s in raw_steps.split(",") if s.strip()]
        elif isinstance(macro_data, list):
            steps = macro_data
        elif isinstance(macro_data, str):
            steps = [s.strip() for s in macro_data.split(",") if s.strip()]

        if not steps:
            logger.warning(f"Macro '{macro_name}' has no valid steps to execute.")
            with self.lock:
                if self.active_macro == macro_name:
                    self.active_macro = None
            return

        try:
            while not self.stop_event.is_set():
                for step in steps:
                    if self.stop_event.is_set():
                        break
                    self._execute_step(step)

                if mode not in ("toggle", "hold", "loop"):
                    break
        except Exception as e:
            logger.error(f"Error during macro execution '{macro_name}': {e}", exc_info=True)
        finally:
            with self.lock:
                if self.active_macro == macro_name:
                    self.active_macro = None

