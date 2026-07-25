import unittest
import tkinter as tk
import customtkinter as ctk
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from gui import ToolTip


class TestToolTip(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = ctk.CTk()
            cls.root.withdraw()  # Don't show main test window
        except Exception as e:
            raise unittest.SkipTest(f"Tkinter window creation failed: {e}")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'root') and cls.root:
            cls.root.destroy()

    def test_tooltip_lifecycle(self):
        btn = ctk.CTkButton(self.root, text="Test Button")
        btn.pack()
        self.root.update_idletasks()

        tt = ToolTip(btn, "Test hover text")
        self.assertIsNone(tt.tipwindow)

        # Trigger enter (schedule)
        tt.enter()
        self.assertIsNotNone(tt.id)

        # Force showtip
        tt.showtip()
        self.assertIsNotNone(tt.tipwindow)

        # Trigger leave
        tt.leave()
        self.assertIsNone(tt.tipwindow)
        self.assertIsNone(tt.id)

    def test_tooltip_focus_out_dismissal(self):
        btn = ctk.CTkButton(self.root, text="Test Button Focus")
        btn.pack()
        self.root.update_idletasks()

        tt = ToolTip(btn, "Hover text focus out")
        tt.showtip()
        self.assertIsNotNone(tt.tipwindow)

        # Simulate FocusOut event on top level
        tt._on_top_focus_out(None)
        self.assertIsNone(tt.tipwindow)

    def test_tooltip_callable_text(self):
        btn = ctk.CTkButton(self.root, text="Test Dynamic")
        btn.pack()
        self.root.update_idletasks()

        tt = ToolTip(btn, lambda: "Dynamic Text")
        tt.showtip()
        self.assertIsNotNone(tt.tipwindow)
        tt.hidetip()
        self.assertIsNone(tt.tipwindow)


if __name__ == "__main__":
    unittest.main()
