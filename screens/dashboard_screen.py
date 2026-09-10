import customtkinter as ctk
from utils.theme_manager import ThemeManager
from database.db_manager import DatabaseManager
from screens.walkthrough_popup import WalkthroughPopup
from utils.animation_manager import animate_slide, animate_slide_in, _resolve_color
from utils.logger import logger

class PlaceholderView(ctk.CTkFrame):
    def __init__(self, master, title):
        super().__init__(master, fg_color="transparent")
        tm = ThemeManager()
        ctk.CTkLabel(self, text=title, font=(tm.main_font(), 24, "bold"), text_color=tm.text_main()).pack(expand=True)

class DashboardScreen(ctk.CTkFrame):
    def __init__(self, master, user_info, on_logout, reload_callback, initial_view="Home"):
        self.tm = ThemeManager()
        super().__init__(master, fg_color=self.tm.bg_sub())
        self.user_info = user_info
        self.on_logout = on_logout
        self.reload_callback = reload_callback
        
        self.current_view = None
        self._current_view_key = None
        self._view_cache = {}
        self._active_nav = None
        self.setup_ui()
        self.show_view(initial_view)
        
        # Trigger walkthrough if not seen
        if not self.user_info.get("has_seen_walkthrough"):
            self.after(10, self.show_walkthrough)

    def show_walkthrough(self):
        def on_complete():
            db = DatabaseManager()
            db.mark_walkthrough_seen(self.user_info["id"])
            self.user_info["has_seen_walkthrough"] = 1
            
        WalkthroughPopup(self, on_complete)

    def setup_ui(self):
        # Sidebar Navigation
        self.sidebar = ctk.CTkFrame(self, fg_color=self.tm.bg_card(), width=220, border_color=self.tm.border_main(), border_width=1, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        # App Logo/Title
        ctk.CTkLabel(self.sidebar, text="Acadence", font=(self.tm.main_font(), 26, "bold"), text_color=self.tm.accent_color()).pack(pady=(40, 40))
        
        nav_items = [("Home", "🏠"), ("Insights", "📈"), ("History", "🕒"), ("Subjects", "📂"), ("Notifications", "🔔"), ("Settings", "⚙️")]
        self.nav_buttons = {}
        self.nav_indicators = {}
        
        for name, icon in nav_items:
            # Container for indicator + button to ensure perfect alignment
            container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            container.pack(fill="x", padx=10, pady=4)
            
            # The vertical indicator pill
            indicator = ctk.CTkFrame(container, fg_color="transparent", width=4, height=28, corner_radius=2)
            indicator.pack(side="left", padx=(0, 5))
            self.nav_indicators[name] = indicator
            
            btn = ctk.CTkButton(
                container, text=f"   {icon}   {name}", 
                fg_color="transparent", text_color=self.tm.text_sub(),
                hover_color=self.tm.bg_sub(), height=45, font=(self.tm.main_font(), 15, "bold"),
                corner_radius=10, anchor="w", command=lambda n=name: self.show_view(n)
            )
            btn.pack(side="left", fill="x", expand=True)
            self.nav_buttons[name] = btn
            
        # Push logout to bottom
        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(expand=True)
        
        logout_btn = ctk.CTkButton(
            self.sidebar, text="Log Out", 
            fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover(),
            height=45, font=(self.tm.main_font(), 15, "bold"), corner_radius=10,
            command=self.on_logout
        )
        logout_btn.pack(fill="x", padx=15, pady=(5, 30))

        # Main content area
        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.pack(side="right", fill="both", expand=True)

    def show_view(self, view_name, *args, **kwargs):
        internal_name = "More" if view_name == "Settings" else view_name

        # --- Sidebar highlight ---
        if view_name in self.nav_buttons:
            # Update button and indicator colors instantly
            for name, btn in self.nav_buttons.items():
                indicator = self.nav_indicators[name]
                if name == view_name:
                    btn.configure(text_color=self.tm.accent_text(), fg_color=self.tm.accent_color(), hover_color=self.tm.accent_color())
                    indicator.configure(fg_color=self.tm.accent_color())
                else:
                    btn.configure(text_color=self.tm.text_sub(), fg_color="transparent", hover_color=self.tm.bg_sub())
                    indicator.configure(fg_color="transparent")
            
            self._active_nav = view_name

        # Cache logic
        cacheable_views = {"Subjects", "Insights", "History", "Notifications", "More"}
        is_cacheable = internal_name in cacheable_views and not args and not kwargs

        # Hide or destroy current view
        if self.current_view is not None:
            if self._current_view_key and self._current_view_key in self._view_cache:
                self.current_view.pack_forget()
            else:
                self.current_view.destroy()
            self.current_view = None

        # Return cached view if available
        if is_cacheable and internal_name in self._view_cache:
            self.current_view = self._view_cache[internal_name]
            self._current_view_key = internal_name
            if hasattr(self.current_view, "refresh"):
                self.current_view.refresh()
            self.current_view.pack(fill="both", expand=True)
            if internal_name != "Subjects":
                self._do_page_transition()
            return

        # Build new view
        new_view = self._create_view(internal_name, *args, **kwargs)
        
        if is_cacheable:
            self._view_cache[internal_name] = new_view
            self._current_view_key = internal_name
        else:
            self._current_view_key = None

        self.current_view = new_view
        self.current_view.pack(fill="both", expand=True)
        
        # Skip animation for Subjects page per user request
        if internal_name != "Subjects":
            self._do_page_transition()

    def _do_page_transition(self):
        """Left-to-right slide-in transition for the content area."""
        mode = ctk.get_appearance_mode()
        bg = _resolve_color(self.tm.bg_sub(), mode)
        animate_slide_in(self.content_area, ctk.CTkFrame, bg, duration_ms=250, steps=10)

    def _create_view(self, internal_name, *args, **kwargs):
        """Creates and returns a new view widget."""
        if internal_name == "Home":
            from screens.home_view import HomeView
            return HomeView(self.content_area, self.user_info, self.show_view)
        elif internal_name == "Subjects":
            from screens.subjects_view import SubjectsView
            return SubjectsView(self.content_area, self.user_info, self.show_view)
        elif internal_name == "Tasks":
            from screens.tasks_view import TasksView
            return TasksView(self.content_area, self.user_info, self.show_view, *args, **kwargs)
        elif internal_name == "History":
            from screens.history_view import HistoryView
            return HistoryView(self.content_area, self.user_info, self.show_view)
        elif internal_name == "AllCompleted":
            from screens.all_completed_tasks_view import AllCompletedTasksView
            return AllCompletedTasksView(self.content_area, self.user_info, self.show_view)
        elif internal_name == "Insights":
            from screens.insights_view import InsightsView
            return InsightsView(self.content_area, self.user_info, self.show_view)
        elif internal_name == "AllPending":
            from screens.all_pending_tasks_view import AllPendingTasksView
            return AllPendingTasksView(self.content_area, self.user_info, self.show_view)
        elif internal_name == "Notifications":
            from screens.notifications_view import NotificationsView
            return NotificationsView(self.content_area, self.user_info, self.show_view)
        elif internal_name == "More":
            from screens.more_view import MoreView
            return MoreView(self.content_area, self.user_info, self.on_logout, self.reload_callback)
        else:
            return PlaceholderView(self.content_area, internal_name + " View")

    def clear_cache(self):
        """Clears all cached views with proper cleanup."""
        for view_name, view in list(self._view_cache.items()):
            try:
                view.pack_forget()
                view.destroy()
            except Exception as e:
                logger.error(f"Error cleaning up cached view {view_name}: {e}")
        self._view_cache.clear()

    def __del__(self):
        """Ensure cached views are cleaned up on object destruction."""
        try:
            self.clear_cache()
        except Exception:
            pass
