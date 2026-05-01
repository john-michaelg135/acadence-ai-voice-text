import customtkinter as ctk
from utils.theme_manager import ThemeManager
from database.db_manager import DatabaseManager

class AllCompletedTasksView(ctk.CTkFrame):
    def __init__(self, master, user_info, show_view_callback):
        self.tm = ThemeManager()
        super().__init__(master, fg_color="transparent")
        self.user_info = user_info
        self.db = DatabaseManager()
        self.show_view_callback = show_view_callback
        self.user_id = self.user_info['id'] if self.user_info else None
        self._render_id = 0
        
        self.setup_ui()
        self.load_tasks()

    def setup_ui(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        back_btn = ctk.CTkButton(header_frame, text="← Back", width=60, fg_color="transparent", text_color=self.tm.text_main(), 
                                 hover_color=self.tm.bg_card(), font=("Arial", 14), command=lambda: self.show_view_callback("History"))
        back_btn.pack(side="left")
        
        ctk.CTkLabel(header_frame, text="All Completed Tasks", font=("Arial", 22, "bold"), text_color=self.tm.text_main()).pack(side="left", padx=20)
        
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=self.tm.bg_main(), scrollbar_button_hover_color=self.tm.text_sub())
        self.scroll.pack(fill="both", expand=True, padx=10, pady=5)

    def load_tasks(self):
        self._render_id += 1
        current_render = self._render_id

        for widget in self.scroll.winfo_children():
            widget.destroy()

        tasks = self.db.get_completed_tasks(self.user_id) if self.user_id else []
        
        if not tasks:
            ctk.CTkLabel(self.scroll, text="No completed tasks found.", font=("Arial", 14, "italic"), text_color=self.tm.text_sub()).pack(pady=40)
            return

        self._render_completed_chunk(tasks, 0, current_render)

    def _render_completed_chunk(self, tasks, index, render_id, chunk_size=15):
        """Renders completed task cards in chunks to prevent UI freezing."""
        if render_id != self._render_id:
            return
        if not self.winfo_exists():
            return

        end = min(index + chunk_size, len(tasks))
        for i in range(index, end):
            task = tasks[i]
            card = ctk.CTkFrame(self.scroll, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=2, corner_radius=10)
            card.pack(fill="x", padx=10, pady=5)
            
            pill = ctk.CTkLabel(card, text="Completed", font=("Arial", 11, "bold"), 
                                fg_color=self.tm.success_color(), text_color="#FFFFFF", 
                                corner_radius=10, width=80, height=24)
            pill.pack(side="left", padx=15, pady=15)
            
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True, pady=10)
            
            ctk.CTkLabel(info_frame, text=task['name'], font=("Arial", 15, "bold"), text_color=self.tm.text_main(), anchor="w").pack(fill="x")
            
            sub_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            sub_frame.pack(fill="x")
            
            p_color = self.tm.error_color() if task['priority'] == 'High' else self.tm.warning_color() if task['priority'] == 'Medium' else self.tm.success_color()
            ctk.CTkLabel(sub_frame, text=task['priority'], font=("Arial", 11, "bold"), text_color=p_color).pack(side="left", padx=(0, 10))
            ctk.CTkLabel(sub_frame, text=task['subject_name'], font=("Arial", 11), text_color=self.tm.text_sub()).pack(side="left", padx=(0, 10))
            
            if task.get('completed_at'):
                # Format to a nice string if it's a timestamp
                ctk.CTkLabel(sub_frame, text=f"🕒 {task['completed_at'][:16]}", font=("Arial", 11), text_color=self.tm.text_sub()).pack(side="left")

        if end < len(tasks):
            self.after(10, lambda: self._render_completed_chunk(tasks, end, render_id, chunk_size))
