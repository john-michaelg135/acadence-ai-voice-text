import customtkinter as ctk
from screens.auth_screen import AuthScreen
from screens.dashboard_screen import DashboardScreen

class AcadenceApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Acadence AI Voice Text")
        self.geometry("400x800")
        self.configure(fg_color="#FFFFFF")

        self.after(0, lambda: self.state('zoomed'))

        # Initialize the Authentication Screen
        self.auth_screen = AuthScreen(self, on_login_success=self.show_main_dashboard)
        self.auth_screen.pack(fill="both", expand=True)

    def show_main_dashboard(self, user_info):
        """
        Callback when login or guest mode is successful.
        user_info is a dict containing user details or None for guest.
        """
        self.auth_screen.pack_forget()
        
        self.dashboard_screen = DashboardScreen(self, user_info=user_info, on_logout=self.logout)
        self.dashboard_screen.pack(fill="both", expand=True)

    def logout(self):
        # Clear main dashboard
        if hasattr(self, 'dashboard_screen'):
            self.dashboard_screen.destroy()
            
        # Reinitialize Auth Screen
        self.auth_screen = AuthScreen(self, on_login_success=self.show_main_dashboard)
        self.auth_screen.pack(fill="both", expand=True)

if __name__ == "__main__":
    app = AcadenceApp()
    app.mainloop()
