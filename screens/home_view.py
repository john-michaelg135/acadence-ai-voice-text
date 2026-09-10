import customtkinter as ctk
from utils.theme_manager import ThemeManager
from database.db_manager import DatabaseManager

class HomeView(ctk.CTkFrame):
    def __init__(self, master, user_info, show_view_callback):
        self.tm = ThemeManager()
        super().__init__(master, fg_color="transparent")
        self.user_info = user_info
        self.show_view_callback = show_view_callback
        self.db = DatabaseManager()
        self.user_id = self.user_info['id'] if self.user_info else None
        
        self.major_color = "#99C2E1" # Light Blue
        self.minor_color = "#E6E2B1" # Light Yellow
        
        # Distribution palette
        self.dist_colors = ["#7BABD9", "#BFD5E7", "#B9D1DD", "#BBD0E6", "#C0CA9C", "#E0DFBE", "#E2DFBF", "#DBD8B9"] 

        self.setup_ui()

    def setup_ui(self):
        if self.user_id:
            metrics = self.db.get_dashboard_metrics(self.user_id)
        else:
            metrics = {"total_subjects": 0, "total_pending_tasks": 0, "high_priority_count": 0, "subjects": []}
            
        ctk.CTkLabel(self, text="Dashboard", font=(self.tm.main_font(), 28, "bold"), text_color=self.tm.text_main()).pack(anchor="w", padx=30, pady=(20, 10))

        main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=self.tm.bg_main(), scrollbar_button_hover_color=self.tm.text_sub())
        main_scroll.pack(fill="both", expand=True, padx=20, pady=5)
        
        # --- Top Row: 3 Cards ---
        top_row = ctk.CTkFrame(main_scroll, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 20))
        
        # 1. Priority Card
        priority_card = ctk.CTkFrame(top_row, fg_color=self.tm.accent_color(), corner_radius=15, border_width=2, border_color=self.tm.border_main(), height=180)
        priority_card.pack(side="left", fill="x", expand=True, padx=10)
        priority_card.pack_propagate(False)
        ctk.CTkLabel(priority_card, text="Priority Tasks", font=(self.tm.main_font(), 18, "bold"), text_color=self.tm.accent_text()).pack(pady=(25, 5))
        ctk.CTkLabel(priority_card, text=f"⚠️ {metrics.get('high_priority_count', 0)}", font=(self.tm.main_font(), 46, "bold"), text_color=self.tm.accent_text()).pack(expand=True)
        ctk.CTkLabel(priority_card, text="Pending High Priority", font=(self.tm.main_font(), 14), text_color=self.tm.accent_text()).pack(pady=(5, 20))

        # 2. Subjects Card
        subjects_card = ctk.CTkFrame(top_row, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=2, corner_radius=15, height=180)
        subjects_card.pack(side="left", fill="x", expand=True, padx=10)
        subjects_card.pack_propagate(False)
        ctk.CTkLabel(subjects_card, text="Total Subjects", font=(self.tm.main_font(), 18, "bold"), text_color=self.tm.text_main()).pack(pady=(25, 5))
        ctk.CTkLabel(subjects_card, text=f"🔖 {metrics['total_subjects']}", font=(self.tm.main_font(), 46, "bold"), text_color=self.tm.text_main()).pack(expand=True)
        ctk.CTkLabel(subjects_card, text="Active Subject Folders", font=(self.tm.main_font(), 14), text_color=self.tm.text_sub()).pack(pady=(5, 20))

        # 3. All Tasks Summary Card
        summary_card = ctk.CTkFrame(top_row, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=2, corner_radius=15, height=180)
        summary_card.pack(side="left", fill="x", expand=True, padx=10)
        summary_card.pack_propagate(False)
        ctk.CTkLabel(summary_card, text="All Tasks", font=(self.tm.main_font(), 18, "bold"), text_color=self.tm.text_main()).pack(pady=(25, 5))
        ctk.CTkLabel(summary_card, text=f"📋 {metrics['total_pending_tasks']}", font=(self.tm.main_font(), 46, "bold"), text_color=self.tm.text_main()).pack(expand=True)
        ctk.CTkLabel(summary_card, text="Total Pending Tasks", font=(self.tm.main_font(), 14), text_color=self.tm.text_sub()).pack(pady=(5, 20))
        
        # Bind cards to navigation
        def bind_card(card_widget, view_name):
            card_widget.bind("<Button-1>", lambda e: self.show_view_callback(view_name))
            card_widget.configure(cursor="hand2")
            for child in card_widget.winfo_children():
                child.bind("<Button-1>", lambda e: self.show_view_callback(view_name))
                child.configure(cursor="hand2")
                
        bind_card(priority_card, "Insights")
        bind_card(subjects_card, "Subjects")
        bind_card(summary_card, "AllPending")

        # --- Bottom Area: Distribution and Subjects ---
        bottom_row = ctk.CTkFrame(main_scroll, fg_color="transparent")
        bottom_row.pack(fill="both", expand=True, pady=10)

        # Task Distribution Container (Left Side)
        distrib_frame = ctk.CTkFrame(bottom_row, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=2, corner_radius=15, width=400)
        distrib_frame.pack(side="left", fill="y", padx=10)
        distrib_frame.pack_propagate(False)
        
        ctk.CTkLabel(distrib_frame, text="Task Distribution", font=(self.tm.main_font(), 18, "bold"), text_color=self.tm.text_main()).pack(pady=(20, 15))
        if not metrics["subjects"]:
            ctk.CTkLabel(distrib_frame, text="No subjects added.", font=(self.tm.main_font(), 14), text_color=self.tm.text_sub()).pack(pady=40)
            
        distrib_scroll = ctk.CTkScrollableFrame(distrib_frame, fg_color="transparent", scrollbar_button_color=self.tm.border_main(), scrollbar_button_hover_color=self.tm.text_sub())
        distrib_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 20))
            
        distrib_subjects = [s for s in metrics["subjects"] if s.get("pending_task_count", 0) > 0]
        
        if metrics["subjects"] and not distrib_subjects:
            ctk.CTkLabel(distrib_scroll, text="No active tasks in any subject.", font=(self.tm.main_font(), 14, "italic"), text_color=self.tm.text_sub()).pack(pady=40)

        for idx, sub in enumerate(distrib_subjects):
            row_frame = ctk.CTkFrame(distrib_scroll, fg_color="transparent")
            row_frame.pack(fill="x", padx=10, pady=8)
            
            category = sub.get("category", "Major")
            dot_color = self.major_color if category == "Major" else self.minor_color
            
            ctk.CTkLabel(row_frame, text="●", text_color=dot_color, font=(self.tm.main_font(), 32)).pack(side="left", padx=(0, 15))
            
            # Pack count on the right first to anchor it
            ctk.CTkLabel(row_frame, text=f" {sub['pending_task_count']}", font=(self.tm.main_font(), 15, "bold"), text_color=self.tm.text_main()).pack(side="right")
            
            # Allow subject name to wrap multiple lines instead of cutting off
            name_lbl = ctk.CTkLabel(row_frame, text=f"{sub['name']}:", font=(self.tm.main_font(), 15), text_color=self.tm.text_sub(), justify="left", wraplength=200, anchor="w")
            name_lbl.pack(side="left", fill="x", expand=True)

        # Horizontally Scrollable Subjects (Categorized) (Right Side)
        subj_container = ctk.CTkFrame(bottom_row, fg_color="transparent")
        subj_container.pack(side="right", fill="both", expand=True, padx=10)
        
        majors = [s for s in metrics["subjects"] if s.get("category") == "Major"]
        minors = [s for s in metrics["subjects"] if s.get("category") == "Minor"]

        if majors:
            ctk.CTkLabel(subj_container, text="Major Subjects", font=(self.tm.main_font(), 16, "bold"), text_color=self.tm.text_main()).pack(anchor="w", padx=5, pady=(0, 10))
            major_scroll = ctk.CTkScrollableFrame(subj_container, fg_color="transparent", orientation="horizontal", height=200, scrollbar_button_color=self.tm.bg_main(), scrollbar_button_hover_color=self.tm.text_sub())
            major_scroll.pack(fill="x", pady=(0, 20))
            
            for sub in majors:
                c = ctk.CTkFrame(major_scroll, fg_color=self.major_color, corner_radius=15, width=160, height=185, cursor="hand2", border_width=2, border_color=self.tm.border_main())
                c.pack(side="left", padx=10, pady=5)
                c.pack_propagate(False)
                
                nav_cmd = lambda e, s_id=sub['id'], s_name=sub['name']: self.show_view_callback("Tasks", subject_id=s_id, subject_name=s_name, source_view="Home")
                c.bind("<Button-1>", nav_cmd)
                
                # Truncate text if it's incredibly long, and wrap it
                display_name = sub['name']
                if len(display_name) > 25:
                    display_name = display_name[:22] + "..."
                    
                l1 = ctk.CTkLabel(c, text=display_name, font=(self.tm.main_font(), 14, "bold"), text_color="#1A1A1A", cursor="hand2", wraplength=140, height=40)
                l1.pack(pady=(15, 0), padx=10)
                l1.bind("<Button-1>", nav_cmd)
                
                l2 = ctk.CTkLabel(c, text="📖", font=(self.tm.main_font(), 42), cursor="hand2")
                l2.pack(expand=True)
                l2.bind("<Button-1>", nav_cmd)
                
                pending_text = "No pending" if sub['pending_task_count'] == 0 else f"{sub['pending_task_count']} pending"
                l3 = ctk.CTkLabel(c, text=pending_text, font=(self.tm.main_font(), 13), text_color="#333333", cursor="hand2")
                l3.pack(pady=(0, 15), side="bottom")
                l3.bind("<Button-1>", nav_cmd)

        if minors:
            ctk.CTkLabel(subj_container, text="Minor Subjects", font=(self.tm.main_font(), 16, "bold"), text_color=self.tm.text_main()).pack(anchor="w", padx=5, pady=(10, 10))
            minor_scroll = ctk.CTkScrollableFrame(subj_container, fg_color="transparent", orientation="horizontal", height=200, scrollbar_button_color=self.tm.bg_main(), scrollbar_button_hover_color=self.tm.text_sub())
            minor_scroll.pack(fill="x")
            
            for sub in minors:
                c = ctk.CTkFrame(minor_scroll, fg_color=self.minor_color, corner_radius=15, width=160, height=185, cursor="hand2", border_width=2, border_color=self.tm.border_main())
                c.pack(side="left", padx=10, pady=5)
                c.pack_propagate(False)
                
                nav_cmd = lambda e, s_id=sub['id'], s_name=sub['name']: self.show_view_callback("Tasks", subject_id=s_id, subject_name=s_name, source_view="Home")
                c.bind("<Button-1>", nav_cmd)
                
                # Truncate text if it's incredibly long, and wrap it
                display_name = sub['name']
                if len(display_name) > 25:
                    display_name = display_name[:22] + "..."
                    
                l1 = ctk.CTkLabel(c, text=display_name, font=(self.tm.main_font(), 14, "bold"), text_color="#1A1A1A", cursor="hand2", wraplength=140, height=40)
                l1.pack(pady=(15, 0), padx=10)
                l1.bind("<Button-1>", nav_cmd)
                
                l2 = ctk.CTkLabel(c, text="📘", font=(self.tm.main_font(), 42), cursor="hand2")
                l2.pack(expand=True)
                l2.bind("<Button-1>", nav_cmd)
                
                pending_text = "No pending" if sub['pending_task_count'] == 0 else f"{sub['pending_task_count']} pending"
                l3 = ctk.CTkLabel(c, text=pending_text, font=(self.tm.main_font(), 13), text_color="#333333", cursor="hand2")
                l3.pack(pady=(0, 15), side="bottom")
                l3.bind("<Button-1>", nav_cmd)
