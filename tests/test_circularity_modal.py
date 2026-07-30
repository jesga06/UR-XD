import sys
import os
import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from gui_v2.dialogs.circularity_modal import CircularityCalibrationModal, CircularityPolarCanvas
from gui_v2.services.theme_manager import ThemeManager

app = QApplication.instance() or QApplication([])


class TestCircularityModal(unittest.TestCase):
    def setUp(self):
        self.tm = ThemeManager.get_instance()

    def test_polar_canvas_rendering(self):
        canvas = CircularityPolarCanvas()
        canvas.resize(300, 300)
        bounds = [1.0] * 360
        canvas.update_data(bounds, 0.05, -0.02, 0.8, 0.6)

        # Trigger paintEvent onto QPixmap
        pixmap = QPixmap(300, 300)
        canvas.render(pixmap)
        self.assertFalse(pixmap.isNull())

    def test_modal_state_machine_and_theme(self):
        modal = CircularityCalibrationModal(section_name="Stick_Left")
        
        # Test initial state
        self.assertEqual(modal.calib_state, "REST")
        
        # Simulate 60 rest samples
        for _ in range(60):
            modal.update_telemetry({"lx": 0.01, "ly": -0.01})
            modal.update_loop()

        self.assertEqual(modal.calib_state, "WAIT_SWEEP")
        self.assertTrue(modal.btn_sweep.isEnabled())

        # Start sweep
        modal.start_sweep()
        self.assertEqual(modal.calib_state, "SWEEP")

        # Simulate 360 degree coverage
        for deg in range(360):
            modal.bounds_data[deg] = 1.0

        modal.update_loop()
        self.assertEqual(modal.calib_state, "DONE")
        self.assertTrue(modal.btn_save.isEnabled())

        # Test theme change responsiveness
        self.tm.set_token("accent_1", "#FF5500FF")
        modal.apply_theme()
        self.assertEqual(modal.calib_state, "DONE")

        modal.close()


if __name__ == "__main__":
    unittest.main()
