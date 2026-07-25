# src/gui.py
import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

class MainWindowStub(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ultimate 2C DInput Fix (PySide6 Ready)")
        self.setGeometry(100, 100, 800, 600)

        # Central container setup
        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)
        
        label = QLabel("PySide6 Engine Initialized.\nReady for UI component construction.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        self.setCentralWidget(central_widget)

def main():
    app = QApplication(sys.argv)
    window = MainWindowStub()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
