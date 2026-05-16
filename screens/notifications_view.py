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
        
        self.setup_ui()

    def setup_ui(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header_frame, text="Notifications", font=(self.tm.main_font(), 26, "bold"), text_color=self.tm.text_main()).pack(side="left")

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=self.tm.bg_main(), scrollbar_button_hover_color=self.tm.text_sub())
        self.scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.refresh()

    def refresh(self):
        for widget in self.scroll.winfo_children():
            widget.destroy()

        tasks = self.db.get_all_pending_tasks(self.user_id) if self.user_id else []
        
        today_date = datetime.today().date()
        tomorrow_date = today_date + timedelta(days=1)
        
        overdue_tasks = []
        due_today = []
        due_tomorrow = []
        
        for task in tasks:
            deadline_str = task.get('deadline')
            if not deadline_str: continue
            
            try:
                date_part = deadline_str.split(" ")[0]
                task_date = datetime.strptime(date_part, "%Y-%m-%d").date()
                
                if task_date < today_date:
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
            card = ctk.CTkFrame(section_frame, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=1, corner_radius=10)
            card.pack(fill="x", padx=10, pady=5)
            
            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True, padx=15, pady=12)
            
            name = ctk.CTkLabel(left, text=task['name'], font=(self.tm.main_font(), 15, "bold"), text_color=self.tm.text_main(), anchor="w")
            name.pack(fill="x")
            
            sub = ctk.CTkFrame(left, fg_color="transparent")
            sub.pack(fill="x")
            
            subj = ctk.CTkLabel(sub, text=task['subject_name'], font=(self.tm.main_font(), 12), text_color=self.tm.text_sub())
            subj.pack(side="left", padx=(0, 10))
            
            deadline_str = task.get('deadline')
            time_lbl = None
            if deadline_str:
                time_lbl = ctk.CTkLabel(sub, text=f"🕒 {deadline_str}", font=(self.tm.main_font(), 12), text_color=icon_color)
                time_lbl.pack(side="left")
                
            card.configure(cursor="hand2")
            left.configure(cursor="hand2")
            name.configure(cursor="hand2")
            sub.configure(cursor="hand2")
            subj.configure(cursor="hand2")
            if time_lbl: time_lbl.configure(cursor="hand2")

            def on_click(event, t=task):
                from screens.tasks_view import TaskDetailsPopup
                TaskDetailsPopup(self.winfo_toplevel(), t, self.db, self.refresh, t['subject_name'])
                
            card.bind("<Button-1>", on_click)
            left.bind("<Button-1>", on_click)
            name.bind("<Button-1>", on_click)
            sub.bind("<Button-1>", on_click)
            subj.bind("<Button-1>", on_click)
            if time_lbl: time_lbl.bind("<Button-1>", on_click)
