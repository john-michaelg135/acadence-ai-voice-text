import customtkinter as ctk
from utils.theme_manager import ThemeManager
from database.db_manager import DatabaseManager

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
        # Header
        ctk.CTkLabel(self, text="Priority Insights", font=("Arial", 28, "bold"), text_color=self.tm.text_main()).pack(anchor="w", padx=20, pady=(20, 10))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Priority Insight Card
        p_card = ctk.CTkFrame(scroll, fg_color=self.tm.accent_color(), corner_radius=15)
        p_card.pack(fill="x", padx=10, pady=(0, 15))
        
        # Header in card
        header_f = ctk.CTkFrame(p_card, fg_color="transparent")
        header_f.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(header_f, text="Priority Insight", font=("Arial", 16, "bold"), text_color=self.tm.accent_text()).pack(side="left")
        ctk.CTkLabel(header_f, text="❗", font=("Arial", 18), text_color=self.tm.error_color()).pack(side="right")
        
        metrics = self.db.get_dashboard_metrics(self.user_id) if self.user_id else None
        worst_subject = None
        if metrics and metrics['subjects']:
            worst_subject = max(metrics['subjects'], key=lambda x: x['pending_task_count'])
            if worst_subject['pending_task_count'] == 0:
                worst_subject = None
                
        if not worst_subject:
            ctk.CTkLabel(p_card, text="Subject with the most pending tasks is\ndisplayed here.", 
                         font=("Arial", 14), text_color=self.tm.accent_text(), justify="center").pack(pady=(20, 30))
        else:
            ctk.CTkLabel(p_card, text=worst_subject['name'], font=("Arial", 14), text_color=self.tm.accent_text()).pack(pady=(0, 15))
            
            # Content with number and star
            c_frame = ctk.CTkFrame(p_card, fg_color="transparent")
            c_frame.pack(fill="x", padx=20)
            
            num_f = ctk.CTkFrame(c_frame, fg_color="transparent")
            num_f.pack(side="left")
            ctk.CTkLabel(num_f, text=str(worst_subject['pending_task_count']), font=("Arial", 46, "bold"), text_color=self.tm.accent_text()).pack(anchor="w", pady=(0,0))
            ctk.CTkLabel(num_f, text="pending tasks", font=("Arial", 12), text_color=self.tm.accent_text()).pack(anchor="w")
            
            star_btn = ctk.CTkButton(c_frame, text="⭐", font=("Arial", 30), text_color=self.tm.accent_text(), 
                                     fg_color=self.tm.accent_hover(), hover_color=self.tm.accent_hover(),
                                     width=70, height=70, corner_radius=35)
            star_btn.pack(side="right")
            
            ctk.CTkLabel(p_card, text="This subject requires immediate attention and\nmay generate more notifications.", 
                         font=("Arial", 12), text_color=self.tm.accent_text(), justify="left").pack(anchor="w", padx=20, pady=(20, 15))
                         
            ctk.CTkButton(p_card, text="View Tasks", fg_color=self.tm.bg_card(), text_color=self.tm.accent_color(), 
                          hover_color=self.tm.bg_sub(), font=("Arial", 14, "bold"), height=45, corner_radius=22,
                          command=lambda: self.show_view_callback("Tasks", worst_subject['id'], worst_subject['name'])).pack(fill="x", padx=20, pady=(0, 20))
                          
        # High Priority List
        high_tasks = self.db.get_pending_tasks_by_priority(self.user_id, 'High', limit=4) if self.user_id else []
        self._build_task_list(scroll, "High Priority Tasks", high_tasks, "No high priority tasks at the moment.", self.tm.error_color())
        
        # Medium Priority List
        med_tasks = self.db.get_pending_tasks_by_priority(self.user_id, 'Medium', limit=4) if self.user_id else []
        self._build_task_list(scroll, "Medium Priority Tasks", med_tasks, "No medium priority tasks at the moment.", self.tm.warning_color())
        
        # View All
        ctk.CTkButton(scroll, text="View All Tasks", fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), 
                      hover_color=self.tm.accent_hover(), font=("Arial", 14, "bold"), height=45, corner_radius=22,
                      command=lambda: self.show_view_callback("AllPending")).pack(fill="x", padx=10, pady=(15, 30))

    def _build_task_list(self, parent, title, tasks, empty_text, flag_color):
        card = ctk.CTkFrame(parent, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=1, corner_radius=15)
        card.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(card, text=title, font=("Arial", 18, "bold"), text_color=self.tm.text_main()).pack(pady=(15, 5))
        
        if not tasks:
            ctk.CTkLabel(card, text=empty_text, font=("Arial", 13), text_color=self.tm.text_sub()).pack(pady=(5, 20))
            return
            
        for task in tasks:
            row = ctk.CTkFrame(card, fg_color=self.tm.bg_sub(), corner_radius=10)
            row.pack(fill="x", padx=15, pady=5)
            
            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True, padx=15, pady=10)
            
            ctk.CTkLabel(left, text=task['name'], font=("Arial", 14, "bold"), text_color=self.tm.text_main(), anchor="w").pack(fill="x")
            
            sub = ctk.CTkFrame(left, fg_color="transparent")
            sub.pack(fill="x")
            
            ctk.CTkLabel(sub, text="🏁 " + task['priority'], font=("Arial", 11, "bold"), text_color=flag_color).pack(side="left", padx=(0, 10))
            ctk.CTkLabel(sub, text=task['subject_name'], font=("Arial", 11), text_color=self.tm.text_sub()).pack(side="left")
            
            view_btn = ctk.CTkButton(row, text="❯", font=("Arial", 18), text_color=self.tm.text_sub(), fg_color="transparent", hover_color=self.tm.border_main(), width=30,
                                     command=lambda s_id=task['subject_id'], s_name=task['subject_name']: self.show_view_callback("Tasks", s_id, s_name))
            view_btn.pack(side="right", padx=15)
            
        ctk.CTkFrame(card, fg_color="transparent", height=10).pack()
