"""
UR-XD Wrapper Daemon (main.py)
This is the background daemon that connects to the physical HID controller,
decodes its reports, maps extra buttons to keyboard/mouse actions, and forwards
gamepad controls to the ViGEmBus virtual XInput controller.
It runs as a system tray icon using pystray.
"""
import time
import configparser
import sys
if sys.version_info[:2] not in ((3, 13), (3, 14)):
    print("WARNING: This script requires Python 3.13.x or 3.14.x. Other versions may fail to compile/load hidapi.")
    # We do not exit immediately in case they somehow made it work, but we warn them.
import os
import threading
import json
from hid_reader import HIDReader
from decoder import Decoder, ControllerState
from mapper import Mapper
from virtual_pad import VirtualPad
from config_manager import ControllerConfig, get_sanitized_filename
from hardware_chords import HardwareChordEngine
from backend_dinput import DInputBackend
from backend_base import ConnectionState
from backend_xinput import XInputBackend

import ctypes
import argparse
import subprocess
from logger_setup import setup_logger, setup_telemetry_logger
from single_instance import ensure_single_instance

is_debug_mode = False
logger = None


def hide_console():
    # Hide the console window
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
    except Exception:
        pass


def show_console():
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            ctypes.windll.user32.SetForegroundWindow(hwnd)
    except Exception:
        pass


gui_processes = []
gui_opened = False


def resolve_xinput_device_name(devices: list) -> str:
    """Query physical HID devices to resolve actual product string for XInput controllers."""
    for d in devices:
        prod = d.get('product_string')
        vid = d.get('vendor_id', 0)
        pid = d.get('product_id', 0)
        # Exclude virtual Xbox 360 controller spawned by vgamepad (0x045E:0x028E)
        if vid == 0x045E and pid == 0x028E:
            continue
        if prod and not any(kw in prod.upper() for kw in ("KEYBOARD", "MOUSE", "KB")):
            clean_name = prod
            if clean_name.startswith("Controller (") and clean_name.endswith(")"):
                clean_name = clean_name[12:-1]
            return clean_name
    return "XInput Gamepad"


def open_config(icon, item):
    global gui_opened
    if logger:
        logger.debug(f"[ENTER] open_config called with args: icon={icon}, item={item}")
    
    # Check if an existing GUI process is running
    for p in list(gui_processes):
        if p.poll() is None:
            gui_opened = True
            if logger:
                logger.debug("GUI instance is already running; skipping launch.")
            return

    if gui_opened:
        if logger:
            logger.debug("GUI already opened in this session; skipping launch.")
        return

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        gui_path = os.path.join(script_dir, 'main_gui.py')
        cmd = [sys.executable, gui_path]
        if is_debug_mode:
            cmd.append('--debug')
        if logger:
            logger.debug(f"  [DEBUG] Launching GUI with cmd: {cmd}")
        p = subprocess.Popen(cmd)
        gui_processes.append(p)
        gui_opened = True
        if logger:
            logger.debug(f"[EXIT] open_config completed successfully. PID: {p.pid}")
    except Exception as e:
        if logger:
            logger.error(f"Failed to open GUI: {e}", exc_info=True)
        else:
            print(f"Failed to open GUI: {e}")


def show_console_action(icon, item):
    show_console()


import tempfile

def write_status(state, device_name="None"):
    try:
        target_path = 'status.json'
        dir_name = os.path.dirname(os.path.abspath(target_path)) or '.'
        with tempfile.NamedTemporaryFile('w', dir=dir_name, delete=False, encoding='utf-8') as tf:
            status_str = state.name if hasattr(state, 'name') else str(state)
            json.dump({"status": status_str, "device": device_name}, tf)
            temp_name = tf.name
        os.replace(temp_name, target_path)
    except Exception as e:
        if logger:
            logger.error(f"Error writing status.json: {e}")
        else:
            print(f"Error writing status.json: {e}")


def quit_app(icon, item):
    icon.stop()
    write_status(ConnectionState.DISCONNECTED)
    os._exit(0)





def load_config(filename='config.ini'):
    config = configparser.ConfigParser()
    if os.path.exists(filename):
        config.read(filename, encoding='utf-8')
    return config


def main():
    """
    Main entry point for the wrapper daemon.
    Initializes virtual controllers, starts the HID reader thread,
    launches the configuration file poller, and runs the system tray icon loop.
    """
    global is_debug_mode, logger

    ensure_single_instance('main', 48124)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Enable verbose debugging logs')
    parser.add_argument(
        '--boot',
        action='store_true',
        help='Indicate wrapper was called by system initialization (prevents GUI auto-open)')
    args = parser.parse_args()

    is_debug_mode = args.debug
    logger = setup_logger('main', 'wrapper.log', is_debug_mode)
    telemetry_logger = setup_telemetry_logger('wrapper_telemetry.log')

    hide_console()
    write_status(ConnectionState.CONNECTING)
    logger.info("UR-XD Wrapper Starting...")

    config_file = 'config.ini'
    config = load_config(config_file)
    # debug_mode from config.ini is overridden by --log if desired, or we just
    # use is_debug_mode
    if not is_debug_mode:
        is_debug_mode = config.getboolean(
            'debug', 'print_reports', fallback=False)
        if is_debug_mode:
            logger = setup_logger('main', 'wrapper.log', is_debug_mode)

    logger.info("Scanning for connected devices with profiles...")
    devices = HIDReader.get_all_devices()
    selected_vid = None
    selected_pid = None
    hid_map_path = None    # path to the {VID}_{PID}.json HID map
    device_name = "Unknown Device"

    # --- Community database auto-update ---
    # The last successful fetch time is stored in config.ini under [community] db_last_updated
    # (Unix timestamp float). The database is refreshed if it is missing OR older than the
    # configured interval. This check runs on every wrapper launch, but the network request
    # only fires once per interval, independent of how many times the wrapper has been run.
    DB_UPDATE_INTERVAL_DAYS = config.getfloat('community', 'db_update_interval_days', fallback=7.0)
    DB_UPDATE_INTERVAL_SECS = DB_UPDATE_INTERVAL_DAYS * 86400.0

    db_path = os.path.join("profiles", "community", "database.json")
    db_last_updated = config.getfloat('community', 'db_last_updated', fallback=0.0)
    time_since_update = time.time() - db_last_updated
    db_needs_update = (not os.path.exists(db_path)) or (time_since_update >= DB_UPDATE_INTERVAL_SECS)

    if db_needs_update:
        reason = "not found locally" if not os.path.exists(db_path) else f"last updated {time_since_update / 86400:.1f} days ago"
        logger.info(f"Community database {reason}. Refreshing...")
        try:
            import community_fetcher
            community_fetcher.fetch_database(logger=logger)
            # Persist the new update timestamp into config.ini
            if not config.has_section('community'):
                config.add_section('community')
            config.set('community', 'db_last_updated', str(time.time()))
            config.set('community', 'db_update_interval_days', str(DB_UPDATE_INTERVAL_DAYS))
            with open(config_file, 'w', encoding='utf-8') as f:
                config.write(f)
            logger.info("Community database updated successfully.")
        except Exception as fe:
            logger.warning(f"Could not update community database: {fe}")
    else:
        logger.info(f"Community database is up to date (updated {time_since_update / 86400:.1f} days ago, interval: {DB_UPDATE_INTERVAL_DAYS:.0f} days).")


    for d in devices:
        vid = d.get('vendor_id', 0)
        pid = d.get('product_id', 0)
        # 1. Try to find a local HID map for this VID/PID
        potential_hid_map = f"profiles/{vid:04X}_{pid:04X}.json".lower()
        if os.path.exists(potential_hid_map):
            selected_vid = vid
            selected_pid = pid
            hid_map_path = potential_hid_map
            try:
                with open(hid_map_path, 'r', encoding='utf-8') as f:
                    map_data = json.load(f)
                    device_name = map_data.get('name', "Unknown Device")
            except:
                pass
            break
        else:
            # 2. Fall back to the community HID map database
            if os.path.exists(db_path):
                try:
                    with open(db_path, 'r', encoding='utf-8') as f:
                        db = json.load(f)
                    vid_pid_str = f"{vid:04X}:{pid:04X}".upper()
                    for entry_name, entry_data in db.items():
                        if vid_pid_str in entry_data.get("aliases", []):
                            # hid_map_file is relative to the REPO root, basename goes to community dir
                            hid_map_filename = os.path.basename(entry_data.get("hid_map_file", ""))
                            comm_map = os.path.join("profiles", "community", hid_map_filename)
                            if not os.path.exists(comm_map):
                                # Map not cached yet — selectively download it now
                                logger.info(f"Downloading community HID map for {vid_pid_str}...")
                                try:
                                    import community_fetcher
                                    community_fetcher.fetch_maps_for_devices([(vid, pid)], logger=logger)
                                except Exception as fe:
                                    logger.warning(f"Could not auto-download community HID map: {fe}")
                            if os.path.exists(comm_map):
                                selected_vid = vid
                                selected_pid = pid
                                hid_map_path = comm_map
                                with open(hid_map_path, 'r', encoding='utf-8') as mf:
                                    map_data = json.load(mf)
                                    device_name = map_data.get('name', "Unknown Device")
                                break
                except Exception:
                    pass
        if hid_map_path:
            break

    if not hid_map_path:
        # Check if XInput backend can initialize an XInput device directly
        test_xinput = XInputBackend()
        if test_xinput.initialize():
            logger.info(f"XInput controller detected on slot {test_xinput.connected_slot} (no DInput HID map required).")
            device_name = resolve_xinput_device_name(devices)
            hid_map_path = None
        else:
            logger.warning("No connected devices with a saved HID map or XInput slot found.")
            logger.info("Entering WAITING state for background device detection...")
            write_status(ConnectionState.WAITING, "No Controller Connected")

            # Open GUI if not called with --boot
            if not args.boot:
                logger.info("Auto-opening GUI in WAITING state...")
                open_config(None, None)

            # Continuous low-overhead background polling for devices in WAITING state
            while not hid_map_path:
                time.sleep(2.0)
                devices = HIDReader.get_all_devices()
                for d in devices:
                    vid = d.get('vendor_id', 0)
                    pid = d.get('product_id', 0)
                    potential_hid_map = f"profiles/{vid:04X}_{pid:04X}.json".lower()
                    if os.path.exists(potential_hid_map):
                        selected_vid = vid
                        selected_pid = pid
                        hid_map_path = potential_hid_map
                        try:
                            with open(hid_map_path, 'r', encoding='utf-8') as f:
                                map_data = json.load(f)
                                device_name = map_data.get('name', "Unknown Device")
                        except Exception:
                            pass
                        break

                if not hid_map_path:
                    test_xinput = XInputBackend()
                    if test_xinput.initialize():
                        device_name = resolve_xinput_device_name(devices)
                        hid_map_path = None
                        break

    logger.info(f"Connected device: {device_name} (HID map: {hid_map_path or 'None (XInput)'})")

    # Initialize user profile — named after the device
    # The user profile ({device_name}.json) holds remaps, deadzones, curves, etc.
    sanitized_name = get_sanitized_filename(device_name)
    controller_config_file = os.path.join("profiles", sanitized_name)
    controller_config = ControllerConfig(controller_config_file)
    
    # Save last connected device info to wrapper config (config.ini)
    if not config.has_section('controller'):
        config.add_section('controller')
    config.set('controller', 'last_device', device_name)
    # 'last_profile' key retained for backwards compatibility; now stores the HID map path
    config.set('controller', 'last_profile', hid_map_path or "")
    with open(config_file, 'w', encoding='utf-8') as f:
        config.write(f)

    # Load HID map to check for interface restriction
    req_ifaces = []
    if hid_map_path and os.path.exists(hid_map_path):
        try:
            with open(hid_map_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
                if "interfaces" in profile_data:
                    req_ifaces = profile_data["interfaces"]
                else:
                    req_iface = profile_data.get('interface_number', -1)
                    if req_iface != -1:
                        req_ifaces.append(req_iface)
        except Exception as e:
            logger.error(f"Failed to parse profile to check interface: {e}", exc_info=True)

    # Determine Backend Mode
    backend_mode = controller_config.data.get('backend', {}).get('mode', 'auto')
    
    backend = None
    if backend_mode in ('xinput', 'auto'):
        backend = XInputBackend()
        if not backend.initialize():
            if backend_mode == 'xinput':
                logger.error("XInput backend selected but no XInput device found.")
                write_status(ConnectionState.INIT_FAILED)
                show_console()
                time.sleep(5)
                sys.exit(1)
            else:
                logger.info("Auto mode: No XInput device found, falling back to DInput.")
                backend = None
        else:
            logger.info("Using XInput Backend.")

    if not backend:
        backend = DInputBackend(hid_map_path, selected_vid, selected_pid, req_ifaces)
        if not backend.initialize():
            logger.error("Failed to initialize DInput backend.")
            write_status(ConnectionState.INIT_FAILED)
            show_console()
            time.sleep(5)
            sys.exit(1)
        logger.info("Using DInput Backend.")
        
    try:
        mapper = Mapper(controller_config)
        virtual_pad = VirtualPad(controller_config)
        
        # Initialize Haptic Engine
        from haptic_engine import HapticEngine
        haptic_engine = HapticEngine(virtual_pad)
        virtual_pad.set_haptic_engine(haptic_engine)
        mapper.set_haptic_engine(haptic_engine)
        mapper.config = controller_config
        
        # Initialize Macro Executor and inject it into mapper
        from macro_executor import MacroExecutor
        macro_executor = MacroExecutor(mapper)
        mapper.macro_executor = macro_executor
        mapper.virtual_pad = virtual_pad
        
        # Initialize Hardware Chord Engine
        active_backend_mode = "dinput" if isinstance(backend, DInputBackend) else "xinput"
        hardware_chord_engine = HardwareChordEngine(controller_config, backend_mode=active_backend_mode)
        
    except Exception as e:
        logger.error(f"Failed to initialize mapper or virtual pad: {e}", exc_info=True)
        logger.info("Please ensure ViGEmBus is installed.")
        write_status(ConnectionState.INIT_FAILED)
        show_console()
        time.sleep(5)
        sys.exit(1)


    write_status(ConnectionState.CONNECTED, device_name)

    def rumble_callback(left_motor, right_motor):
        backend.set_vibration(left_motor / 255.0, right_motor / 255.0)

    virtual_pad.set_rumble_callback(rumble_callback)

    last_log_time = 0

    from utilities_backend import monitor

    is_interception_paused = False

    def toggle_pause_interception_action(icon, item):
        nonlocal is_interception_paused
        is_interception_paused = not is_interception_paused
        if is_interception_paused:
            mapper.reset()
            logger.info("Interception PAUSED. Physical inputs passing through without remapping.")
        else:
            logger.info("Interception RESUMED. Remapping active.")

    def reload_configuration_action(icon, item):
        try:
            nonlocal config
            config = load_config(config_file)
            controller_config.load()
            mapper.reload_config(controller_config)
            active_b_mode = "dinput" if isinstance(backend, DInputBackend) else "xinput"
            hardware_chord_engine.reload_config(controller_config, backend_mode=active_b_mode)
            virtual_pad.reload_config(controller_config)
            macro_executor.load_macros()
            logger.info("Configuration reloaded live from config.ini and profiles/.")
        except Exception as e:
            logger.error(f"Error reloading configuration: {e}", exc_info=True)

    def quit_app(icon, item):
        logger.info("Exiting application from system tray...")
        try:
            virtual_pad.destroy()
        except Exception as e:
            logger.error(f"Error destroying virtual pad: {e}")
        try:
            backend.shutdown()
        except Exception as e:
            logger.error(f"Error shutting down backend: {e}")
        write_status("Disconnected")
        for p in gui_processes:
            try:
                p.terminate()
            except Exception:
                pass
        if icon:
            icon.stop()
        os._exit(0)

    def data_handler(state: ControllerState):
        start_t = monitor.record_poll()
        nonlocal last_log_time
        current_time = time.time()

        if is_debug_mode and (current_time - last_log_time) >= 1.0:
            telemetry_logger.debug(f"[DECODED STATE] {state}")
            last_log_time = current_time

        if is_interception_paused:
            virtual_pad.process(state, paused=True)
        else:
            # Pipeline: Hardware Chords -> Mapper -> VirtualPad
            hardware_chord_engine.record_poll_interval()
            state = hardware_chord_engine.process(state)
            mapper.process(state)
            virtual_pad.process(state)
        
        monitor.record_process(start_t)
        monitor.broadcast_state(state)

    backend.set_callback(data_handler)
    threading.Thread(target=backend.poll, daemon=True).start()

    logger.info("Running daemon in background...")
    # Background config poller
    def config_poller():
        last_mtime = 0
        last_ini_mtime = 0
        if os.path.exists(controller_config_file):
            last_mtime = os.path.getmtime(controller_config_file)
        if os.path.exists(config_file):
            last_ini_mtime = os.path.getmtime(config_file)

        while True:
            time.sleep(1)  # Poll every 1 second for live tuning responsiveness
            try:
                changed = False
                if os.path.exists(controller_config_file):
                    current_mtime = os.path.getmtime(controller_config_file)
                    if current_mtime != last_mtime:
                        last_mtime = current_mtime
                        changed = True
                if os.path.exists(config_file):
                    current_ini_mtime = os.path.getmtime(config_file)
                    if current_ini_mtime != last_ini_mtime:
                        last_ini_mtime = current_ini_mtime
                        changed = True

                if changed:
                    controller_config.load()
                    mapper.reload_config(controller_config)
                    active_b_mode = "dinput" if isinstance(backend, DInputBackend) else "xinput"
                    hardware_chord_engine.reload_config(controller_config, backend_mode=active_b_mode)
                    virtual_pad.reload_config(controller_config)
                    macro_executor.load_macros()
                    logger.info("Controller config reloaded live!")
            except Exception as e:
                logger.error(f"Error reloading config: {e}", exc_info=True)

    t_poller = threading.Thread(target=config_poller, daemon=True)
    t_poller.start()

    logger.info("Daemon is running in the background.")

    # Automatically open GUI on initialization unless --boot is specified
    if not args.boot:
        logger.info("Auto-opening GUI...")
        open_config(None, None)


    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        backend.shutdown()
        write_status("Disconnected")
        for p in gui_processes:
            try:
                p.terminate()
            except Exception:
                pass
        os._exit(0)


if __name__ == "__main__":
    main()
