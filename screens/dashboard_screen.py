import customtkinter as ctk
from utils.theme_manager import ThemeManager

class PlaceholderView(ctk.CTkFrame):
    def __init__(self, master, title):
        super().__init__(master, fg_color="transparent")
        tm = ThemeManager()
        ctk.CTkLabel(self, text=title, font=("Arial", 24, "bold"), text_color=tm.text_main()).pack(expand=True)

class DashboardScreen(ctk.CTkFrame):
    def __init__(self, master, user_info, on_logout, reload_callback):
        self.tm = ThemeManager()
        super().__init__(master, fg_color=self.tm.bg_sub())
        self.user_info = user_info
        self.on_logout = on_logout
        self.reload_callback = reload_callback
        
        self.current_view = None
        self.setup_ui()
        self.show_view("Home")

    def setup_ui(self):
        # Sidebar Navigation
        self.sidebar = ctk.CTkFrame(self, fg_color=self.tm.bg_card(), width=220, border_color=self.tm.border_main(), border_width=1, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        # App Logo/Title
        ctk.CTkLabel(self.sidebar, text="Acadence", font=("Arial", 26, "bold"), text_color=self.tm.accent_color()).pack(pady=(40, 40))
        
        nav_items = [("Home", "🏠"), ("Insights", "📈"), ("History", "🕒"), ("Subjects", "≡"), ("Settings", "⚙️")]
        self.nav_buttons = {}
        
        for name, icon in nav_items:
            btn = ctk.CTkButton(
                self.sidebar, text=f"   {icon}   {name}", 
                fg_color="transparent", text_color=self.tm.text_sub(),
                hover_color=self.tm.bg_sub(), height=45, font=("Arial", 15, "bold"),
                anchor="w", command=lambda n=name: self.show_view(n)
            )
            btn.pack(fill="x", padx=15, pady=5)
            self.nav_buttons[name] = btn
            
        # Push logout to bottom
        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(expand=True)
        
        logout_btn = ctk.CTkButton(
            self.sidebar, text="    Log Out", 
            fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover(),
            height=45, font=("Arial", 15, "bold"), anchor="w", corner_radius=10,
            command=self.on_logout
        )
        logout_btn.pack(fill="x", padx=15, pady=(5, 30))

        # Main content area
        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.pack(side="right", fill="both", expand=True)

    def show_view(self, view_name, *args, **kwargs):
        internal_name = "More" if view_name == "Settings" else view_name

        # Update button colors if present in sidebar
        if view_name in self.nav_buttons:
            for name, btn in self.nav_buttons.items():
                if name == view_name:
                    btn.configure(text_color=self.tm.accent_color(), fg_color=self.tm.bg_sub())
                else:
                    btn.configure(text_color=self.tm.text_sub(), fg_color="transparent")

        # Clear current content
        if self.current_view is not None:
            self.current_view.destroy()

        # Load new view
        if internal_name == "Home":
            from screens.home_view import HomeView
            self.current_view = HomeView(self.content_area, self.user_info, self.show_view)
        elif internal_name == "Subjects":
            from screens.subjects_view import SubjectsView
            self.current_view = SubjectsView(self.content_area, self.user_info, self.show_view)
        elif internal_name == "Tasks":
            from screens.tasks_view import TasksView
            self.current_view = TasksView(self.content_area, self.user_info, self.show_view, *args, **kwargs)
        elif internal_name == "History":
            from screens.history_view import HistoryView
            self.current_view = HistoryView(self.content_area, self.user_info, self.show_view)
        elif internal_name == "AllCompleted":
            from screens.all_completed_tasks_view import AllCompletedTasksView
            self.current_view = AllCompletedTasksView(self.content_area, self.user_info, self.show_view)
        elif internal_name == "Insights":
            from screens.insights_view import InsightsView
            self.current_view = InsightsView(self.content_area, self.user_info, self.show_view)
        elif internal_name == "AllPending":
            from screens.all_pending_tasks_view import AllPendingTasksView
            self.current_view = AllPendingTasksView(self.content_area, self.user_info, self.show_view)
        elif internal_name == "More":
            from screens.more_view import MoreView
            self.current_view = MoreView(self.content_area, self.user_info, self.on_logout, self.reload_callback)
        else:
            self.current_view = PlaceholderView(self.content_area, view_name + " View")

        self.current_view.pack(fill="both", expand=True)
