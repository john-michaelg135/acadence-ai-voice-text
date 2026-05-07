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
        
        self.sort_order = "newer"  # Default: newest accounts first
        self.search_query = ""  # Current search filter
        self._cached_users = []  # Cache DB results to avoid round-trips on each keystroke
        self._search_after_id = None  # Debounce timer ID
        self.setup_ui()
        self._render_id = 0  # Incremented on each load to cancel stale renders
        self.load_users()

    def setup_ui(self):
        # Header area
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(header_frame, text="Admin Portal", font=(self.tm.main_font(), 28, "bold"), text_color=self.tm.accent_color()).pack(side="left")
        
        # Right side actions (Search, Theme Toggle, Logout)
        actions_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        actions_frame.pack(side="right")
        
        # Search bar for filtering usernames
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search_changed)
        
        self.search_entry = ctk.CTkEntry(
            actions_frame, placeholder_text="Search username...",
            textvariable=self.search_var,
            width=200, height=32, corner_radius=16,
            fg_color=self.tm.bg_sub(),
            border_width=2, border_color=self.tm.accent_color(),
            text_color=self.tm.text_main(),
            placeholder_text_color=self.tm.text_sub(),
            font=(self.tm.main_font(), 12)
        )
        ctk.CTkLabel(actions_frame, text="Search Username", font=(self.tm.main_font(), 13, "bold"), text_color=self.tm.text_main()).pack(side="left", padx=(0, 5))
        self.search_entry.pack(side="left", padx=(0, 15))
        
        theme_menu = ctk.CTkOptionMenu(
            actions_frame, values=["Light", "Dark", "System"],
            command=ctk.set_appearance_mode, width=100, height=30,
            fg_color=self.tm.bg_sub(), button_color=self.tm.accent_color(), button_hover_color=self.tm.accent_hover(),
            text_color=self.tm.text_main(),
            font=(self.tm.main_font(), 12), dropdown_font=(self.tm.main_font(), 12)
        )
        theme_menu.pack(side="left", padx=(0, 15))
        current_mode = ctk.get_appearance_mode()
        theme_menu.set(current_mode)
        
        ctk.CTkButton(actions_frame, text="Log Out", width=90, fg_color="transparent", border_width=1, text_color=self.tm.text_main(),
                      font=(self.tm.main_font(), 12, "bold"),
                      command=self.on_logout).pack(side="left")

        # Subheader row: "System User Metrics" label + Sort toggle
        subheader_frame = ctk.CTkFrame(self, fg_color="transparent")
        subheader_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(subheader_frame, text="System User Metrics", font=(self.tm.main_font(), 16), text_color=self.tm.text_sub()).pack(side="left")
        
        # Sort toggle button (styled like the deadline sort toggle)
        self.sort_btn = ctk.CTkButton(
            subheader_frame, text="Sort: Newer", width=130, height=32, corner_radius=16,
            fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(),
            hover_color=self.tm.accent_hover(),
            font=(self.tm.main_font(), 13, "bold"),
            command=self.toggle_sort
        )
        self.sort_btn.pack(side="left", padx=15)

        # Scrollable list for standard users
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=self.tm.bg_main(), scrollbar_button_hover_color=self.tm.text_sub())
        self.scroll_frame.pack(fill="both", expand=True, padx=15, pady=10)

    def toggle_sort(self):
        """Toggle between Newer (DESC) and Older (ASC) account ordering."""
        if self.sort_order == "newer":
            self.sort_order = "older"
            self.sort_btn.configure(
                text="Sort: Older",
                fg_color="transparent",
                text_color=self.tm.accent_color(),
                border_width=2,
                border_color=self.tm.accent_color()
            )
        else:
            self.sort_order = "newer"
            self.sort_btn.configure(
                text="Sort: Newer",
                fg_color=self.tm.accent_color(),
                text_color=self.tm.accent_text(),
                border_width=0
            )
        self.load_users()

    def _on_search_changed(self, *args):
        """Debounced search: waits 300ms after last keystroke before filtering."""
        if self._search_after_id is not None:
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(300, self._apply_search)
    
    def _apply_search(self):
        """Actually apply the search filter after debounce."""
        self._search_after_id = None
        self.search_query = self.search_var.get().strip().lower()
        self._render_from_cache()

    def load_users(self):
        """Fetches fresh data from DB, caches it, then renders."""
        self._cached_users = self.db.get_all_users_for_admin()
        self._render_from_cache()

    def _render_from_cache(self):
        """Renders user list from cached data with current search/sort applied."""
        self._render_id += 1
        current_render = self._render_id

        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        users = list(self._cached_users)
        
        # Apply search filter
        if self.search_query:
            users = [u for u in users if self.search_query in u['username'].lower()]
        
        # Apply sort order
        if self.sort_order == "newer":
            users.sort(key=lambda u: u.get('created_at', ''), reverse=True)
        else:
            users.sort(key=lambda u: u.get('created_at', ''), reverse=False)
        
        if not users:
            msg = f"No users found matching \"{self.search_var.get().strip()}\"." if self.search_query else "No standard users registered in the system yet."
            ctk.CTkLabel(self.scroll_frame, text=msg, text_color=self.tm.text_sub(), font=(self.tm.main_font(), 14)).pack(pady=30)
            return
            
        self._render_user_chunk(users, 0, current_render)

    def _render_user_chunk(self, users, index, render_id, chunk_size=10):
        """Renders user cards in chunks to prevent UI freezing."""
        if render_id != self._render_id:
            return
        if not self.winfo_exists():
            return

        end = min(index + chunk_size, len(users))
        for i in range(index, end):
            self.create_user_card(users[i])

        if end < len(users):
            self.after(10, lambda: self._render_user_chunk(users, end, render_id, chunk_size))

    def create_user_card(self, user):
        card = ctk.CTkFrame(self.scroll_frame, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=2, corner_radius=15)
        card.pack(fill="x", pady=8, padx=5)

        # Top row: Username and Indicators
        top_frame = ctk.CTkFrame(card, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=(15, 5))
        
        ctk.CTkLabel(top_frame, text=f"@{user['username']}", font=(self.tm.main_font(), 18, "bold"), text_color=self.tm.text_main()).pack(side="left")
        
        # Inactivity Pill
        from datetime import datetime
        last_login_str = user.get('last_login')
        needs_action = False
        is_abandoned = False
        
        if not user.get('is_disabled'):
            if not last_login_str:
                created_dt_str = user.get('created_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                try:
                    last_dt = datetime.strptime(created_dt_str, "%Y-%m-%d %H:%M:%S")
                    days_inactive = (datetime.now() - last_dt).days
                except:
                    days_inactive = 0
            else:
                try:
                    last_dt = datetime.strptime(last_login_str, "%Y-%m-%d %H:%M:%S")
                    days_inactive = (datetime.now() - last_dt).days
                except:
                    days_inactive = 0
                    
            if days_inactive > 90:
                is_abandoned = True
            elif days_inactive > 21:
                needs_action = True
                    
            if is_abandoned:
                ctk.CTkLabel(top_frame, text="No Longer Active", font=(self.tm.main_font(), 12, "bold"), text_color=self.tm.text_inverse()[0], 
                             fg_color=self.tm.error_color(), corner_radius=10, width=130, height=24).pack(side="left", padx=15)
            elif needs_action:
                ctk.CTkLabel(top_frame, text="Action Needed", font=(self.tm.main_font(), 12, "bold"), text_color=self.tm.text_inverse()[0], 
                             fg_color=self.tm.warning_color(), corner_radius=10, width=110, height=24).pack(side="left", padx=15)

        # Disable/Enable/Delete Account Buttons
        action_btns_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        action_btns_frame.pack(side="right")
        
        from tkinter import messagebox
        if user.get('is_disabled'):
            def enable_cmd():
                if messagebox.askyesno("Enable Account", f"Are you sure you want to re-enable @{user['username']}?\nThey will be able to log in again.", parent=self):
                    self.db.enable_user(user['id'])
                    for widget in self.scroll_frame.winfo_children():
                        widget.destroy()
                    self.load_users()
                    
            ctk.CTkButton(action_btns_frame, text="Enable Account", width=120, height=28, fg_color="transparent", text_color=self.tm.success_color(),
                          border_width=1, border_color=self.tm.success_color(), font=(self.tm.main_font(), 12),
                          command=enable_cmd).pack(pady=(0, 2))
        else:
            def disable_cmd():
                if messagebox.askyesno("Disable Account", f"Are you sure you want to disable @{user['username']}?\nThis action will prevent them from logging in.", parent=self):
                    self.db.disable_user(user['id'])
                    for widget in self.scroll_frame.winfo_children():
                        widget.destroy()
                    self.load_users()

            ctk.CTkButton(action_btns_frame, text="Disable Account", width=120, height=28, fg_color="transparent", text_color=self.tm.warning_color(),
                          border_width=1, border_color=self.tm.warning_color(), hover_color=self.tm.bg_sub(),
                          font=(self.tm.main_font(), 12),
                          command=disable_cmd).pack(pady=(0, 2))
                          
        if is_abandoned:
            def delete_cmd():
                if messagebox.askyesno("Delete Account", f"Are you absolutely sure you want to PERMANENTLY DELETE @{user['username']}?\nThis action cannot be undone and will erase all their subjects and tasks.", parent=self):
                    self.db.delete_user(user['id'])
                    for widget in self.scroll_frame.winfo_children():
                        widget.destroy()
                    self.load_users()
            
            ctk.CTkButton(action_btns_frame, text="Delete Account", width=120, height=28, fg_color=self.tm.error_color(), text_color=self.tm.text_inverse()[0],
                          hover_color=self.tm.error_hover(), font=(self.tm.main_font(), 12, "bold"), command=delete_cmd).pack(pady=(2, 0))
        
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
        
        ctk.CTkLabel(info_frame, text=f"Joined: {created_str}", font=(self.tm.main_font(), 12), text_color=self.tm.text_sub()).pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"Last Active: {last_login_str}", font=(self.tm.main_font(), 12), text_color=self.tm.text_sub()).pack(anchor="w", pady=(2,0))
        
        recent_mins = user.get('recent_login_duration') or 0
        ctk.CTkLabel(info_frame, text=f"Most Recent Session: {recent_mins} min(s)", font=(self.tm.main_font(), 12), text_color=self.tm.text_sub()).pack(anchor="w", pady=(2,0))
        
        duration_mins = user.get('login_duration') or 0
        ctk.CTkLabel(info_frame, text=f"Total Logged In Time: {duration_mins} min(s)", font=(self.tm.main_font(), 12), text_color=self.tm.text_sub()).pack(anchor="w", pady=(2,0))

        # Bottom metrics aggregates (Subjects / Tasks split block)
        metrics_frame = ctk.CTkFrame(card, fg_color=self.tm.bg_completed(), corner_radius=10)
        metrics_frame.pack(fill="x", padx=15, pady=(10, 15))
        
        ctk.CTkLabel(metrics_frame, text=f"📚 Subjects: {user['total_subjects']}", font=(self.tm.main_font(), 13, "bold"), text_color=self.tm.text_main()).pack(side="left", expand=True, pady=10)
        ctk.CTkLabel(metrics_frame, text=f"📋 Tasks: {user['total_tasks']}", font=(self.tm.main_font(), 13, "bold"), text_color=self.tm.text_main()).pack(side="right", expand=True, pady=10)
