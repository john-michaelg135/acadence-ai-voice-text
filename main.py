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
        
        # Setup Initial Theme Colors
        ctk.set_appearance_mode("Light")
        self.configure(fg_color=self.tm.bg_main())

        self.after(0, lambda: self.state('zoomed'))
        
        self.db = DatabaseManager()
        self.current_user = None
        self.session_start = None

        # Bind closing event to record active sessions
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Initialize the Authentication Screen
        self.auth_screen = AuthScreen(self, on_login_success=self.show_main_dashboard)
        self.auth_screen.pack(fill="both", expand=True)
        
    def reload_ui(self):
        """Rebuilds the current screen to apply theme changes dynamically."""
        self.configure(fg_color=self.tm.bg_main())
        if self.current_user:
            if hasattr(self, 'dashboard_screen'):
                self.dashboard_screen.destroy()
            self.show_main_dashboard(self.current_user)
        else:
            self.auth_screen.destroy()
            self.auth_screen = AuthScreen(self, on_login_success=self.show_main_dashboard)
            self.auth_screen.pack(fill="both", expand=True)

    def show_main_dashboard(self, user_info):
        """
        Callback when login or guest mode is successful.
        user_info is a dict containing user details or None for guest.
        """
        self.auth_screen.pack_forget()
        
        self.current_user = user_info
        if user_info and not self.session_start:
            self.session_start = datetime.datetime.now()
        
        if user_info and user_info.get('is_admin'):
            from screens.admin_dashboard import AdminDashboard
            self.dashboard_screen = AdminDashboard(self, user_info=user_info, on_logout=self.logout)
        else:
            self.dashboard_screen = DashboardScreen(self, user_info=user_info, on_logout=self.logout, reload_callback=self.reload_ui)
            
        self.dashboard_screen.pack(fill="both", expand=True)

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
        
        # Clear main dashboard
        if hasattr(self, 'dashboard_screen'):
            self.dashboard_screen.destroy()
            
        # Reinitialize Auth Screen using the current theme
        self.auth_screen = AuthScreen(self, on_login_success=self.show_main_dashboard)
        self.auth_screen.pack(fill="both", expand=True)

    def on_closing(self):
        self.record_session()
        self.quit()

if __name__ == "__main__":
    app = AcadenceApp()
    app.mainloop()
