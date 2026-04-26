import customtkinter as ctk
from utils.theme_manager import ThemeManager
from database.db_manager import DatabaseManager

class AllPendingTasksView(ctk.CTkFrame):
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
        
        back_btn = ctk.CTkButton(header_frame, text="← Back", width=60, fg_color="transparent", text_color=self.tm.text_main(), 
                                 hover_color=self.tm.bg_card(), font=("Arial", 14), command=lambda: self.show_view_callback("Insights"))
        back_btn.pack(side="left")
        
        ctk.CTkLabel(header_frame, text="All Pending Tasks", font=("Arial", 22, "bold"), text_color=self.tm.text_main()).pack(side="left", padx=20)
        
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        tasks = self.db.get_all_pending_tasks(self.user_id) if self.user_id else []
        
        if not tasks:
            ctk.CTkLabel(scroll, text="You have no pending tasks! Great job.", font=("Arial", 14, "italic"), text_color=self.tm.text_sub()).pack(pady=40)
            return
            
        for task in tasks:
            row = ctk.CTkFrame(scroll, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=1, corner_radius=10)
            row.pack(fill="x", padx=10, pady=5)
            
            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True, padx=15, pady=10)
            
            ctk.CTkLabel(left, text=task['name'], font=("Arial", 15, "bold"), text_color=self.tm.text_main(), anchor="w").pack(fill="x")
            
            sub = ctk.CTkFrame(left, fg_color="transparent")
            sub.pack(fill="x")
            
            flag_color = self.tm.error_color() if task['priority'] == 'High' else self.tm.warning_color() if task['priority'] == 'Medium' else self.tm.success_color()
            
            ctk.CTkLabel(sub, text="🏁 " + task['priority'], font=("Arial", 11, "bold"), text_color=flag_color).pack(side="left", padx=(0, 10))
            ctk.CTkLabel(sub, text=task['subject_name'], font=("Arial", 11), text_color=self.tm.text_sub()).pack(side="left", padx=(0, 10))
            if task.get('deadline'):
                ctk.CTkLabel(sub, text=f"📅 {task['deadline']}", font=("Arial", 11), text_color=self.tm.text_sub()).pack(side="left")

            view_btn = ctk.CTkButton(row, text="❯", font=("Arial", 18), text_color=self.tm.text_sub(), fg_color="transparent", hover_color=self.tm.bg_sub(), width=40,
                                     command=lambda s_id=task['subject_id'], s_name=task['subject_name']: self.show_view_callback("Tasks", s_id, s_name))
            view_btn.pack(side="right", padx=10)
