"""Regression for scaling controls extending below a desktop panel."""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PyQt6 import QtCore, QtGui, QtWidgets  # noqa: E402
import SteamCommandGen as app_module  # noqa: E402


class WindowGeometryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def assert_inside_parents(self, widget, central):
        while widget is not central:
            parent = widget.parentWidget()
            self.assertIsNotNone(parent)
            self.assertTrue(
                parent.rect().contains(widget.geometry()),
                f"{widget.__class__.__name__} {widget.geometry()} "
                f"outside {parent.__class__.__name__} {parent.rect()}",
            )
            widget = parent

    def check_screen(self, width, height, font_points):
        screen = self.app.primaryScreen()
        old_geometry = screen.availableGeometry
        old_font = self.app.font()
        screen.availableGeometry = lambda: QtCore.QRect(0, 0, width, height)
        if font_points:
            self.app.setFont(QtGui.QFont("DejaVu Sans", font_points))
        try:
            for select_game in (False, True):
                window = None
                with self.subTest(select_game=select_game), \
                        patch.object(QtWidgets.QMessageBox, "information"), \
                        patch.object(app_module.GamescopeManager, "load_image"), \
                        patch.object(app_module.GamescopeManager, "load_icon"), \
                        patch.object(app_module, "get_active_launch_options", return_value=""):
                    try:
                        window = app_module.GamescopeManager()
                        window.screen = lambda: screen
                        window.show()
                        window.resize(window.maximumWidth(), window.maximumHeight())
                        self.app.processEvents()
                        window.scan_finished([{
                            "name": "Game " * 30,
                            "appid": "42",
                            "game_dir": "/steam/" + "very-long-directory/" * 50,
                            "executables": ["game.exe"],
                        }])
                        if select_game:
                            window.game_list.setCurrentRow(0)
                            window._game_pixmap = QtGui.QPixmap(400, 200)
                            window._fit_game_image()
                        self.app.processEvents()
                        initial_size = window.size()

                        for index in range(40):
                            (window.btn_fsr, window.btn_nis,
                             window.btn_nearest)[index % 3].click()
                            self.app.processEvents()
                            self.assertEqual(window.size(), initial_size)
                            self.assertLessEqual(window.height(), window.maximumHeight())
                            self.assertLessEqual(window.minimumSizeHint().height(), window.height())
                            central = window.centralWidget()
                            for control in (
                                    window.btn_fsr, window.btn_nis, window.btn_nearest,
                                    window.btn_mangohud, window.btn_mangohud_config,
                                    window.sharpness_labels.currentWidget(),
                                    window.sharpness_controls.currentWidget(),
                                    window.sharpness_slider if index % 3 == 0
                                    else window.nis_slider if index % 3 == 1
                                    else window.sharpness_controls,
                                    window.cmd_text, window.btn_preview,
                                    window.btn_kill_steam,
                            ):
                                self.assert_inside_parents(control, central)
                    finally:
                        if window is not None:
                            window.close()
        finally:
            screen.availableGeometry = old_geometry
            self.app.setFont(old_font)

    def test_1080p_with_desktop_panel_and_larger_font(self):
        self.check_screen(1920, 1021, 14)

    def test_720p(self):
        self.check_screen(1280, 720, None)

    def test_720p_with_larger_font(self):
        self.check_screen(1280, 720, 14)


if __name__ == "__main__":
    unittest.main()
