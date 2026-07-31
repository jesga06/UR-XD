"""
Automated Diagnostic Report Packager & Log Sanitizer (package_report.py)
Collects diagnostic logs, applies export sanitation stripping all [QUOTE] tagged lines,
and packages them cleanly into 'issue_report.zip'.
"""

import os
import sys
import zipfile
import tempfile
import shutil

# Ensure src/ is on Python path to import logger_setup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

try:
    from logger_setup import filter_sanitized_logs
except ImportError:
    def filter_sanitized_logs(raw_log_text: str) -> str:
        if not raw_log_text:
            return ""
        lines = raw_log_text.splitlines()
        sanitized = [line for line in lines if "[QUOTE]" not in line]
        return "\n".join(sanitized)


def package_issue_report(output_zip: str = "issue_report.zip") -> bool:
    """
    Scans for diagnostic logs, sanitizes [QUOTE] flavor text from all .log files,
    and packages them into a compressed zip archive.
    """
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    logs_dir = os.path.join(root_dir, "diagnostics_logs")
    zip_path = os.path.join(root_dir, output_zip)

    # Clean previous zip if it exists
    if os.path.exists(zip_path):
        try:
            os.remove(zip_path)
        except Exception as e:
            print(f"[WARN] Failed to delete existing {zip_path}: {e}")

    # Build list of target files
    target_files = []

    # 1. Gather all files in diagnostics_logs/
    if os.path.exists(logs_dir):
        for entry in os.listdir(logs_dir):
            full_path = os.path.join(logs_dir, entry)
            if os.path.isfile(full_path):
                target_files.append((full_path, os.path.join("diagnostics_logs", entry)))

    # 2. Gather root log and config files if present
    root_candidates = [
        "wrapper.log",
        "wrapper_telemetry.log",
        "calibration.log",
        "diagnostics.json",
        "status.json",
        "config.ini"
    ]
    for c in root_candidates:
        full_path = os.path.join(root_dir, c)
        if os.path.exists(full_path):
            target_files.append((full_path, c))

    if not target_files:
        print("[WARN] No log files found to package.")
        return False

    print(f"[INFO] Packaging {len(target_files)} file(s) into '{output_zip}' with [QUOTE] sanitation...")

    with tempfile.TemporaryDirectory() as tmp_dir:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for src_file, arc_name in target_files:
                filename = os.path.basename(src_file)
                if filename.endswith(".log"):
                    # Apply log sanitation to remove [QUOTE] lines
                    try:
                        with open(src_file, 'r', encoding='utf-8', errors='ignore') as f:
                            raw_text = f.read()
                        sanitized_text = filter_sanitized_logs(raw_text)
                        
                        tmp_file_path = os.path.join(tmp_dir, filename)
                        with open(tmp_file_path, 'w', encoding='utf-8') as f:
                            f.write(sanitized_text)

                        zf.write(tmp_file_path, arc_name)
                        print(f"  [SANITIZED & ADDED] {arc_name}")
                    except Exception as e:
                        print(f"  [WARN] Sanitation fallback for {arc_name}: {e}")
                        zf.write(src_file, arc_name)
                else:
                    zf.write(src_file, arc_name)
                    print(f"  [ADDED] {arc_name}")

    print(f"[SUCCESS] Successfully created sanitized report at: {zip_path}")
    return True


if __name__ == "__main__":
    success = package_issue_report()
    sys.exit(0 if success else 1)
