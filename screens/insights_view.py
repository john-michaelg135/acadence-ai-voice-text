import customtkinter as ctk
from utils.theme_manager import ThemeManager
from database.db_manager import DatabaseManager
from datetime import datetime

class InsightsView(ctk.CTkFrame):
    def __init__(self, master, user_info, show_view_callback):
        self.tm = ThemeManager()
        super().__init__(master, fg_color="transparent")
        self.user_info = user_info
        self.db = DatabaseManager()
        self.show_view_callback = show_view_callback
        self.user_id = self.user_info['id'] if self.user_info else None
        
        self.setup_ui()

    def setup_ui(self):
        ctk.CTkLabel(self, text="Priority Insights", font=(self.tm.main_font(), 28, "bold"), text_color=self.tm.text_main()).pack(anchor="w", padx=30, pady=(20, 10))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=self.tm.bg_main(), scrollbar_button_hover_color=self.tm.text_sub())
        scroll.pack(fill="both", expand=True, padx=20, pady=5)
        
        # Top Row
        top_row = ctk.CTkFrame(scroll, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 15))
        
        # Priority Insight Card (Left)
        p_card = ctk.CTkFrame(top_row, fg_color=self.tm.accent_color(), corner_radius=15)
        p_card.pack(side="left", fill="both", expand=True, padx=10)
        
        # Header in card
        header_f = ctk.CTkFrame(p_card, fg_color="transparent")
        header_f.pack(fill="x", padx=30, pady=(20, 5))
        ctk.CTkLabel(header_f, text="Priority Insight", font=(self.tm.main_font(), 18, "bold"), text_color=self.tm.accent_text()).pack(side="left")
        ctk.CTkLabel(header_f, text="❗", font=(self.tm.main_font(), 22), text_color=self.tm.error_color()).pack(side="right")
        
        metrics = self.db.get_dashboard_metrics(self.user_id) if self.user_id else None
        worst_subject = None
        if metrics and metrics['subjects']:
            worst_subject = max(metrics['subjects'], key=lambda x: x['pending_task_count'])
            if worst_subject['pending_task_count'] == 0: worst_subject = None
                
        if not worst_subject:
            ctk.CTkLabel(p_card, text="Subject with the most pending tasks is displayed here.", 
                         font=(self.tm.main_font(), 15), text_color=self.tm.accent_text(), justify="center").pack(pady=40)
        else:
            ctk.CTkLabel(p_card, text=worst_subject['name'], font=(self.tm.main_font(), 16), text_color=self.tm.accent_text()).pack(pady=(0, 15))
            c_frame = ctk.CTkFrame(p_card, fg_color="transparent")
            c_frame.pack(fill="x", padx=40)
            num_f = ctk.CTkFrame(c_frame, fg_color="transparent")
            num_f.pack(side="left")
            ctk.CTkLabel(num_f, text=str(worst_subject['pending_task_count']), font=(self.tm.main_font(), 50, "bold"), text_color=self.tm.accent_text()).pack(anchor="w")
            ctk.CTkLabel(num_f, text="pending tasks", font=(self.tm.main_font(), 14), text_color=self.tm.accent_text()).pack(anchor="w")
            
            star_btn = ctk.CTkButton(c_frame, text="⭐", font=(self.tm.main_font(), 36), text_color=self.tm.accent_text(), 
                                     fg_color=self.tm.accent_hover(), hover_color=self.tm.accent_hover(),
                                     width=80, height=80, corner_radius=40)
            star_btn.pack(side="right")
            
            ctk.CTkLabel(p_card, text="This subject requires immediate attention and may generate more notifications.", 
                         font=(self.tm.main_font(), 13), text_color=self.tm.accent_text(), justify="left").pack(anchor="w", padx=30, pady=(20, 20))
                         
            ctk.CTkButton(p_card, text="View Tasks", fg_color=self.tm.bg_card(), text_color=self.tm.accent_color(), 
                          hover_color=self.tm.bg_sub(), font=(self.tm.main_font(), 15, "bold"), height=45, corner_radius=22,
                          command=lambda: self.show_view_callback("Tasks", subject_id=worst_subject['id'], subject_name=worst_subject['name'], source_view="Insights")).pack(fill="x", padx=30, pady=(0, 25))

        # Bottom Row
        bottom_row = ctk.CTkFrame(scroll, fg_color="transparent")
        bottom_row.pack(fill="x", pady=15)
                          
        # High Priority List (Left in bottom row)
        high_f = ctk.CTkFrame(bottom_row, fg_color="transparent")
        high_f.pack(side="left", fill="both", expand=True, padx=10)
        high_tasks = self.db.get_pending_tasks_by_priority(self.user_id, 'High', limit=5) if self.user_id else []
        self._build_task_list(high_f, "High Priority Tasks", high_tasks, "No high priority tasks.", self.tm.error_color())
        
        # Medium Priority List (Right in bottom row)
        med_f = ctk.CTkFrame(bottom_row, fg_color="transparent")
        med_f.pack(side="right", fill="both", expand=True, padx=10)
        med_tasks = self.db.get_pending_tasks_by_priority(self.user_id, 'Medium', limit=5) if self.user_id else []
        self._build_task_list(med_f, "Medium Priority Tasks", med_tasks, "No medium priority tasks.", self.tm.warning_color())
        
        # View All
        ctk.CTkButton(scroll, text="View All Tasks", fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), 
                      hover_color=self.tm.accent_hover(), font=(self.tm.main_font(), 15, "bold"), height=50, corner_radius=25,
                      command=lambda: self.show_view_callback("AllPending")).pack(fill="x", padx=20, pady=(15, 30))

    def _build_task_list(self, parent, title, tasks, empty_text, flag_color):
        card = ctk.CTkFrame(parent, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=2, corner_radius=15)
        card.pack(fill="both", expand=True)
        
        ctk.CTkLabel(card, text=title, font=(self.tm.main_font(), 18, "bold"), text_color=self.tm.text_main()).pack(pady=(20, 10))
        
        if not tasks:
            ctk.CTkLabel(card, text=empty_text, font=(self.tm.main_font(), 14), text_color=self.tm.text_sub()).pack(pady=(20, 40))
            return

        today = datetime.today().strftime('%Y-%m-%d')  # Computed once for all cards
        for task in tasks:
            row = ctk.CTkFrame(card, fg_color=self.tm.bg_sub(), corner_radius=10, cursor="hand2")
            row.pack(fill="x", padx=20, pady=5)
            
            nav_cmd = lambda e, s_id=task['subject_id'], s_name=task['subject_name']: self.show_view_callback("Tasks", subject_id=s_id, subject_name=s_name, source_view="Insights")
            row.bind("<Button-1>", nav_cmd)
            
            left = ctk.CTkFrame(row, fg_color="transparent", cursor="hand2")
            left.pack(side="left", fill="x", expand=True, padx=15, pady=12)
            left.bind("<Button-1>", nav_cmd)
            
            # Truncate task name
            display_name = task['name']
            if len(display_name) > 30: display_name = display_name[:27] + "..."
            
            n_lbl = ctk.CTkLabel(left, text=display_name, font=(self.tm.main_font(), 14, "bold"), text_color=self.tm.text_main(), anchor="w", cursor="hand2")
            n_lbl.pack(fill="x")
            n_lbl.bind("<Button-1>", nav_cmd)
            
            sub = ctk.CTkFrame(left, fg_color="transparent", cursor="hand2")
            sub.pack(fill="x")
            sub.bind("<Button-1>", nav_cmd)
            
            # Use fixed widths for alignment
            p_lbl = ctk.CTkLabel(sub, text=task['priority'], font=(self.tm.main_font(), 12, "bold"), text_color=flag_color, cursor="hand2", width=60, anchor="w")
            p_lbl.pack(side="left")
            p_lbl.bind("<Button-1>", nav_cmd)
            
            # Truncate subject name - More aggressive to fit layout
            display_sub = task['subject_name']
            if len(display_sub) > 18: display_sub = display_sub[:15] + "..."
            
            s_lbl = ctk.CTkLabel(sub, text=display_sub, font=(self.tm.main_font(), 12), text_color=self.tm.text_sub(), cursor="hand2", width=120, anchor="w")
            s_lbl.pack(side="left", padx=10)
            s_lbl.bind("<Button-1>", nav_cmd)
            
            deadline_str = task.get('deadline')
            if deadline_str:
                d_lbl = ctk.CTkLabel(sub, text=f"📅 {deadline_str}", font=(self.tm.main_font(), 12), text_color=self.tm.accent_color(), cursor="hand2", width=120, anchor="w")
                d_lbl.pack(side="left")
                d_lbl.bind("<Button-1>", nav_cmd)
                
                if deadline_str < today and task.get('status', 'pending') == 'pending':
                    overdue_lbl = ctk.CTkLabel(sub, text="Overdue", font=(self.tm.main_font(), 10, "bold"), text_color="#FFFFFF", fg_color=self.tm.error_color(), corner_radius=6, width=60, height=20)
                    overdue_lbl.pack(side="left", padx=(10, 0))
                    overdue_lbl.bind("<Button-1>", nav_cmd)
            
            view_btn = ctk.CTkButton(row, text="❯", font=(self.tm.main_font(), 18, "bold"), text_color=self.tm.text_sub(), fg_color="transparent", hover_color=self.tm.border_main(), width=30,
                                     command=lambda s_id=task['subject_id'], s_name=task['subject_name']: self.show_view_callback("Tasks", subject_id=s_id, subject_name=s_name, source_view="Insights"))
            view_btn.pack(side="right", padx=15)
            
        ctk.CTkFrame(card, fg_color="transparent", height=15).pack()

    def refresh(self):
        """Called by DashboardScreen when the cached view is shown to refresh data."""
        for widget in self.winfo_children():
            widget.destroy()
        self.setup_ui()
