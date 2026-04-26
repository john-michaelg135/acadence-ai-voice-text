import customtkinter as ctk
from utils.theme_manager import ThemeManager
from database.db_manager import DatabaseManager
from datetime import datetime

class AdminDashboard(ctk.CTkFrame):
    def __init__(self, master, user_info, on_logout):
        self.tm = ThemeManager()
        super().__init__(master, fg_color="transparent")
        self.user_info = user_info
        self.on_logout = on_logout
        self.db = DatabaseManager()
        
        self.setup_ui()
        self.load_users()

    def setup_ui(self):
        # Header area
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(header_frame, text="Admin Portal", font=("Arial", 28, "bold"), text_color=self.tm.accent_color()).pack(side="left")
        ctk.CTkButton(header_frame, text="Log Out", width=80, fg_color="transparent", border_width=1, text_color=self.tm.text_main(),
                      command=self.on_logout).pack(side="right")

        # Intro text
        ctk.CTkLabel(self, text="System User Metrics", font=("Arial", 16), text_color=self.tm.text_sub()).pack(anchor="w", padx=20, pady=(0, 10))

        # Scrollable list for standard users
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=15, pady=10)

    def load_users(self):
        users = self.db.get_all_users_for_admin()
        
        if not users:
            ctk.CTkLabel(self.scroll_frame, text="No standard users registered in the system yet.", text_color=self.tm.text_sub()).pack(pady=30)
            return
            
        for user in users:
            self.create_user_card(user)

    def create_user_card(self, user):
        card = ctk.CTkFrame(self.scroll_frame, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=1, corner_radius=15)
        card.pack(fill="x", pady=8, padx=5)

        # Top row: Username
        top_frame = ctk.CTkFrame(card, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=(15, 5))
        
        ctk.CTkLabel(top_frame, text=f"@{user['username']}", font=("Arial", 18, "bold"), text_color=self.tm.text_main()).pack(side="left")
        
        # Format dates dynamically natively mapping standard SQLite Timestamp strings
        def fmt_time(t_str):
            if not t_str: return "Never logged in"
            try:
                dt = datetime.strptime(t_str, "%Y-%m-%d %H:%M:%S")
                return dt.strftime("%b %d, %Y %I:%M %p")
            except:
                return str(t_str)

        created_str = fmt_time(user['created_at'])
        last_login_str = fmt_time(user['last_login'])

        # Info body Data fields
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(info_frame, text=f"Joined: {created_str}", font=("Arial", 12), text_color=self.tm.text_sub()).pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"Last Active: {last_login_str}", font=("Arial", 12), text_color=self.tm.text_sub()).pack(anchor="w", pady=(2,0))
        
        duration_mins = user.get('login_duration') or 0
        ctk.CTkLabel(info_frame, text=f"Total Logged In Time: {duration_mins} min(s)", font=("Arial", 12), text_color=self.tm.text_sub()).pack(anchor="w", pady=(2,0))

        # Bottom metrics aggregates (Subjects / Tasks split block)
        metrics_frame = ctk.CTkFrame(card, fg_color=self.tm.bg_completed(), corner_radius=10)
        metrics_frame.pack(fill="x", padx=15, pady=(10, 15))
        
        ctk.CTkLabel(metrics_frame, text=f"📚 Subjects: {user['total_subjects']}", font=("Arial", 13, "bold"), text_color=self.tm.text_main()).pack(side="left", expand=True, pady=10)
        ctk.CTkLabel(metrics_frame, text=f"📋 Tasks: {user['total_tasks']}", font=("Arial", 13, "bold"), text_color=self.tm.text_main()).pack(side="right", expand=True, pady=10)
