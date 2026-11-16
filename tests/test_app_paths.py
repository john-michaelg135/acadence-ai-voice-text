import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from utils.app_paths import data_root


class PackagedDataTests(unittest.TestCase):
    def test_packaged_windows_data_survives_install_location_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            with (
                patch("sys.frozen", True, create=True),
                patch("sys.platform", "win32"),
                patch.dict("os.environ", {"LOCALAPPDATA": directory}),
                patch("sys.executable", "C:/Program Files/Acadence/Acadence.exe"),
            ):
                root = data_root()
                self.assertEqual(root, Path(directory) / "Acadence")
                self.assertTrue(root.is_dir())

    def test_linux_package_uses_xdg_data_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            with (
                patch("sys.frozen", True, create=True),
                patch("sys.platform", "linux"),
                patch.dict("os.environ", {"XDG_DATA_HOME": directory}),
            ):
                self.assertEqual(data_root(), Path(directory) / "Acadence")
