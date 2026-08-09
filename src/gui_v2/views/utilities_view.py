"""
Utilities & Diagnostics View for PySide6 UI (gui_v2).

Provides continuous 2Hz live telemetry monitoring (Polling Rate, Processing Latency, Max Delta),
synthetic benchmark execution, diagnostic suite launchers, and asynchronous Community HID Database updates.
"""

import os
import sys
import json
import time
import subprocess
import threading
import logging
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QGroupBox, QScrollArea, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, Slot, QTimer, QThread, Signal

from gui_v2.services.theme_manager import ThemeManager, color_to_rgba_str, color_to_hex6

logger = logging.getLogger("utilities_view")


class CommunityFetchThread(QThread):
    """Background worker thread for asynchronous community HID map updates."""
    finished_signal = Signal(str)

    def run(self):
        try:
            import community_fetcher
            result = community_fetcher.fetch_community_hid_maps()
            self.finished_signal.emit(str(result))
        except Exception as e:
            self.finished_signal.emit(f"Error: {e}")


class UtilitiesView(QWidget):
    """
    Utilities View featuring Live Telemetry Monitoring, Synthetic Packet Benchmark,
    Diagnostic Tool Launchers, and Community HID Profiles Fetcher.
    """

    def __init__(self, theme_manager: Optional[ThemeManager] = None, parent=None):
        super().__init__(parent)
        self.theme_mgr = theme_manager

        self.setup_ui()
        self.apply_theme()

        # 2Hz (500ms) timer for diagnostics.json telemetry updates
        self.telemetry_timer = QTimer(self)
        self.telemetry_timer.setInterval(500)
        self.telemetry_timer.timeout.connect(self._poll_diagnostics_file)
        self.telemetry_timer.start()

        if self.theme_mgr and hasattr(self.theme_mgr, "theme_changed"):
            self.theme_mgr.theme_changed.connect(self._on_theme_changed)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll Area Container
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self.container_widget = QWidget(self.scroll_area)
        self.container_layout = QVBoxLayout(self.container_widget)
        self.container_layout.setContentsMargins(16, 16, 16, 16)
        self.container_layout.setSpacing(20)

        # Title Header
        title_lbl = QLabel("Utilities & Diagnostic Suite", self.container_widget)
        title_lbl.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.container_layout.addWidget(title_lbl)

        # -------------------------------------------------------------------
        # 0. HIDHIDE ASSISTANT (DOUBLE-INPUT PREVENTION)
        # -------------------------------------------------------------------
        self.setup_hidhide_section()

        # -------------------------------------------------------------------
        # 1. LIVE TELEMETRY COUNTER PANEL
        # -------------------------------------------------------------------
        self.telemetry_card = QGroupBox("Live Latency & Telemetry Monitor", self.container_widget)
        tel_layout = QVBoxLayout(self.telemetry_card)
        tel_layout.setContentsMargins(16, 16, 16, 16)
        tel_layout.setSpacing(10)

        grid_layout = QHBoxLayout()

        # Polling Rate Box
        self.box_poll = QFrame(self.telemetry_card)
        box_poll_lay = QVBoxLayout(self.box_poll)
        self.lbl_poll_val = QLabel("0.0 Hz", self.box_poll)
        self.lbl_poll_val.setAlignment(Qt.AlignCenter)
        self.lbl_poll_val.setStyleSheet("font-size: 22px; font-weight: bold; color: #00F5A0;")
        lbl_poll_title = QLabel("Polling Rate", self.box_poll)
        lbl_poll_title.setAlignment(Qt.AlignCenter)
        lbl_poll_title.setStyleSheet("font-size: 11px; color: #AAAAAA;")
        box_poll_lay.addWidget(self.lbl_poll_val)
        box_poll_lay.addWidget(lbl_poll_title)

        # Avg Latency Box
        self.box_avg = QFrame(self.telemetry_card)
        box_avg_lay = QVBoxLayout(self.box_avg)
        self.lbl_avg_val = QLabel("0.000 ms", self.box_avg)
        self.lbl_avg_val.setAlignment(Qt.AlignCenter)
        self.lbl_avg_val.setStyleSheet("font-size: 22px; font-weight: bold; color: #A855F7;")
        lbl_avg_title = QLabel("Avg Processing Latency", self.box_avg)
        lbl_avg_title.setAlignment(Qt.AlignCenter)
        lbl_avg_title.setStyleSheet("font-size: 11px; color: #AAAAAA;")
        box_avg_lay.addWidget(self.lbl_avg_val)
        box_avg_lay.addWidget(lbl_avg_title)

        # Max Delta Box
        self.box_max = QFrame(self.telemetry_card)
        box_max_lay = QVBoxLayout(self.box_max)
        self.lbl_max_val = QLabel("0.000 ms", self.box_max)
        self.lbl_max_val.setAlignment(Qt.AlignCenter)
        self.lbl_max_val.setStyleSheet("font-size: 22px; font-weight: bold; color: #FF9900;")
        lbl_max_title = QLabel("Max Latency Delta", self.box_max)
        lbl_max_title.setAlignment(Qt.AlignCenter)
        lbl_max_title.setStyleSheet("font-size: 11px; color: #AAAAAA;")
        box_max_lay.addWidget(self.lbl_max_val)
        box_max_lay.addWidget(lbl_max_title)

        grid_layout.addWidget(self.box_poll)
        grid_layout.addWidget(self.box_avg)
        grid_layout.addWidget(self.box_max)
        tel_layout.addLayout(grid_layout)

        self.container_layout.addWidget(self.telemetry_card)

        # -------------------------------------------------------------------
        # 2. SYNTHETIC PACKET BENCHMARK
        # -------------------------------------------------------------------
        self.bench_card = QGroupBox("Synthetic Math Benchmark", self.container_widget)
        bench_layout = QVBoxLayout(self.bench_card)
        bench_layout.setContentsMargins(16, 16, 16, 16)
        bench_layout.setSpacing(10)

        bench_desc = QLabel(
            "Runs 10,000 simulated input packets through the raw decoder and trigonometric math engines to test CPU processing throughput.",
            self.bench_card
        )
        bench_desc.setWordWrap(True)
        bench_layout.addWidget(bench_desc)

        bench_action_lay = QHBoxLayout()
        self.btn_run_bench = QPushButton("Run Benchmark", self.bench_card)
        self.btn_run_bench.setFixedWidth(150)
        self.btn_run_bench.clicked.connect(self.run_synthetic_benchmark)
        bench_action_lay.addWidget(self.btn_run_bench)

        self.lbl_bench_result = QLabel("", self.bench_card)
        self.lbl_bench_result.setStyleSheet("font-weight: bold; color: #00F5A0; font-size: 12px;")
        bench_action_lay.addWidget(self.lbl_bench_result, stretch=1)

        bench_layout.addLayout(bench_action_lay)
        self.container_layout.addWidget(self.bench_card)

        # -------------------------------------------------------------------
        # 3. DIAGNOSTIC SUITE LAUNCHERS
        # -------------------------------------------------------------------
        self.diag_card = QGroupBox("Diagnostic Tools & Inspectors", self.container_widget)
        diag_layout = QVBoxLayout(self.diag_card)
        diag_layout.setContentsMargins(16, 16, 16, 16)
        diag_layout.setSpacing(12)

        diag_btns_lay = QHBoxLayout()

        self.btn_launch_tools = QPushButton("🛠️ Run Diagnostic Suite (.bat)", self.diag_card)
        self.btn_launch_tools.clicked.connect(self.launch_diagnostic_batch)

        self.btn_launch_graph = QPushButton("📈 Open Live Input Inspector", self.diag_card)
        self.btn_launch_graph.clicked.connect(self.launch_input_graph)

        diag_btns_lay.addWidget(self.btn_launch_tools)
        diag_btns_lay.addWidget(self.btn_launch_graph)
        diag_layout.addLayout(diag_btns_lay)

        self.container_layout.addWidget(self.diag_card)

        # -------------------------------------------------------------------
        # 4. COMMUNITY DATABASE UPDATER
        # -------------------------------------------------------------------
        self.comm_card = QGroupBox("Community HID Maps Database", self.container_widget)
        comm_layout = QVBoxLayout(self.comm_card)
        comm_layout.setContentsMargins(16, 16, 16, 16)
        comm_layout.setSpacing(10)

        comm_desc = QLabel(
            "Download and sync verified community hardware HID device mapping definitions directly from the remote repository.",
            self.comm_card
        )
        comm_desc.setWordWrap(True)
        comm_layout.addWidget(comm_desc)

        comm_action_lay = QHBoxLayout()
        self.btn_fetch_comm = QPushButton("📥 Community Profiles Fetcher", self.comm_card)
        self.btn_fetch_comm.setFixedWidth(230)
        self.btn_fetch_comm.clicked.connect(self.fetch_community_database)
        comm_action_lay.addWidget(self.btn_fetch_comm)

        self.lbl_comm_status = QLabel("", self.comm_card)
        self.lbl_comm_status.setStyleSheet("font-size: 11px; color: #EEEEEE;")
        comm_action_lay.addWidget(self.lbl_comm_status, stretch=1)

        comm_layout.addLayout(comm_action_lay)
        self.container_layout.addWidget(self.comm_card)
        self.container_layout.addStretch()
        self.scroll_area.setWidget(self.container_widget)
        main_layout.addWidget(self.scroll_area)

        # Initial HidHide status check
        self._refresh_hidhide_status()

    # -------------------------------------------------------------------
    # HIDHIDE ASSISTANT SECTION & SLOTS
    # -------------------------------------------------------------------
    def setup_hidhide_section(self):
        self.hidhide_card = QGroupBox("🛡️ Double-Input Prevention (HidHide Assistant)", self.container_widget)
        hh_layout = QVBoxLayout(self.hidhide_card)
        hh_layout.setContentsMargins(16, 16, 16, 16)
        hh_layout.setSpacing(12)

        # Status indicators row
        status_row = QHBoxLayout()
        self.lbl_hh_driver = QLabel("Driver: Checking...", self.hidhide_card)
        self.lbl_hh_whitelist = QLabel("Whitelist: Checking...", self.hidhide_card)
        self.lbl_hh_cloak = QLabel("Cloak: Checking...", self.hidhide_card)
        for lbl in (self.lbl_hh_driver, self.lbl_hh_whitelist, self.lbl_hh_cloak):
            lbl.setStyleSheet("font-size: 11px; padding: 4px 8px; border-radius: 4px; background: rgba(255,255,255,0.05);")
            status_row.addWidget(lbl)
        status_row.addStretch()
        hh_layout.addLayout(status_row)

        # Action buttons row
        btn_row = QHBoxLayout()
        self.btn_hh_whitelist = QPushButton("⚡ Whitelist App", self.hidhide_card)
        self.btn_hh_cloak = QPushButton("🛡️ Enable Cloak", self.hidhide_card)
        self.btn_hh_uncloak = QPushButton("🔓 Disable Cloak", self.hidhide_card)
        self.btn_hh_replug = QPushButton("🔄 Software Re-Plug", self.hidhide_card)

        self.btn_hh_whitelist.clicked.connect(self._on_hh_whitelist_clicked)
        self.btn_hh_cloak.clicked.connect(self._on_hh_cloak_clicked)
        self.btn_hh_uncloak.clicked.connect(self._on_hh_uncloak_clicked)
        self.btn_hh_replug.clicked.connect(self._on_hh_replug_clicked)

        for btn in (self.btn_hh_whitelist, self.btn_hh_cloak, self.btn_hh_uncloak, self.btn_hh_replug):
            btn.setMinimumHeight(32)
            btn_row.addWidget(btn)

        hh_layout.addLayout(btn_row)

        # Plain language warning note
        note_lbl = QLabel("Note: If the button doesn't work, unplug your controller and plug it back in.", self.hidhide_card)
        note_lbl.setStyleSheet("font-size: 11px; color: #FFC107; font-style: italic;")
        hh_layout.addWidget(note_lbl)

        self.container_layout.addWidget(self.hidhide_card)

    def _refresh_hidhide_status(self):
        """Refreshes HidHide status labels based on current system state."""
        try:
            import hidhide_helper
            st = hidhide_helper.get_hidhide_status()

            if not st["installed"]:
                self.lbl_hh_driver.setText("Driver: 🔴 Not Found")
                self.lbl_hh_whitelist.setText("Whitelist: --")
                self.lbl_hh_cloak.setText("Cloak: --")
                for btn in (self.btn_hh_whitelist, self.btn_hh_cloak, self.btn_hh_uncloak, self.btn_hh_replug):
                    btn.setEnabled(False)
                return

            for btn in (self.btn_hh_whitelist, self.btn_hh_cloak, self.btn_hh_uncloak, self.btn_hh_replug):
                btn.setEnabled(True)

            self.lbl_hh_driver.setText("Driver: 🟢 Installed")
            if st["app_registered"]:
                self.lbl_hh_whitelist.setText("Whitelist: 🟢 sys.executable Registered")
            else:
                self.lbl_hh_whitelist.setText("Whitelist: 🟡 Not Registered")

            if st["cloak_active"]:
                self.lbl_hh_cloak.setText("Cloak: 🟢 Active")
            else:
                self.lbl_hh_cloak.setText("Cloak: 🔴 Inactive")
        except Exception as e:
            logger.debug(f"Error refreshing HidHide status: {e}")

    def _on_hh_whitelist_clicked(self):
        """Registers sys.executable into HidHide whitelist."""
        try:
            import hidhide_helper
            ok, msg = hidhide_helper.register_app_whitelist()
            self._refresh_hidhide_status()
            if ok:
                QMessageBox.information(self, "HidHide Whitelist", f"Successfully registered app:\n{msg}")
            else:
                QMessageBox.warning(self, "HidHide Whitelist Error", f"Could not register whitelist:\n{msg}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _on_hh_cloak_clicked(self):
        """Queries PnP instance IDs, adds them to blocklist, and enables global cloak."""
        try:
            import hidhide_helper
            ids = hidhide_helper.get_pnp_instance_ids()
            added_count = 0
            for iid in ids:
                ok, _ = hidhide_helper.add_device_to_blocklist(iid)
                if ok:
                    added_count += 1

            ok_cloak, msg = hidhide_helper.set_global_cloak(True)
            self._refresh_hidhide_status()
            if ok_cloak:
                QMessageBox.information(
                    self, "HidHide Cloaking Enabled",
                    f"Global cloaking is now ON.\nAdded {added_count} device node(s) to blocklist.\n\n"
                    "Note: If the button doesn't work, unplug your controller and plug it back in."
                )
            else:
                QMessageBox.warning(self, "HidHide Error", f"Could not enable global cloaking:\n{msg}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _on_hh_uncloak_clicked(self):
        """Toggles global cloaking OFF via --cloak-off."""
        try:
            import hidhide_helper
            ok, msg = hidhide_helper.set_global_cloak(False)
            self._refresh_hidhide_status()
            if ok:
                QMessageBox.information(self, "HidHide Cloaking Disabled", "Global cloaking is now OFF.")
            else:
                QMessageBox.warning(self, "HidHide Error", f"Could not disable global cloaking:\n{msg}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _on_hh_replug_clicked(self):
        """Executes a software PnP device restart on detected controller nodes."""
        try:
            import hidhide_helper
            ids = hidhide_helper.get_pnp_instance_ids()
            if not ids:
                QMessageBox.warning(
                    self, "No Controller Found",
                    "No connected HID/USB controller PnP instance IDs detected.\n\n"
                    "Note: If the button doesn't work, unplug your controller and plug it back in."
                )
                return

            restart_count = 0
            for iid in ids:
                ok, _ = hidhide_helper.restart_pnp_device(iid)
                if ok:
                    restart_count += 1

            QMessageBox.information(
                self, "Software Re-Plug Completed",
                f"Restarted {restart_count} PnP device node(s).\n\n"
                "Note: If the button doesn't work, unplug your controller and plug it back in."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # -------------------------------------------------------------------
    # TELEMETRY & DIAGNOSTICS SLOTS
    # -------------------------------------------------------------------
    @Slot(dict)
    def update_diagnostics_telemetry(self, stats: dict):
        """Updates polling rate, avg process ms, and max process ms at 2Hz."""
        poll_hz = float(stats.get("polling_rate_hz", 0.0))
        avg_ms = float(stats.get("avg_process_ms", 0.0))
        max_ms = float(stats.get("max_process_ms", 0.0))

        self.lbl_poll_val.setText(f"{poll_hz:.1f} Hz")
        self.lbl_avg_val.setText(f"{avg_ms:.3f} ms")
        self.lbl_max_val.setText(f"{max_ms:.3f} ms")

    def _poll_diagnostics_file(self):
        """Polls diagnostics.json or live backend monitor stats every 500ms (2Hz)."""
        found = False
        if os.path.exists("diagnostics.json"):
            try:
                with open("diagnostics.json", "r", encoding="utf-8") as f:
                    stats = json.load(f)
                if isinstance(stats, dict) and stats:
                    self.update_diagnostics_telemetry(stats)
                    found = True
            except Exception as e:
                logger.debug(f"Diagnostics file poll exception: {e}")

        if not found:
            try:
                from utilities_backend import monitor
                stats = monitor.get_snapshot()
                if stats:
                    self.update_diagnostics_telemetry(stats)
            except Exception:
                pass

    # -------------------------------------------------------------------
    # BENCHMARK ENGINE
    # -------------------------------------------------------------------
    def run_synthetic_benchmark(self):
        """Runs 10,000 simulated packets through decoding and math utilities."""
        self.lbl_bench_result.setText("Running benchmark...")
        self.btn_run_bench.setEnabled(False)

        def bench_task():
            try:
                sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
                import math_utils
                from decoder import Decoder
                from hid_reader import RawHIDReport

                decoder = Decoder("")
                decoder.reports_config = {"0": {"inputs": {"lx": {"type": "axis", "byte": 1}}}}

                start_t = time.perf_counter()
                for _ in range(10000):
                    rep = RawHIDReport(0, bytes([0, 128]), 0.0)
                    state = decoder.decode(rep)
                    lx, ly = math_utils.process_analog_stick(state.lx, state.ly, 0.1, 0.1, "bezier", 2.0, 0.0, 1.0)
                end_t = time.perf_counter()

                total_ms = (end_t - start_t) * 1000.0
                per_packet_us = (total_ms / 10000.0) * 1000.0
                res_str = f"Score: 10,000 packets in {total_ms:.1f}ms (Avg: {per_packet_us:.2f}µs / packet)"
            except Exception as e:
                res_str = f"Benchmark Error: {e}"

            # Post back to main GUI thread
            QTimer.singleShot(0, lambda: self._on_benchmark_done(res_str))

        threading.Thread(target=bench_task, daemon=True).start()

    def _on_benchmark_done(self, result_text: str):
        self.lbl_bench_result.setText(result_text)
        self.btn_run_bench.setEnabled(True)

    # -------------------------------------------------------------------
    # LAUNCHERS
    # -------------------------------------------------------------------
    def launch_diagnostic_batch(self):
        """Triggers tools_and_diagnostics.bat externally."""
        bat_path = "tools_and_diagnostics.bat"
        if os.path.exists(bat_path):
            try:
                subprocess.Popen(["cmd.exe", "/c", bat_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
            except Exception as e:
                QMessageBox.critical(self, "Launch Error", f"Failed to launch {bat_path}: {e}")
        else:
            QMessageBox.warning(self, "File Not Found", f"Could not find {bat_path} in working directory.")

    def launch_input_graph(self):
        """Launches live input graph script (input_graph.py)."""
        script_path = os.path.join("src", "input_graph.py")
        if not os.path.exists(script_path):
            script_path = "input_graph.py"

        if os.path.exists(script_path):
            try:
                subprocess.Popen([sys.executable, script_path])
            except Exception as e:
                QMessageBox.critical(self, "Launch Error", f"Failed to launch input graph: {e}")
        else:
            QMessageBox.warning(self, "File Not Found", f"Could not locate input_graph.py.")

    # -------------------------------------------------------------------
    # COMMUNITY FETCHING
    # -------------------------------------------------------------------
    def fetch_community_database(self):
        """Executes community_fetcher.py asynchronously."""
        self.btn_fetch_comm.setEnabled(False)
        self.lbl_comm_status.setText("Syncing remote community database...")

        self.fetch_thread = CommunityFetchThread(self)
        self.fetch_thread.finished_signal.connect(self._on_community_fetch_finished)
        self.fetch_thread.start()

    def _on_community_fetch_finished(self, status_msg: str):
        self.btn_fetch_comm.setEnabled(True)
        self.lbl_comm_status.setText(status_msg)
        if "Success" in status_msg:
            QMessageBox.information(self, "Community DB Update", status_msg)
        else:
            QMessageBox.warning(self, "Community DB Update", status_msg)

    # -------------------------------------------------------------------
    # THEME STYLING
    # -------------------------------------------------------------------
    def _on_theme_changed(self, tokens: dict):
        self.apply_theme()

    def apply_theme(self):
        """Applies dynamic QSS using ThemeManager tokens."""
        if not self.theme_mgr:
            return

        bg_col = self.theme_mgr.get_color("background")
        acc1_col = self.theme_mgr.get_color("accent_1")
        acc2_col = self.theme_mgr.get_color("accent_2")

        bg_str = color_to_hex6(bg_col)
        acc1_hex = color_to_hex6(acc1_col)
        acc2_hex = color_to_hex6(acc2_col)

        acc1_bg = color_to_rgba_str(acc1_col, 0.12)
        acc1_hover = color_to_rgba_str(acc1_col, 0.25)
        border1_str = color_to_rgba_str(acc1_col, 0.4)

        box_bg = color_to_rgba_str(bg_col, 0.7)

        qss = f"""
        QWidget {{
            background-color: {bg_str};
            color: #FFFFFF;
        }}
        QGroupBox {{
            background-color: {color_to_rgba_str(bg_col, 0.6)};
            border: 1.5px solid {border1_str};
            border-radius: 6px;
            margin-top: 10px;
            font-weight: bold;
            font-size: 13px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 2px 8px;
            color: {acc1_hex};
        }}
        QFrame {{
            background-color: {box_bg};
            border: 1px solid {border1_str};
            border-radius: 6px;
            padding: 8px;
        }}
        QPushButton {{
            background-color: {acc1_bg};
            border: 1px solid {border1_str};
            border-radius: 4px;
            color: #FFFFFF;
            padding: 6px 14px;
            font-weight: bold;
            font-size: 11px;
        }}
        QPushButton:hover {{
            background-color: {acc1_hover};
            border-color: {acc1_hex};
        }}
        """
        self.setStyleSheet(qss)
