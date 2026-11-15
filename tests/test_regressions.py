import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import build_exe
from utils import session_manager
from utils.voice_manager import WhisperInferenceWorker


class BuildTests(unittest.TestCase):
    def test_build_does_not_package_secrets(self):
        with patch.dict("sys.modules", {"PyInstaller": Mock()}):
            with patch.object(build_exe.subprocess, "check_call") as run:
                build_exe.build_executable()
        args = run.call_args.args[0]
        self.assertFalse(any(".env" in arg for arg in args))
        self.assertEqual(args[:3], [build_exe.sys.executable, "-m", "PyInstaller"])


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "session.json"
        self.setting = patch.object(session_manager, "SESSION_FILE", str(self.path))
        self.setting.start()
        self.addCleanup(self.directory.cleanup)
        self.addCleanup(self.setting.stop)

    def test_non_object_json_is_ignored(self):
        for value in ([], None, "username", 1):
            with self.subTest(value=value):
                self.path.write_text(json.dumps(value), encoding="utf-8")
                self.assertIsNone(session_manager.get_session())

    def test_clear_session_preserves_preferences(self):
        session_manager.save_theme_settings({"appearance_mode": "Dark"})
        session_manager.save_session("student")
        session_manager.clear_session()
        self.assertIsNone(session_manager.get_session())
        self.assertEqual(session_manager.get_theme_settings()["appearance_mode"], "Dark")

    def test_invalid_preference_shape_uses_defaults(self):
        self.path.write_text('{"theme_settings": 7}', encoding="utf-8")
        self.assertEqual(session_manager.get_theme_settings()["appearance_mode"], "Light")

    def test_failed_write_preserves_previous_session(self):
        session_manager.save_session("student")
        with patch.object(session_manager.json, "dump", side_effect=OSError("disk full")):
            session_manager.save_session("replacement")
        self.assertEqual(session_manager.get_session(), "student")


class WhisperTests(unittest.TestCase):
    def test_missing_result_times_out(self):
        worker = object.__new__(WhisperInferenceWorker)
        worker.result_dict = {}
        worker.worker_thread = Mock()
        worker.worker_thread.is_alive.return_value = True
        responses = []
        waiter = threading.Thread(
            target=lambda: responses.append(worker.get_result("missing", timeout=0.02)),
            daemon=True,
        )
        waiter.start()
        waiter.join(timeout=0.5)
        self.assertFalse(waiter.is_alive(), "get_result ignored its timeout")
        self.assertFalse(responses[0]["success"])

    def test_finished_result_is_consumed(self):
        worker = object.__new__(WhisperInferenceWorker)
        worker.result_dict = {"ready": {"success": True, "text": "hello"}}
        worker.worker_thread = Mock()
        self.assertEqual(worker.get_result("ready")["text"], "hello")
        self.assertNotIn("ready", worker.result_dict)


if __name__ == "__main__":
    unittest.main()
