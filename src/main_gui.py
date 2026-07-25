"""
Entry point for the PySide6 UI.
Initializes the QApplication, applies the global deep space/glassmorphic QSS theme,
instantiates the main window and native system tray integration.
"""

import sys
from PySide6.QtWidgets import QApplication

from theme import GLOBAL_QSS
from app_window import MainWindow
from tray_icon import TrayManager

def main():
    """
    Main execution hook for the GUI process.
    Initializes non-blocking Qt execution loop.
    """
    # Create the application
    app = QApplication(sys.argv)
    
    # Enable quitting on last window closed? 
    # No, we want the system tray to keep it alive even if window is closed,
    # but the prompt implies hiding it toggles visibility. 
    # So we don't quit on last window closed.
    app.setQuitOnLastWindowClosed(False)

    # Apply global QSS glassmorphic deep space theme
    app.setStyleSheet(GLOBAL_QSS)

    # Initialize the main window frame shell
    main_window = MainWindow()

    # Initialize the native system tray
    # It stores the reference to prevent garbage collection
    tray_manager = TrayManager(main_window)

    # Launch the frame (hidden initially or shown depending on how we want it)
    # Typically we show it on boot
    main_window.show()

    # Enter the non-blocking event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
