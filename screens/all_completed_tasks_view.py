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
        
        # We need this for the popups
        from tkinter import messagebox
        self.messagebox = messagebox
        
        self.setup_ui()
        self.load_tasks()

    def setup_ui(self):
        # Header Container
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 5))
        
        header_frame.columnconfigure(0, weight=1, uniform="header")
        header_frame.columnconfigure(1, weight=1, uniform="header")
        header_frame.columnconfigure(2, weight=1, uniform="header")
        
        # --- LEFT SIDE BUTTONS ---
        left_btns = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_btns.grid(row=0, column=0, sticky="w")

        back_btn = ctk.CTkButton(left_btns, text="← Back", width=60, fg_color="transparent", 
                                 text_color=self.tm.text_main(), hover_color=self.tm.bg_card(), 
                                 font=(self.tm.main_font(), 14), command=lambda: self.show_view_callback("History"))
        back_btn.pack(side="left")
        
        # --- CENTER CONTAINER ---
        center_f = ctk.CTkFrame(header_frame, fg_color="transparent")
        center_f.grid(row=0, column=1)

        # Title
        ctk.CTkLabel(center_f, text="All Completed Tasks", font=(self.tm.main_font(), 26, "bold"), 
                     text_color=self.tm.text_main()).pack()

        # Task List Area
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=self.tm.bg_main(), scrollbar_button_hover_color=self.tm.text_sub())
        self.scroll.pack(fill="both", expand=True, padx=10, pady=5)

    def load_tasks(self):
        self._render_id += 1
        current_render = self._render_id

        for widget in self.scroll.winfo_children():
            widget.destroy()

        tasks = self.db.get_completed_tasks(self.user_id) if self.user_id else []
        
        if not tasks:
            ctk.CTkLabel(self.scroll, text="No completed tasks found.", font=(self.tm.main_font(), 14, "italic"), text_color=self.tm.text_sub()).pack(pady=40)
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
            self._create_task_card(tasks[i])

        if end < len(tasks):
            self.after(10, lambda: self._render_completed_chunk(tasks, end, render_id, chunk_size))

    def _create_task_card(self, task):
        card = ctk.CTkFrame(self.scroll, fg_color=self.tm.bg_sub(), border_color=self.tm.border_main(), border_width=2, corner_radius=10, height=65)
        card.pack(fill="x", padx=10, pady=5)
        card.pack_propagate(False)

        # --- Pack action buttons FIRST (side="right") to anchor them ---
        act_frame = ctk.CTkFrame(card, fg_color="transparent")
        act_frame.pack(side="right", padx=15)
        
        def toggle_status():
            if self.messagebox.askyesno("Confirm Action", "Are you sure you want to unmark this task?"):
                self.db.update_task_status(task['id'], 'pending')
                self.load_tasks()

        ctk.CTkButton(act_frame, text="Unmark Task", font=(self.tm.main_font(), 11, "bold"), width=100, height=24, corner_radius=8,
                      fg_color=self.tm.text_sub(), text_color="#FFFFFF", hover_color=self.tm.border_main(),
                      command=toggle_status).pack(side="left", padx=5)
        
        ctk.CTkButton(act_frame, text="Manage", font=(self.tm.main_font(), 11, "bold"), width=60, height=24, corner_radius=8,
                      fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover(),
                      command=lambda t=task: self.edit_task(t)).pack(side="left", padx=5)
                      
        ctk.CTkButton(act_frame, text="Delete", font=(self.tm.main_font(), 11, "bold"), width=60, height=24, corner_radius=8,
                      fg_color=self.tm.error_color(), text_color="#FFFFFF", hover_color=self.tm.error_hover(),
                      command=lambda t=task: self.delete_task(t)).pack(side="left", padx=5)

        # Priority Indicator
        prio_color = "#FF6B6B" if task['priority'] == 'High' else ("#EAB308" if task['priority'] == 'Medium' else "#22C55E")
        ctk.CTkLabel(card, text=task['priority'], font=(self.tm.main_font(), 13, "bold"), text_color=prio_color, width=70, anchor="w").pack(side="right", padx=(0, 5))

        # --- Left-side content ---
        left = ctk.CTkFrame(card, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True, padx=15, pady=10)
        
        # Truncate name
        display_name = task['name']
        if len(display_name) > 35: display_name = display_name[:32] + "..."
        
        name_lbl = ctk.CTkLabel(left, text=display_name, font=(self.tm.main_font(), 15, "bold"), text_color=self.tm.text_sub(), anchor="w")
        name_lbl.pack(fill="x")
        
        sub = ctk.CTkFrame(left, fg_color="transparent")
        sub.pack(fill="x")
        
        # Truncate subject
        display_sub = task['subject_name']
        if len(display_sub) > 25: display_sub = display_sub[:22] + "..."
        
        subj_lbl = ctk.CTkLabel(sub, text=display_sub, font=(self.tm.main_font(), 11), text_color=self.tm.text_sub(), width=150, anchor="w")
        subj_lbl.pack(side="left")
        
        time_lbl = None
        if task.get('completed_at'):
            time_lbl = ctk.CTkLabel(sub, text=f"🕒 {task['completed_at'][:16]}", font=(self.tm.main_font(), 11), text_color=self.tm.accent_color(), width=150, anchor="w")
            time_lbl.pack(side="left", padx=10)

        # Clickability
        card.configure(cursor="hand2")
        left.configure(cursor="hand2")
        name_lbl.configure(cursor="hand2")
        sub.configure(cursor="hand2")
        subj_lbl.configure(cursor="hand2")
        if time_lbl: time_lbl.configure(cursor="hand2")

        def on_row_click(event, t=task):
            from screens.tasks_view import TaskDetailsPopup
            TaskDetailsPopup(self.winfo_toplevel(), t, self.db, self.load_tasks, t['subject_name'])

        card.bind("<Button-1>", on_row_click)
        left.bind("<Button-1>", on_row_click)
        name_lbl.bind("<Button-1>", on_row_click)
        sub.bind("<Button-1>", on_row_click)
        subj_lbl.bind("<Button-1>", on_row_click)
        if time_lbl: time_lbl.bind("<Button-1>", on_row_click)

    def edit_task(self, task):
        from screens.tasks_view import EditTaskPopup
        EditTaskPopup(self.winfo_toplevel(), self.db, task, task['subject_name'], self.load_tasks)

    def delete_task(self, task):
        if self.messagebox.askyesno("Delete", "Are you sure you want to delete this task?"):
            self.db.delete_task(task['id'])
            self.load_tasks()
