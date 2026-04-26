import customtkinter as ctk
from utils.theme_manager import ThemeManager
from database.db_manager import DatabaseManager

class HomeView(ctk.CTkFrame):
    def __init__(self, master, user_info):
        self.tm = ThemeManager()
        super().__init__(master, fg_color="transparent")
        self.user_info = user_info
        self.db = DatabaseManager()
        self.user_id = self.user_info['id'] if self.user_info else None
        
        self.major_color = "#99C2E1" # Light Blue
        self.minor_color = "#E6E2B1" # Light Yellow
        
        # Distribution palette
        self.dist_colors = ["#7BABD9", "#BFD5E7", "#B9D1DD", "#BBD0E6", "#C0CA9C", "#E0DFBE", "#E2DFBF", "#DBD8B9"] 

        self.setup_ui()

    def setup_ui(self):
        # Fetch metrics
        if self.user_id:
            metrics = self.db.get_dashboard_metrics(self.user_id)
        else:
            metrics = {"total_subjects": 0, "total_pending_tasks": 0, "high_priority_count": 0, "subjects": []}
            
        main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # 1. Priority Card (Restored)
        priority_card = ctk.CTkFrame(main_scroll, fg_color=self.tm.accent_color(), corner_radius=15)
        priority_card.pack(fill="x", padx=10, pady=(10, 10))
        
        ctk.CTkLabel(priority_card, text="Priority Card", font=("Arial", 16), text_color=self.tm.text_main()).pack(pady=(15, 5))
        
        p_content = ctk.CTkFrame(priority_card, fg_color="transparent")
        p_content.pack()
        ctk.CTkLabel(p_content, text=f"⚠️ {metrics.get('high_priority_count', 0)}", font=("Arial", 40, "bold"), text_color=self.tm.text_main()).pack()

        ctk.CTkLabel(
            priority_card, 
            text="These are the number of pending\ntask with high priority.", 
            font=("Arial", 12), text_color=self.tm.text_main()
        ).pack(pady=(5, 15))

        # 2. Subjects Card (Restored)
        subjects_card = ctk.CTkFrame(main_scroll, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=1, corner_radius=15)
        subjects_card.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(subjects_card, text="Subjects", font=("Arial", 16), text_color=self.tm.text_main()).pack(pady=(15, 5))
        
        s_content = ctk.CTkFrame(subjects_card, fg_color="transparent")
        s_content.pack()
        ctk.CTkLabel(s_content, text=f"🔖 {metrics['total_subjects']}", font=("Arial", 40, "bold"), text_color=self.tm.text_main()).pack()

        ctk.CTkLabel(
            subjects_card, 
            text="Added subjects will appear as\ncontainers in the bottom.", 
            font=("Arial", 12), text_color=self.tm.text_sub()
        ).pack(pady=(5, 15))


        # 3. All Tasks Summary Card
        summary_card = ctk.CTkFrame(main_scroll, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=1, corner_radius=15)
        summary_card.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(summary_card, text="All Tasks", font=("Arial", 16)).pack(pady=(20, 10))
        tasks_count = metrics["total_pending_tasks"]
        ctk.CTkLabel(summary_card, text=f"📋 {tasks_count}", font=("Arial", 50, "bold"), text_color=self.tm.text_main()).pack(pady=5)
        ctk.CTkLabel(summary_card, text=f"Total Pending Tasks", font=("Arial", 13), text_color=self.tm.text_sub()).pack(pady=(5, 30))
        
        # Task Distribution Container
        distrib_frame = ctk.CTkFrame(summary_card, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=1, corner_radius=15)
        distrib_frame.pack(fill="x", padx=15, pady=(0, 20))
        
        ctk.CTkLabel(distrib_frame, text="Task Distribution", font=("Arial", 16)).pack(pady=(15, 5))
        ctk.CTkLabel(distrib_frame, text="Your data distribution appears here.", font=("Arial", 11), text_color=self.tm.text_sub()).pack(pady=(0, 20))
        
        if not metrics["subjects"]:
            ctk.CTkLabel(distrib_frame, text="No subjects added.", text_color=self.tm.text_sub()).pack(pady=(0, 20))
            
        for idx, sub in enumerate(metrics["subjects"]):
            row_frame = ctk.CTkFrame(distrib_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=30, pady=5)
            dot_color = self.dist_colors[idx % len(self.dist_colors)]
            ctk.CTkLabel(row_frame, text="●", text_color=dot_color, font=("Arial", 20)).pack(side="left", padx=(0, 10))
            ctk.CTkLabel(row_frame, text=f"{sub['name']}  :", font=("Arial", 13), text_color=self.tm.text_sub()).pack(side="left")
            ctk.CTkLabel(row_frame, text=f" {sub['task_count']}", font=("Arial", 13), text_color=self.tm.text_main()).pack(side="left")

        # 4. Horizontally Scrollable Subjects (Categorized)
        majors = [s for s in metrics["subjects"] if s.get("category") == "Major"]
        minors = [s for s in metrics["subjects"] if s.get("category") == "Minor"]

        # Row 1: Major
        if majors:
            ctk.CTkLabel(main_scroll, text="Major Subjects", font=("Arial", 12, "bold"), text_color=self.tm.text_main()).pack(anchor="w", padx=15, pady=(10, 0))
            major_scroll = ctk.CTkScrollableFrame(main_scroll, fg_color="transparent", orientation="horizontal", height=150)
            major_scroll.pack(fill="x", padx=5)
            
            for sub in majors:
                c = ctk.CTkFrame(major_scroll, fg_color=self.major_color, corner_radius=15, width=110, height=135)
                c.pack(side="left", padx=10, pady=5)
                c.pack_propagate(False)
                
                ctk.CTkLabel(c, text=sub['name'], font=("Arial", 12, "bold"), text_color="#333333").pack(pady=(15, 5))
                ctk.CTkLabel(c, text="📖", font=("Arial", 32), text_color=self.tm.accent_text()).pack(expand=True)
                ctk.CTkLabel(c, text=f"{sub['task_count']} tasks", font=("Arial", 11), text_color=self.tm.text_sub()).pack(pady=(5, 10))

        # Row 2: Minor
        if minors:
            ctk.CTkLabel(main_scroll, text="Minor Subjects", font=("Arial", 12, "bold"), text_color=self.tm.text_main()).pack(anchor="w", padx=15, pady=(10, 0))
            minor_scroll = ctk.CTkScrollableFrame(main_scroll, fg_color="transparent", orientation="horizontal", height=150)
            minor_scroll.pack(fill="x", padx=5)
            
            for sub in minors:
                c = ctk.CTkFrame(minor_scroll, fg_color=self.minor_color, corner_radius=15, width=110, height=135)
                c.pack(side="left", padx=10, pady=5)
                c.pack_propagate(False)
                
                ctk.CTkLabel(c, text=sub['name'], font=("Arial", 12, "bold"), text_color="#333333").pack(pady=(15, 5))
                ctk.CTkLabel(c, text="📖", font=("Arial", 32), text_color=self.tm.accent_text()).pack(expand=True)
                ctk.CTkLabel(c, text=f"{sub['task_count']} tasks", font=("Arial", 11), text_color=self.tm.text_sub()).pack(pady=(5, 10))

