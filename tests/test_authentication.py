import unittest
from types import SimpleNamespace
from unittest.mock import DEFAULT, Mock, patch

from main import AcadenceApp
from screens.auth_screen import AuthScreen


class AuthenticationTests(unittest.TestCase):
    def test_admin_session_cannot_bypass_login(self):
        with patch("main.ctk.CTk.__init__", return_value=None), patch.multiple(
            AcadenceApp, title=DEFAULT, geometry=DEFAULT, configure=DEFAULT,
            after=DEFAULT, protocol=DEFAULT, show_main_dashboard=DEFAULT,
        ), patch("main.load_fonts"), patch("main.AuthScreen") as auth, patch(
            "main.DatabaseManager"
        ) as database, patch("utils.session_manager.get_session", return_value="admin"), patch(
            "utils.session_manager.get_theme_settings", return_value={}
        ):
            database.return_value.get_user.return_value = {"id": 1, "is_admin": True}
            app = AcadenceApp()
            app.show_main_dashboard.assert_not_called()
            auth.return_value.pack.assert_called_once()

    def test_password_reset_requires_verification_for_current_account(self):
        for verified_username in (None, "previous-account"):
            screen = SimpleNamespace(
                target_username="student", _verified_recovery_username=verified_username,
                db=Mock(), new_pass_entry=Mock(), conf_new_pass_entry=Mock(),
                switch_mode=Mock(),
            )
            screen.new_pass_entry.get.return_value = "ValidPassword123!"
            screen.conf_new_pass_entry.get.return_value = "ValidPassword123!"
            with self.subTest(verified_username=verified_username), patch(
                "screens.auth_screen.messagebox.showerror"
            ), patch("screens.auth_screen.messagebox.showinfo"):
                AuthScreen.process_step3(screen)
                screen.db.admin_reset_password.assert_not_called()


if __name__ == "__main__":
    unittest.main()
