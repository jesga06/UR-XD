import re
import time
import threading
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger('haptic_engine')


def parse_haptic_profile(profile_str: str) -> List[Dict[str, Any]]:
    """
    Parses haptic vibration profile strings into chronological event blocks.
    Syntax:
      - Keyword: RM[30% @ 0ms, dur=1500ms], LM[100% @ 1500ms, dur=250ms], BOTH[50% @ 0ms, dur=200ms]
      - Fallback: RM[30%, 0-1500ms], LM[100%, 1500-250ms]
    Returns a list of event dicts:
      [{'motor': 'RM', 'intensity': 0.30, 'start_s': 0.0, 'duration_s': 1.5, 'end_s': 1.5}, ...]
    """
    events = []
    if not profile_str or not profile_str.strip():
        return events

    # Regex matches blocks like: MOTOR[INTENSITY ... ]
    block_pattern = re.compile(r'(RM|LM|BOTH)\s*\[\s*([^\]]+)\s*\]', re.IGNORECASE)
    matches = block_pattern.findall(profile_str)

    for motor_raw, body in matches:
        motor = motor_raw.upper()
        
        # Extract intensity % (e.g. 30% or 0.3 or 30)
        intensity = 0.0
        int_match = re.search(r'(\d+(?:\.\d+)?)\s*%', body)
        if int_match:
            intensity = min(100.0, max(0.0, float(int_match.group(1)))) / 100.0
        else:
            # Fallback numeric match
            num_match = re.search(r'(\d+(?:\.\d+)?)', body)
            if num_match:
                val = float(num_match.group(1))
                intensity = val / 100.0 if val > 1.0 else val
                intensity = min(1.0, max(0.0, intensity))

        # Extract timing: keyword @ Xms, dur=Yms OR fallback X-Yms
        start_ms = 0.0
        dur_ms = 200.0 # Default 200ms

        start_match = re.search(r'@\s*(\d+(?:\.\d+)?)\s*ms', body, re.IGNORECASE)
        dur_match = re.search(r'dur\s*=\s*(\d+(?:\.\d+)?)\s*ms', body, re.IGNORECASE)

        if start_match:
            start_ms = float(start_match.group(1))
        if dur_match:
            dur_ms = float(dur_match.group(1))
            
        if not start_match and not dur_match:
            # Fallback for X-Yms syntax (e.g. 0-1500ms or 1500-250ms)
            range_match = re.search(r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*ms', body, re.IGNORECASE)
            if range_match:
                start_ms = float(range_match.group(1))
                dur_ms = float(range_match.group(2))

        start_s = max(0.0, start_ms / 1000.0)
        duration_s = max(0.01, dur_ms / 1000.0)
        end_s = start_s + duration_s

        if motor == 'BOTH':
            events.append({'motor': 'LM', 'intensity': intensity, 'start_s': start_s, 'duration_s': duration_s, 'end_s': end_s})
            events.append({'motor': 'RM', 'intensity': intensity, 'start_s': start_s, 'duration_s': duration_s, 'end_s': end_s})
        else:
            events.append({'motor': motor, 'intensity': intensity, 'start_s': start_s, 'duration_s': duration_s, 'end_s': end_s})

    events.sort(key=lambda x: x['start_s'])
    return events


class HapticEngine:
    """
    Asynchronous non-blocking vibration engine for Shift Layer transitions.
    Drives virtual gamepad rumble motors using high-resolution hardware timers.
    """

    def __init__(self, virtual_pad: Optional[Any] = None):
        self.virtual_pad = virtual_pad
        self.active_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.is_hijacked = False
        self.lock = threading.Lock()

    def set_virtual_pad(self, virtual_pad: Any) -> None:
        self.virtual_pad = virtual_pad

    def play_profile(self, profile_str: str) -> bool:
        events = parse_haptic_profile(profile_str)
        if not events:
            return False

        with self.lock:
            self.stop()
            self.stop_event.clear()
            self.is_hijacked = True
            self.active_thread = threading.Thread(
                target=self._run_timeline,
                args=(events,),
                daemon=True
            )
            self.active_thread.start()
        return True

    def stop(self) -> None:
        self.stop_event.set()
        if self.active_thread and self.active_thread.is_alive():
            self.active_thread.join(timeout=0.1)
        self.active_thread = None
        self.is_hijacked = False
        if self.virtual_pad and hasattr(self.virtual_pad, 'set_vibration'):
            try:
                self.virtual_pad.set_vibration(0, 0)
            except Exception:
                pass

    def _run_timeline(self, events: List[Dict[str, Any]]) -> None:
        if not events:
            self.is_hijacked = False
            return

        total_duration = max(e['end_s'] for e in events)
        t_start = time.perf_counter()

        while not self.stop_event.is_set():
            t_curr = time.perf_counter() - t_start
            if t_curr > total_duration:
                break

            # Compute active motor intensities at t_curr
            lm_val = 0.0
            rm_val = 0.0

            for e in events:
                if e['start_s'] <= t_curr <= e['end_s']:
                    if e['motor'] == 'LM':
                        lm_val = max(lm_val, e['intensity'])
                    elif e['motor'] == 'RM':
                        rm_val = max(rm_val, e['intensity'])

            if self.virtual_pad and hasattr(self.virtual_pad, 'set_vibration'):
                try:
                    lm_int = int(lm_val * 65535)
                    rm_int = int(rm_val * 65535)
                    self.virtual_pad.set_vibration(lm_int, rm_int)
                except Exception as ex:
                    logger.error(f"Error dispatching vibration: {ex}")

            time.sleep(0.010) # 10ms resolution check

        # Reset vibration and release hijacking control back to in-game rumble
        if self.virtual_pad and hasattr(self.virtual_pad, 'set_vibration'):
            try:
                self.virtual_pad.set_vibration(0, 0)
            except Exception:
                pass
        self.is_hijacked = False
