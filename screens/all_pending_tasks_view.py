import customtkinter as ctk
from utils.theme_manager import ThemeManager
from database.db_manager import DatabaseManager
from datetime import datetime

class AllPendingTasksView(ctk.CTkFrame):
    def __init__(self, master, user_info, show_view_callback):
        self.tm = ThemeManager()
        super().__init__(master, fg_color="transparent")
        self.user_info = user_info
        self.db = DatabaseManager()
        self.show_view_callback = show_view_callback
        self.user_id = self.user_info['id'] if self.user_info else None
        
        # We need this for the popups
        from tkinter import messagebox
        self.messagebox = messagebox
        
        # State for sorting: "ASC" (Closest) or "DESC" (Furthest)
        self.sort_order = "ASC"
        self._raw_tasks = []  # Cache — filter/sort reuse this without re-querying the DB
        self._render_id = 0   # Incremented on each load to cancel stale renders
        
        self.setup_ui()

    def setup_ui(self):
        # Header Container
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 5))
        
        header_frame.columnconfigure(0, weight=1, uniform="header")
        header_frame.columnconfigure(1, weight=1, uniform="header")
        header_frame.columnconfigure(2, weight=1, uniform="header")
        
        # --- LEFT SIDE BUTTONS ---
        # Using a container for left-side buttons
        left_btns = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_btns.grid(row=0, column=0, sticky="w")

        back_btn = ctk.CTkButton(left_btns, text="← Back", width=60, fg_color="transparent", 
                                 text_color=self.tm.text_main(), hover_color=self.tm.bg_card(), 
                                 font=(self.tm.main_font(), 14), command=lambda: self.show_view_callback("Insights"))
        back_btn.pack(side="left", padx=(0, 10))
        
        self.sort_btn = ctk.CTkButton(
            left_btns, text="Sort: Closest First", width=140, height=32, corner_radius=16, 
            font=(self.tm.main_font(), 11, "bold"), command=self.toggle_sort
        )
        self.sort_btn.pack(side="left")

        # --- CENTER CONTAINER ---
        center_f = ctk.CTkFrame(header_frame, fg_color="transparent")
        center_f.grid(row=0, column=1)

        # Title
        ctk.CTkLabel(center_f, text="All Pending Tasks", font=(self.tm.main_font(), 26, "bold"), 
                     text_color=self.tm.text_main()).pack(pady=(0, 5))
        
        # Priority Filter (Centered)
        self.filter_container = ctk.CTkFrame(center_f, fg_color=self.tm.bg_sub(), corner_radius=20, 
                                    border_color=self.tm.border_main(), border_width=1)
        self.filter_container.pack()
        
        self.current_filter = ctk.StringVar(value="All")
        self.filter_buttons = {}
        self._filter_order = ["All", "High", "Medium", "Low"]
        for prio in self._filter_order:
            btn = ctk.CTkButton(
                self.filter_container, text=prio, width=80, height=32, corner_radius=16,
                font=(self.tm.main_font(), 12, "bold"),
                command=lambda p=prio: self.set_filter(p)
            )
            btn.pack(side="left", padx=3, pady=3)
            self.filter_buttons[prio] = btn
        
        self.update_filter_buttons()
        self.update_sort_button_style() 

        # Task List Area
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=self.tm.bg_main(), scrollbar_button_hover_color=self.tm.text_sub())
        self.scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        self._fetch_and_render()

    def toggle_sort(self):
        self.sort_order = "DESC" if self.sort_order == "ASC" else "ASC"
        self.update_sort_button_style()
        self.load_tasks()

    def update_sort_button_style(self):
        """Updates style with a functional hover 'fill' effect."""
        if self.sort_order == "ASC":
            # Closest First: Bordered style
            self.sort_btn.configure(
                text="Sort: Closest First",
                fg_color=self.tm.bg_main(), 
                text_color=self.tm.accent_color(),
                border_color=self.tm.accent_color(),
                border_width=2,
                hover_color=self.tm.bg_sub() 
            )
        else:
            # Furthest First: Fully colored style
            self.sort_btn.configure(
                text="Sort: Furthest First",
                fg_color=self.tm.accent_color(),
                text_color=self.tm.accent_text(),
                border_width=0,
                hover_color=self.tm.accent_hover()
            )

    def set_filter(self, val):
        self.current_filter.set(val)
        self.update_filter_buttons()
        self.load_tasks()

    def update_filter_buttons(self):
        """Instant color swap — all buttons update in same frame, no flicker."""
        curr = self.current_filter.get()
        for val, btn in self.filter_buttons.items():
            if val == curr:
                btn.configure(fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover())
            else:
                btn.configure(fg_color="transparent", text_color=self.tm.text_sub(), hover_color=self.tm.border_main())

    def _fetch_and_render(self):
        """Fetches fresh data from DB, then re-renders. Called on initial load."""
        self._raw_tasks = self.db.get_all_pending_tasks(self.user_id) if self.user_id else []
        self.load_tasks()

    def load_tasks(self):
        """Re-renders from cache using chunked rendering for performance."""
        self._render_id += 1
        current_render = self._render_id

        for widget in self.scroll.winfo_children():
            widget.destroy()

        tasks = list(self._raw_tasks)

        if self.current_filter.get() != "All":
            tasks = [t for t in tasks if t['priority'] == self.current_filter.get()]

        # Sorting logic
        tasks.sort(
            key=lambda x: x.get('deadline') or '9999-12-31', 
            reverse=(self.sort_order == "DESC")
        )
            
        if not tasks:
            msg = "You have no pending tasks!" if self.current_filter.get() == "All" else f"No pending {self.current_filter.get()} priority tasks."
            ctk.CTkLabel(self.scroll, text=msg, font=(self.tm.main_font(), 14, "italic"), text_color=self.tm.text_sub()).pack(pady=40)
            return
            
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        self._render_pending_chunk(tasks, 0, now_str, current_render)

    def _render_pending_chunk(self, tasks, index, now_str, render_id, chunk_size=15):
        """Renders pending task cards in chunks to prevent UI freezing."""
        if render_id != self._render_id:
            return
        if not self.winfo_exists():
            return
            
        end = min(index + chunk_size, len(tasks))
        for i in range(index, end):
            self._create_task_card(tasks[i], now_str)
            
        if end < len(tasks):
            self.after(10, lambda: self._render_pending_chunk(tasks, end, now_str, render_id, chunk_size))

    def _create_task_card(self, task, now_str):
        card = ctk.CTkFrame(self.scroll, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=2, corner_radius=10, height=65)
        card.pack(fill="x", padx=10, pady=5)
        card.pack_propagate(False)

        # --- Pack action buttons FIRST (side="right") to anchor them ---
        act_frame = ctk.CTkFrame(card, fg_color="transparent")
        act_frame.pack(side="right", padx=15)
        
        def toggle_status():
            if self.messagebox.askyesno("Confirm Action", "Are you sure you want to mark this task as done?", parent=self.winfo_toplevel()):
                self.db.update_task_status(task['id'], 'completed')
                self._fetch_and_render()
                self.messagebox.showinfo("Success", "Task marked as completed!", parent=self.winfo_toplevel())

        ctk.CTkButton(act_frame, text="Mark as Done", font=(self.tm.main_font(), 11, "bold"), width=100, height=24, corner_radius=8,
                      fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover(),
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
        
        name_lbl = ctk.CTkLabel(left, text=display_name, font=(self.tm.main_font(), 15, "bold"), text_color=self.tm.text_main(), anchor="w")
        name_lbl.pack(fill="x")
        
        sub = ctk.CTkFrame(left, fg_color="transparent")
        sub.pack(fill="x")
        
        # Truncate subject
        display_sub = task['subject_name']
        if len(display_sub) > 25: display_sub = display_sub[:22] + "..."
        
        subj_lbl = ctk.CTkLabel(sub, text=display_sub, font=(self.tm.main_font(), 11), text_color=self.tm.text_sub(), width=150, anchor="w")
        subj_lbl.pack(side="left")
        
        deadline_str = task.get('deadline')
        deadline_lbl = None
        overdue_lbl = None
        if deadline_str:
            deadline_lbl = ctk.CTkLabel(sub, text=f"📅 {deadline_str}", font=(self.tm.main_font(), 11), text_color=self.tm.accent_color(), width=120, anchor="w")
            deadline_lbl.pack(side="left", padx=10)
            
            # If deadline is date-only, assume it's due at end of day (23:59) for overdue calculation
            compare_deadline = deadline_str if len(deadline_str) > 10 else deadline_str + " 23:59"
            
            if compare_deadline < now_str:
                overdue_lbl = ctk.CTkLabel(sub, text="Overdue", font=(self.tm.main_font(), 10, "bold"), text_color="#FFFFFF", fg_color=self.tm.error_color(), corner_radius=6, width=60, height=20)
                overdue_lbl.pack(side="left")

        # Clickability
        card.configure(cursor="hand2")
        left.configure(cursor="hand2")
        name_lbl.configure(cursor="hand2")
        sub.configure(cursor="hand2")
        subj_lbl.configure(cursor="hand2")
        if deadline_lbl: deadline_lbl.configure(cursor="hand2")
        if overdue_lbl: overdue_lbl.configure(cursor="hand2")

        def on_row_click(event, t=task):
            from screens.tasks_view import TaskDetailsPopup
            TaskDetailsPopup(self.winfo_toplevel(), t, self.db, self._fetch_and_render, t['subject_name'])

        card.bind("<Button-1>", on_row_click)
        left.bind("<Button-1>", on_row_click)
        name_lbl.bind("<Button-1>", on_row_click)
        sub.bind("<Button-1>", on_row_click)
        subj_lbl.bind("<Button-1>", on_row_click)
        if deadline_lbl: deadline_lbl.bind("<Button-1>", on_row_click)
        if overdue_lbl: overdue_lbl.bind("<Button-1>", on_row_click)

    def edit_task(self, task):
        from screens.tasks_view import EditTaskPopup
        EditTaskPopup(self.winfo_toplevel(), self.db, task, task['subject_name'], self._fetch_and_render)

    def delete_task(self, task):
        if self.messagebox.askyesno("Delete", "Are you sure you want to delete this task?", parent=self.winfo_toplevel()):
            self.db.delete_task(task['id'])
            self._fetch_and_render()
            self.messagebox.showinfo("Success", "Task deleted successfully!", parent=self.winfo_toplevel())