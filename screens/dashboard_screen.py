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
        # Main content area
        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.pack(fill="both", expand=True, side="top")

        # Bottom Navigation Bar
        self.nav_bar = ctk.CTkFrame(self, fg_color=self.tm.bg_card(), corner_radius=30, height=80, border_color=self.tm.border_main(), border_width=1)
        self.nav_bar.pack(side="bottom", fill="x", padx=20, pady=20)
        self.nav_bar.pack_propagate(False)
        
        nav_items = [("Home", "🏠"), ("Insights", "📈"), ("History", "🕒"), ("Subjects", "≡"), ("More", "•••")]
        self.nav_buttons = {}
        
        for name, icon in nav_items:
            btn = ctk.CTkButton(
                self.nav_bar, text=f"{icon}\n{name}", 
                fg_color="transparent", text_color=self.tm.text_sub(),
                hover=False, width=60, font=("Arial", 11),
                command=lambda n=name: self.show_view(n)
            )
            btn.pack(side="left", expand=True)
            self.nav_buttons[name] = btn

    def show_view(self, view_name, *args, **kwargs):
        # Update button colors if present in bottom nav
        if view_name in self.nav_buttons:
            for name, btn in self.nav_buttons.items():
                btn.configure(text_color=self.tm.accent_color() if name == view_name else self.tm.text_sub())

        # Clear current content
        if self.current_view is not None:
            self.current_view.destroy()

        # Load new view
        if view_name == "Home":
            from screens.home_view import HomeView
            self.current_view = HomeView(self.content_area, self.user_info)
        elif view_name == "Subjects":
            from screens.subjects_view import SubjectsView
            self.current_view = SubjectsView(self.content_area, self.user_info, self.show_view)
        elif view_name == "Tasks":
            from screens.tasks_view import TasksView
            self.current_view = TasksView(self.content_area, self.user_info, self.show_view, *args, **kwargs)
        elif view_name == "History":
            from screens.history_view import HistoryView
            self.current_view = HistoryView(self.content_area, self.user_info, self.show_view)
        elif view_name == "AllCompleted":
            from screens.all_completed_tasks_view import AllCompletedTasksView
            self.current_view = AllCompletedTasksView(self.content_area, self.user_info, self.show_view)
        elif view_name == "Insights":
            from screens.insights_view import InsightsView
            self.current_view = InsightsView(self.content_area, self.user_info, self.show_view)
        elif view_name == "AllPending":
            from screens.all_pending_tasks_view import AllPendingTasksView
            self.current_view = AllPendingTasksView(self.content_area, self.user_info, self.show_view)
        elif view_name == "More":
            from screens.more_view import MoreView
            self.current_view = MoreView(self.content_area, self.user_info, self.on_logout, self.reload_callback)
        else:
            self.current_view = PlaceholderView(self.content_area, view_name + " View")

        self.current_view.pack(fill="both", expand=True)
