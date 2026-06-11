import customtkinter as ctk
from screens.auth_screen import AuthScreen
from screens.dashboard_screen import DashboardScreen
from database.db_manager import DatabaseManager
from utils.theme_manager import ThemeManager
from utils.font_loader import load_fonts
import datetime

class AcadenceApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        load_fonts()  # Load custom Poppins fonts
        self.tm = ThemeManager()
        
        self.title("Acadence")
        self.geometry("1100x700")
        
        # Setup Initial Theme Colors from last saved session
        from utils.session_manager import get_theme_settings
        theme_prefs = get_theme_settings()
        ctk.set_appearance_mode(theme_prefs.get('appearance_mode', 'Light'))
        self.tm.set_accent(theme_prefs.get('accent_color', 'Pastel Purple'))
        self.configure(fg_color=self.tm.bg_main())

        # Delay zoomed state slightly so CustomTkinter has time to map the window
        self.after(200, lambda: self.state('zoomed'))
        
        self.db = DatabaseManager()
        self.current_user = None
        self.session_start = None

        # Bind closing event to record active sessions
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Initialize the Authentication Screen
        self.auth_screen = AuthScreen(self, on_login_success=self.show_main_dashboard)
        
        # Check for persistent login session
        from utils.session_manager import get_session
        saved_username = get_session()
        if saved_username:
            user = self.db.get_user(saved_username)
            if user and not user.get('is_disabled'):
                self.show_main_dashboard(user)
                return
                
        self.auth_screen.pack(fill="both", expand=True)
        
    def reload_ui(self):
        """Rebuilds the current screen to apply theme changes dynamically."""
        self.configure(fg_color=self.tm.bg_main())
        if self.current_user:
            current_view = "Home"
            if hasattr(self, 'dashboard_screen'):
                # Extract the current view name from the dashboard before destroying it
                current_view = getattr(self.dashboard_screen, '_active_nav', "Home")
                self.dashboard_screen.destroy()
            self.show_main_dashboard(self.current_user, initial_view=current_view, is_reload=True)
        else:
            self.auth_screen.destroy()
            self.auth_screen = AuthScreen(self, on_login_success=self.show_main_dashboard)
            self.auth_screen.pack(fill="both", expand=True)

    def show_main_dashboard(self, user_info, initial_view="Home", is_reload=False):
        """
        Callback when login or guest mode is successful.
        user_info is a dict containing user details or None for guest.
        """
        self.auth_screen.pack_forget()
        
        self.current_user = user_info
        
        # Handle persistent session saving
        from utils.session_manager import save_session, clear_session, get_theme_settings
        if user_info:
            if not user_info.get('is_admin'):
                save_session(user_info['username'])
                # Only load and apply settings if this is a fresh login, not a UI reload
                if not is_reload:
                    theme_prefs = get_theme_settings(user_info['id'])
                    ctk.set_appearance_mode(theme_prefs.get('appearance_mode', 'Light'))
                    self.tm.set_accent(theme_prefs.get('accent_color', 'Pastel Purple'))
            else:
                clear_session()
                
            if not self.session_start:
                self.session_start = datetime.datetime.now()
        else:
            clear_session()
        
        if user_info and user_info.get('is_admin'):
            from screens.admin_dashboard import AdminDashboard
            self.dashboard_screen = AdminDashboard(self, user_info=user_info, on_logout=self.logout)
        else:
            self.dashboard_screen = DashboardScreen(self, user_info=user_info, on_logout=self.logout, reload_callback=self.reload_ui, initial_view=initial_view)
            
        self.dashboard_screen.pack(fill="both", expand=True)
        
        # Start system notification scheduler for non-admin, non-guest users
        # Skip this if we are just reloading the UI theme to prevent spamming notifications
        if not is_reload and user_info and not user_info.get('is_admin'):
            self._start_notification_scheduler(user_info)
            
            # Send a welcome desktop notification
            from utils.notification_manager import NotificationManager
            NotificationManager.send(
                title=f"Welcome back, {user_info['username']}!",
                message="You are now logged into Acadence. Desktop notifications are active.",
                app_name="Acadence Login",
                timeout=7
            )

    def record_session(self):
        """Calculates the time spent logged in before killing the window/logout."""
        if self.current_user and self.session_start:
            delta = datetime.datetime.now() - self.session_start
            minutes = max(1, int(delta.total_seconds() / 60.0)) # Round up to 1 minute minimum
            self.db.update_login_duration(self.current_user['id'], minutes)
            self.session_start = None

    def logout(self):
        self.record_session()
        self.current_user = None
        
        from utils.session_manager import clear_session, get_theme_settings
        clear_session()
        
        # Load theme from session fallback (the last theme used)
        theme_prefs = get_theme_settings()
        ctk.set_appearance_mode(theme_prefs.get('appearance_mode', 'Light'))
        self.tm.set_accent(theme_prefs.get('accent_color', 'Pastel Purple'))
        self.configure(fg_color=self.tm.bg_main())
        
        # Stop the notification scheduler
        self._stop_notification_scheduler()
        
        # Clear main dashboard
        if hasattr(self, 'dashboard_screen'):
            self.dashboard_screen.destroy()
            
        # Reinitialize Auth Screen using the current theme
        self.auth_screen = AuthScreen(self, on_login_success=self.show_main_dashboard)
        self.auth_screen.pack(fill="both", expand=True)

    def on_closing(self):
        self.record_session()
        self._stop_notification_scheduler()
        self.quit()

    def _start_notification_scheduler(self, user_info):
        """Starts the background notification scheduler for the logged-in user."""
        try:
            from utils.notification_scheduler import NotificationScheduler
            from utils.session_manager import get_notification_settings
            scheduler = NotificationScheduler()
            settings = get_notification_settings(user_id=user_info['id'])
            scheduler.start(user_info['id'], user_info['username'], settings)
        except Exception as e:
            import traceback
            traceback.print_exc()

    def _stop_notification_scheduler(self):
        """Stops the background notification scheduler."""
        try:
            from utils.notification_scheduler import NotificationScheduler
            scheduler = NotificationScheduler()
            scheduler.stop()
        except Exception:
            pass

if __name__ == "__main__":
    app = AcadenceApp()
    app.mainloop()
