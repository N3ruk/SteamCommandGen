"""Check Steam Deck launch options and per-game UI state."""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PyQt6 import QtCore, QtWidgets  # noqa: E402
import SteamCommandGen as app_module  # noqa: E402


class SteamDeckModeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def setUp(self):
        with patch.object(QtWidgets.QMessageBox, "information"), \
                patch.object(app_module.GamescopeManager, "load_image"):
            self.window = app_module.GamescopeManager()

    def tearDown(self):
        self.window.close()

    def test_exact_requested_command_and_original_format(self):
        options = dict(
            res_w=1280, res_h=720, out_w=1920, out_h=1080,
            immediate=True, nis_enabled=True, nis_sharpness=0,
            mangohud=True, steamdeck=True,
        )
        original = app_module.build_gamescope_command({**options, "steamdeck": False})
        self.assertEqual(
            original,
            "gamescope -w 1280 -h 720 -W 1920 -H 1080 "
            "--immediate-flips -F nis --sharpness 0 --mangoapp -f -- %command%",
        )
        command = app_module.build_gamescope_command(options)
        self.assertEqual(
            command,
            'env -u LD_PRELOAD gamescope -w 1280 -h 720 -W 1920 -H 1080 '
            '--immediate-flips -F nis --sharpness 0 --mangoapp -f -- '
            'env LD_PRELOAD="$LD_PRELOAD" %command%',
        )
        self.assertFalse(self.window.parse_gamescope_command(original)["steamdeck"])
        self.assertTrue(self.window.parse_gamescope_command(command)["steamdeck"])

    def test_generated_and_applied_commands_use_checkbox(self):
        self.window.base_res_combo.setCurrentIndex(1)
        self.window.out_res_combo.setCurrentIndex(1)
        self.window.chk_steamdeck.setChecked(True)
        self.window.generate_command()
        generated = self.window.cmd_text.toPlainText()
        self.assertTrue(generated.startswith("env -u LD_PRELOAD gamescope "))
        self.assertTrue(generated.endswith('env LD_PRELOAD="$LD_PRELOAD" %command%'))

        self.window.current_game = {"appid": "42"}
        with patch.object(app_module, "write_launch_options") as write, \
                patch.object(QtWidgets.QMessageBox, "information"):
            self.window.apply_command()
            write.assert_called_once_with("42", generated)

    def test_switching_games_resets_and_restores_mode(self):
        games = [
            {"appid": "42", "name": "Deck", "game_dir": "/tmp", "executables": []},
            {"appid": "43", "name": "Other", "game_dir": "/tmp", "executables": []},
        ]
        command = app_module.build_gamescope_command(dict(
            res_w=1280, res_h=720, out_w=1920, out_h=1080, steamdeck=True,
        ))
        items = []
        for game in games:
            item = QtWidgets.QListWidgetItem(game["name"])
            item.setData(QtCore.Qt.ItemDataRole.UserRole, game)
            items.append(item)
        with patch.object(self.window, "load_image"), \
                patch.object(app_module, "get_active_launch_options", side_effect=[command, "", command]):
            self.window.game_selected(items[0], None)
            self.assertTrue(self.window.chk_steamdeck.isChecked())
            self.window.game_selected(items[1], items[0])
            self.assertFalse(self.window.chk_steamdeck.isChecked())
            self.window.game_selected(items[0], items[1])
            self.assertTrue(self.window.chk_steamdeck.isChecked())


if __name__ == "__main__":
    unittest.main()
