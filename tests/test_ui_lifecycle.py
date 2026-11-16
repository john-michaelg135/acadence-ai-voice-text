import unittest
from unittest.mock import Mock, patch

from screens.dashboard_screen import DashboardScreen
from screens.voice_popup import VoiceRecordingPopup


class LifecycleTests(unittest.TestCase):
    def test_voice_window_destroy_stops_microphone_once(self):
        popup = object.__new__(VoiceRecordingPopup)
        stop = Mock()
        popup.stop_listening_func = stop
        popup._destroyed = False
        popup.is_listening = True
        with patch("customtkinter.CTkToplevel.destroy"):
            popup.destroy()
            popup.destroy()
        stop.assert_called_once()
        self.assertFalse(popup.is_listening)

    def test_dashboard_cleans_cached_views_before_destroying_tk(self):
        dashboard = object.__new__(DashboardScreen)
        cached = Mock()
        dashboard._view_cache = {"Subjects": cached}
        events = []
        cached.destroy.side_effect = lambda: events.append("cached")
        with patch("customtkinter.CTkFrame.destroy", side_effect=lambda: events.append("frame")):
            dashboard.destroy()
        self.assertEqual(events, ["cached", "frame"])
        self.assertEqual(dashboard._view_cache, {})


if __name__ == "__main__":
    unittest.main()
