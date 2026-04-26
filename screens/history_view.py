import customtkinter as ctk
from utils.theme_manager import ThemeManager
from database.db_manager import DatabaseManager

class HistoryView(ctk.CTkFrame):
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
        ctk.CTkLabel(self, text="History & Analytics", font=("Arial", 28, "bold"), text_color=self.tm.text_main()).pack(anchor="w", padx=20, pady=(20, 10))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 1. Banner
        banner = ctk.CTkFrame(scroll, fg_color=self.tm.accent_color(), corner_radius=15)
        banner.pack(fill="x", padx=10, pady=(0, 15))
        
        ctk.CTkLabel(banner, text="Four of your recently\ncompleted tasks are listed below.", 
                     font=("Arial", 16), text_color=self.tm.accent_text(), justify="center").pack(pady=20)
                     
        # 2. Completion List Card
        list_card = ctk.CTkFrame(scroll, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=1, corner_radius=15)
        list_card.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(list_card, text="Completion List", font=("Arial", 18, "bold"), text_color=self.tm.text_main()).pack(pady=(15, 5))
        ctk.CTkLabel(list_card, text="Tasks marked as done appear here.", font=("Arial", 12), text_color=self.tm.text_sub()).pack(pady=(0, 15))
        
        recent_tasks = self.db.get_completed_tasks(self.user_id, limit=4) if self.user_id else []
        
        if not recent_tasks:
            ctk.CTkLabel(list_card, text="No completed tasks yet.", font=("Arial", 13, "italic"), text_color=self.tm.text_sub()).pack(pady=20)
        else:
            for task in recent_tasks:
                task_row = ctk.CTkFrame(list_card, fg_color="transparent")
                task_row.pack(fill="x", padx=20, pady=5)
                
                # Check icon natively rendered
                check_lbl = ctk.CTkLabel(task_row, text="✅", font=("Arial", 20), text_color=self.tm.success_color())
                check_lbl.pack(side="left", padx=(0, 15))
                
                info_frame = ctk.CTkFrame(task_row, fg_color="transparent")
                info_frame.pack(side="left", fill="x", expand=True)
                
                ctk.CTkLabel(info_frame, text=task['name'], font=("Arial", 14, "bold"), text_color=self.tm.text_main(), anchor="w").pack(fill="x")
                
                sub_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
                sub_frame.pack(fill="x")
                
                p_color = self.tm.error_color() if task['priority'] == 'High' else self.tm.warning_color() if task['priority'] == 'Medium' else self.tm.success_color()
                ctk.CTkLabel(sub_frame, text=f"🏁 {task['priority']}", font=("Arial", 11, "bold"), text_color=p_color).pack(side="left", padx=(0, 10))
                ctk.CTkLabel(sub_frame, text=task['subject_name'], font=("Arial", 11), text_color=self.tm.text_sub()).pack(side="left")
                
        # View All Button
        ctk.CTkButton(list_card, text="View All Completed Tasks", fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), 
                      hover_color=self.tm.accent_hover(), font=("Arial", 13, "bold"), height=45, corner_radius=22,
                      command=lambda: self.show_view_callback("AllCompleted")).pack(fill="x", padx=20, pady=(15, 20))
                      
        # 3. Bar Chart Card
        chart_card = ctk.CTkFrame(scroll, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=1, corner_radius=15)
        chart_card.pack(fill="x", padx=10, pady=15)
        
        ctk.CTkLabel(chart_card, text="Task Completion by Subject", font=("Arial", 18, "bold"), text_color=self.tm.text_main()).pack(pady=(15, 20))
        
        chart_data = self.db.get_completed_tasks_by_subject(self.user_id) if self.user_id else []
        
        if not chart_data or all(d['count'] == 0 for d in chart_data):
            ctk.CTkLabel(chart_card, text="Not enough data to display chart.", font=("Arial", 13, "italic"), text_color=self.tm.text_sub()).pack(pady=30)
        else:
            # Native Canvas Bar Chart Implementation
            c_width = 320
            c_height = 200
            
            # Extract actual hex strings for Canvas
            bg_hex = self.tm.bg_card()[0] if ctk.get_appearance_mode()=="Light" else self.tm.bg_card()[1]
            accent_hex = self.tm.accent_color()[0] if ctk.get_appearance_mode()=="Light" else self.tm.accent_color()[1]
            text_hex = self.tm.text_sub()[0] if ctk.get_appearance_mode()=="Light" else self.tm.text_sub()[1]
            
            canvas = ctk.CTkCanvas(chart_card, width=c_width, height=c_height, bg=bg_hex, highlightthickness=0)
            canvas.pack(pady=(0, 20), padx=10)
            
            max_val = max(d['count'] for d in chart_data)
            if max_val == 0: max_val = 1
            
            bar_width = 40
            spacing = 20
            
            # Center the chart dynamically based on how many subjects have completions
            valid_bars = [d for d in chart_data if d['count'] > 0]
            total_width = (len(valid_bars) * bar_width) + ((len(valid_bars) - 1) * spacing)
            start_x = (c_width - total_width) / 2
            if start_x < 10: start_x = 10 # Provide 10px padding if it overflows
            
            bottom_y = c_height - 30 # Reserving space for bottom text labels
            
            drawn_idx = 0
            for data in chart_data:
                if data['count'] == 0: continue
                
                # Bar height ratio
                height = (data['count'] / max_val) * (c_height - 60) # max physical height is 140px
                
                x0 = start_x + (drawn_idx * (bar_width + spacing))
                y0 = bottom_y - height
                x1 = x0 + bar_width
                y1 = bottom_y
                
                # Draw rounded-like rectangle using polygon or standard rectangle
                # Canvas doesn't do rounded corners easily, standard rects for bar charts
                canvas.create_rectangle(x0, y0, x1, y1, fill=accent_hex, outline="")
                
                # Draw Bottom Label (truncate long subject names)
                name = data['name'][:6] + ".." if len(data['name']) > 8 else data['name']
                canvas.create_text(x0 + (bar_width/2), bottom_y + 15, text=name, fill=text_hex, font=("Arial", 10))
                
                # Draw Top Value count
                canvas.create_text(x0 + (bar_width/2), y0 - 10, text=str(data['count']), fill=text_hex, font=("Arial", 10, "bold"))
                
                drawn_idx += 1
