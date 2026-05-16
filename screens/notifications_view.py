import customtkinter as ctk
from utils.theme_manager import ThemeManager
from database.db_manager import DatabaseManager
from datetime import datetime, timedelta

class NotificationsView(ctk.CTkFrame):
    def __init__(self, master, user_info, show_view_callback):
        self.tm = ThemeManager()
        super().__init__(master, fg_color="transparent")
        self.user_info = user_info
        self.db = DatabaseManager()
        self.show_view_callback = show_view_callback
        self.user_id = self.user_info['id'] if self.user_info else None
        
        # We need this for the popups
        from tkinter import messagebox
        self.messagebox = messagebox
        
        self._auto_refresh_id = None
        self.setup_ui()
        self._start_auto_refresh()

    def _start_auto_refresh(self):
        """Auto-refresh every 30 seconds to catch tasks that just became overdue."""
        if not self.winfo_exists():
            return
        self.refresh()
        self._auto_refresh_id = self.after(30000, self._start_auto_refresh)

    def destroy(self):
        """Cancel the auto-refresh timer on destroy."""
        if self._auto_refresh_id:
            self.after_cancel(self._auto_refresh_id)
            self._auto_refresh_id = None
        super().destroy()

    def setup_ui(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header_frame, text="Notifications", font=(self.tm.main_font(), 26, "bold"), text_color=self.tm.text_main()).pack(side="left")

        # System notification status banner
        from utils.session_manager import get_notification_settings
        settings = get_notification_settings(user_id=self.user_id)
        is_enabled = settings.get("enabled", True)
        
        banner_frame = ctk.CTkFrame(self, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=1, corner_radius=10, height=40)
        banner_frame.pack(fill="x", padx=20, pady=(0, 10))
        banner_frame.pack_propagate(False)
        
        if is_enabled:
            high_int = settings.get("high_interval_minutes", 5)
            med_int = settings.get("medium_interval_minutes", 15)
            low_int = settings.get("low_interval_minutes", 30)
            status_text = f"🔔 System desktop notifications are ON"
            status_color = self.tm.accent_color()
        else:
            status_text = "🔕 System desktop notifications are OFF"
            status_color = self.tm.text_sub()
        
        ctk.CTkLabel(banner_frame, text=status_text, font=(self.tm.main_font(), 12), text_color=status_color).pack(side="left", padx=15)
        
        ctk.CTkButton(
            banner_frame, text="Configure", font=(self.tm.main_font(), 11, "bold"), width=80, height=26, corner_radius=8,
            fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover(),
            command=lambda: self.show_view_callback("Settings")
        ).pack(side="right", padx=15)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=self.tm.bg_main(), scrollbar_button_hover_color=self.tm.text_sub())
        self.scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.refresh()

    def refresh(self):
        for widget in self.scroll.winfo_children():
            widget.destroy()

        tasks = self.db.get_all_pending_tasks(self.user_id) if self.user_id else []
        
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        today_date = datetime.today().date()
        tomorrow_date = today_date + timedelta(days=1)
        
        overdue_tasks = []
        due_today = []
        due_tomorrow = []
        
        for task in tasks:
            deadline_str = task.get('deadline')
            if not deadline_str: continue
            
            try:
                # If deadline is date-only, assume it's due at end of day (23:59) for overdue calculation
                compare_deadline = deadline_str if len(deadline_str) > 10 else deadline_str + " 23:59"
                is_overdue = compare_deadline < now_str
                
                date_part = deadline_str.split(" ")[0]
                task_date = datetime.strptime(date_part, "%Y-%m-%d").date()
                
                if is_overdue:
                    overdue_tasks.append(task)
                elif task_date == today_date:
                    due_today.append(task)
                elif task_date == tomorrow_date:
                    due_tomorrow.append(task)
            except Exception:
                pass
                
        has_notifications = False
        
        if overdue_tasks:
            self._render_section("🚨 Overdue Tasks", overdue_tasks, self.tm.error_color())
            has_notifications = True
            
        if due_today:
            self._render_section("⚠️ Due Today", due_today, self.tm.warning_color())
            has_notifications = True
            
        if due_tomorrow:
            self._render_section("📅 Due Tomorrow", due_tomorrow, self.tm.accent_color())
            has_notifications = True
            
        if not has_notifications:
            empty_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
            empty_frame.pack(fill="both", expand=True, pady=100)
            ctk.CTkLabel(empty_frame, text="🔔", font=(self.tm.main_font(), 48)).pack(pady=(0, 10))
            ctk.CTkLabel(empty_frame, text="You're all caught up!", font=(self.tm.main_font(), 18, "bold"), text_color=self.tm.text_main()).pack()
            ctk.CTkLabel(empty_frame, text="No immediate deadlines approaching.", font=(self.tm.main_font(), 14), text_color=self.tm.text_sub()).pack()

    def _render_section(self, title, tasks, icon_color):
        section_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        section_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(section_frame, text=title, font=(self.tm.main_font(), 18, "bold"), text_color=icon_color).pack(anchor="w", padx=10, pady=(0, 10))
        
        for task in tasks:
            card = ctk.CTkFrame(section_frame, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=2, corner_radius=10, height=65)
            card.pack(fill="x", padx=10, pady=5)
            card.pack_propagate(False)
            
            # Action Button (Mark as Done)
            act_frame = ctk.CTkFrame(card, fg_color="transparent")
            act_frame.pack(side="right", padx=15)
            
            def toggle_status(t=task):
                if self.messagebox.askyesno("Confirm", "Mark this task as completed?"):
                    self.db.update_task_status(t['id'], 'completed')
                    self.refresh()
            
            ctk.CTkButton(act_frame, text="Mark as Done", font=(self.tm.main_font(), 11, "bold"), width=100, height=24, corner_radius=8,
                          fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover(),
                          command=toggle_status).pack(side="right")

            # Priority Indicator
            p_color = self.tm.error_color() if task['priority'] == 'High' else (self.tm.warning_color() if task['priority'] == 'Medium' else self.tm.success_color())
            ctk.CTkLabel(card, text=task['priority'], font=(self.tm.main_font(), 13, "bold"), text_color=p_color, width=70, anchor="w").pack(side="right", padx=(0, 5))

            # Left content
            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True, padx=15, pady=10)
            
            # Truncate name
            display_name = task['name']
            if len(display_name) > 35: display_name = display_name[:32] + "..."
            
            name_lbl = ctk.CTkLabel(left, text=display_name, font=(self.tm.main_font(), 15, "bold"), text_color=self.tm.text_main(), anchor="w")
            name_lbl.pack(fill="x")
            
            sub = ctk.CTkFrame(left, fg_color="transparent")
            sub.pack(fill="x")
            
            # Truncate subject
            display_sub = task['subject_name']
            if len(display_sub) > 20: display_sub = display_sub[:17] + "..."
            
            subj_lbl = ctk.CTkLabel(sub, text=display_sub, font=(self.tm.main_font(), 11), text_color=self.tm.text_sub(), width=200, anchor="w")
            subj_lbl.pack(side="left")
            
            deadline_str = task.get('deadline')
            time_lbl = None
            if deadline_str:
                time_lbl = ctk.CTkLabel(sub, text=f"🕒 {deadline_str}", font=(self.tm.main_font(), 11), text_color=icon_color, width=150, anchor="w")
                time_lbl.pack(side="left", padx=20)
                
            # Clickability
            card.configure(cursor="hand2")
            left.configure(cursor="hand2")
            name_lbl.configure(cursor="hand2")
            sub.configure(cursor="hand2")
            subj_lbl.configure(cursor="hand2")
            if time_lbl: time_lbl.configure(cursor="hand2")

            def on_click(event, t=task):
                from screens.tasks_view import TaskDetailsPopup
                TaskDetailsPopup(self.winfo_toplevel(), t, self.db, self.refresh, t['subject_name'])
                
            card.bind("<Button-1>", on_click)
            left.bind("<Button-1>", on_click)
            name_lbl.bind("<Button-1>", on_click)
            sub.bind("<Button-1>", on_click)
            subj_lbl.bind("<Button-1>", on_click)
            if time_lbl: time_lbl.bind("<Button-1>", on_click)
