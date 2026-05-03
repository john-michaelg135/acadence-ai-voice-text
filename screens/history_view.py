import customtkinter as ctk
from utils.theme_manager import ThemeManager
from database.db_manager import DatabaseManager
from utils.animation_manager import animate_bar_grow

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
        ctk.CTkLabel(self, text="History & Analytics", font=(self.tm.main_font(), 28, "bold"), text_color=self.tm.text_main()).pack(anchor="w", padx=30, pady=(20, 10))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=self.tm.bg_main(), scrollbar_button_hover_color=self.tm.text_sub())
        scroll.pack(fill="both", expand=True, padx=20, pady=5)
        
        # Grid Container
        grid_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, pady=5)
        
        # LEFT COLUMN
        left_col = ctk.CTkFrame(grid_frame, fg_color="transparent", width=420)
        left_col.pack(side="left", fill="both", padx=10)
        
        # Invisible spacer to force minimum width of left column
        ctk.CTkFrame(left_col, fg_color="transparent", width=380, height=1).pack()
        
        # 1. Banner
        banner = ctk.CTkFrame(left_col, fg_color=self.tm.accent_color(), corner_radius=15)
        banner.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(banner, text="Your recently completed tasks\nand productivity analytics.", 
                     font=(self.tm.main_font(), 16), text_color=self.tm.accent_text(), justify="center").pack(pady=30)
                     
        # 3. Bar Chart Card
        chart_card = ctk.CTkFrame(left_col, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=2, corner_radius=15)
        chart_card.pack(fill="both", expand=True)
        
        ctk.CTkLabel(chart_card, text="Task Completion by Subject", font=(self.tm.main_font(), 16, "bold"), text_color=self.tm.text_main(), wraplength=300).pack(pady=(20, 20))
        
        chart_data = self.db.get_completed_tasks_by_subject(self.user_id) if self.user_id else []
        
        if not chart_data or all(d['count'] == 0 for d in chart_data):
            empty_frame = ctk.CTkFrame(chart_card, fg_color="transparent")
            empty_frame.pack(fill="both", expand=True, pady=40)
            ctk.CTkLabel(empty_frame, text="📊", font=(self.tm.main_font(), 40)).pack(expand=True, side="bottom", pady=(0, 10))
            
            text_frame = ctk.CTkFrame(chart_card, fg_color="transparent")
            text_frame.pack(fill="both", expand=True, pady=(0, 40))
            ctk.CTkLabel(text_frame, text="No user data yet.\nStart completing tasks.", 
                         font=(self.tm.main_font(), 14), text_color=self.tm.text_sub(), justify="center").pack(side="top")
        else:
            valid_bars = [d for d in chart_data if d['count'] > 0]
            num_bars = len(valid_bars)

            bar_width = 35
            spacing = 65
            req_width = max(360, num_bars * (bar_width + spacing) + spacing)
            
            # Increased height and padding for Poppins font metrics
            c_height = 310
            
            bg_hex = self.tm.bg_card()[0] if ctk.get_appearance_mode()=="Light" else self.tm.bg_card()[1]
            accent_hex = self.tm.accent_color()[0] if ctk.get_appearance_mode()=="Light" else self.tm.accent_color()[1]
            text_hex = self.tm.text_sub()[0] if ctk.get_appearance_mode()=="Light" else self.tm.text_sub()[1]
            
            # Use CTkScrollableFrame for horizontal scrolling
            scroll_frame = ctk.CTkScrollableFrame(chart_card, orientation="horizontal", fg_color="transparent", height=340)
            scroll_frame.pack(fill="x", pady=(0, 20), padx=10)
            
            canvas = ctk.CTkCanvas(scroll_frame, width=req_width, height=c_height, bg=bg_hex, highlightthickness=0)
            canvas.pack()
            
            max_val = max([d['count'] for d in chart_data] + [1])
            
            if num_bars > 0:
                total_bar_width = (num_bars * bar_width) + ((num_bars - 1) * spacing)
                start_x = (req_width - total_bar_width) / 2
                if start_x < 10: start_x = 10
                
                # More room at bottom for Poppins
                bottom_y = c_height - 75
                
                drawn_idx = 0
                for data in chart_data:
                    if data['count'] == 0: continue
                    target_height = (data['count'] / max_val) * (c_height - 120)
                    x0 = start_x + (drawn_idx * (bar_width + spacing))
                    
                    r = min(8, bar_width / 2)
                    r = min(r, target_height / 2)
                    
                    # Create bar at baseline with height=1 (will be animated)
                    bar_frame = ctk.CTkFrame(canvas, fg_color=accent_hex, corner_radius=int(r))
                    win_id = canvas.create_window(x0, bottom_y - 1, anchor="nw", window=bar_frame, width=bar_width, height=1)
                    
                    bottom_square = None
                    if target_height > r:
                        bottom_square = ctk.CTkFrame(canvas, fg_color=accent_hex, corner_radius=0)
                        canvas.create_window(x0, bottom_y, anchor="nw", window=bottom_square, width=bar_width, height=1)
                        
                    # Subject name label (always visible)
                    display_name = data['name']
                    if len(display_name) > 18:
                        display_name = display_name[:15] + "..."
                    canvas.create_text(x0 + (bar_width/2), bottom_y + 10, text=display_name, fill=text_hex, font=(self.tm.main_font(), 11), width=bar_width + spacing - 5, justify="center", anchor="n")
                    # Count label (hidden initially, revealed after animation)
                    count_id = canvas.create_text(x0 + (bar_width/2), bottom_y - 12, text=str(data['count']), fill=text_hex, font=(self.tm.main_font(), 11, "bold"), state="hidden")
                    
                    # Schedule staggered animation — wait 300ms for page load, then stagger 80ms
                    delay = 300 + (drawn_idx * 80)
                    canvas.after(delay, lambda wid=win_id, bf=bar_frame, bs=bottom_square, cid=count_id, 
                                 _x0=x0, _th=target_height, _r=r:
                        animate_bar_grow(canvas, wid, bf, bs, cid, _x0, bottom_y, _th, bar_width, _r, 
                                        duration_ms=350, steps=14))
                    drawn_idx += 1

        # RIGHT COLUMN
        right_col = ctk.CTkFrame(grid_frame, fg_color="transparent")
        right_col.pack(side="right", fill="both", expand=True, padx=10)

        # 2. Completion List Card
        list_card = ctk.CTkFrame(right_col, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=2, corner_radius=15)
        list_card.pack(fill="both", expand=True)
        
        ctk.CTkLabel(list_card, text="Recent Completions", font=(self.tm.main_font(), 18, "bold"), text_color=self.tm.text_main()).pack(pady=(20, 5))
        ctk.CTkLabel(list_card, text="Tasks marked as done appear here.", font=(self.tm.main_font(), 14), text_color=self.tm.text_sub()).pack(pady=(0, 20))
        
        recent_tasks = self.db.get_completed_tasks(self.user_id, limit=6) if self.user_id else []
        
        if not recent_tasks:
            empty_container = ctk.CTkFrame(list_card, fg_color="transparent")
            empty_container.pack(fill="both", expand=True)
            ctk.CTkLabel(empty_container, text="✅", font=(self.tm.main_font(), 35)).pack(expand=True, side="bottom", pady=(0, 10))
            
            text_container = ctk.CTkFrame(list_card, fg_color="transparent")
            text_container.pack(fill="both", expand=True)
            ctk.CTkLabel(text_container, text="No completed tasks yet.\nYour recent completions will appear here.", 
                         font=(self.tm.main_font(), 14), text_color=self.tm.text_sub(), justify="center").pack(side="top")
        else:
            for task in recent_tasks:
                task_row = ctk.CTkFrame(list_card, fg_color=self.tm.bg_sub(), corner_radius=10)
                task_row.pack(fill="x", padx=20, pady=6)
                
                check_lbl = ctk.CTkLabel(task_row, text="Completed", font=(self.tm.main_font(), 11, "bold"), 
                                         fg_color=self.tm.success_color(), text_color="#FFFFFF", 
                                         corner_radius=10, width=80, height=24)
                check_lbl.pack(side="left", padx=(15, 15), pady=15)
                
                info_frame = ctk.CTkFrame(task_row, fg_color="transparent")
                info_frame.pack(side="left", fill="x", expand=True, pady=10)
                
                ctk.CTkLabel(info_frame, text=task['name'], font=(self.tm.main_font(), 15, "bold"), text_color=self.tm.text_main(), anchor="w").pack(fill="x")
                
                sub_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
                sub_frame.pack(fill="x")
                
                p_color = self.tm.error_color() if task['priority'] == 'High' else self.tm.warning_color() if task['priority'] == 'Medium' else self.tm.success_color()
                ctk.CTkLabel(sub_frame, text=task['priority'], font=(self.tm.main_font(), 12, "bold"), text_color=p_color).pack(side="left", padx=(0, 15))
                ctk.CTkLabel(sub_frame, text=task['subject_name'], font=(self.tm.main_font(), 12), text_color=self.tm.text_sub()).pack(side="left", padx=(0, 15))
                
                if task.get('completed_at'):
                    ctk.CTkLabel(sub_frame, text=f"🕒 {task['completed_at'][:16]}", font=(self.tm.main_font(), 11), text_color=self.tm.accent_color()).pack(side="left")
                
        # View All Button
        ctk.CTkButton(list_card, text="View All Completed Tasks", fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), 
                      hover_color=self.tm.accent_hover(), font=(self.tm.main_font(), 15, "bold"), height=50, corner_radius=25,
                      command=lambda: self.show_view_callback("AllCompleted")).pack(fill="x", side="bottom", padx=40, pady=30)

    def refresh(self):
        """Called by DashboardScreen when the cached view is shown to refresh data."""
        for widget in self.winfo_children():
            widget.destroy()
        self.setup_ui()

