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
        
        # State for sorting: "ASC" (Closest) or "DESC" (Furthest)
        self.sort_order = "ASC"
        self._raw_tasks = []  # Cache — filter/sort reuse this without re-querying the DB
        self._render_id = 0   # Incremented on each load to cancel stale renders
        
        self.setup_ui()

    def setup_ui(self):
        # Header Container
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        header_frame.columnconfigure(1, weight=1) 

        # --- LEFT SIDE: Back Button ---
        back_btn = ctk.CTkButton(header_frame, text="← Back", width=60, fg_color="transparent", 
                                 text_color=self.tm.text_main(), hover_color=self.tm.bg_card(), 
                                 font=(self.tm.main_font(), 14), command=lambda: self.show_view_callback("Insights"))
        back_btn.grid(row=0, column=0, sticky="w")
        
        # --- CENTER: Title ---
        ctk.CTkLabel(header_frame, text="All Pending Tasks", font=(self.tm.main_font(), 22, "bold"), 
                     text_color=self.tm.text_main()).grid(row=0, column=1, pady=(0, 5))
        
        # --- ROW 1: Controls ---
        sort_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        sort_container.grid(row=1, column=0, sticky="w", pady=(10, 0))

        # Fixed width to prevent layout popping
        self.sort_btn = ctk.CTkButton(
            sort_container, 
            text="Sort: Closest First", 
            width=150, 
            height=32, 
            corner_radius=16, 
            font=(self.tm.main_font(), 11, "bold"),
            command=self.toggle_sort
        )
        self.sort_btn.pack()

        # Priority Filter (Center-aligned)
        self.filter_container = ctk.CTkFrame(header_frame, fg_color=self.tm.bg_sub(), corner_radius=20, 
                                    border_color=self.tm.border_main(), border_width=1)
        self.filter_container.grid(row=1, column=1, pady=(10, 0))
        
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
            
        today = datetime.today().strftime('%Y-%m-%d')
        self._render_pending_chunk(tasks, 0, today, current_render)

    def _render_pending_chunk(self, tasks, index, today, render_id, chunk_size=15):
        """Renders pending task rows in chunks to prevent UI freezing."""
        if render_id != self._render_id:
            return
        if not self.winfo_exists():
            return

        end = min(index + chunk_size, len(tasks))
        for i in range(index, end):
            task = tasks[i]
            row = ctk.CTkFrame(self.scroll, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=2, corner_radius=10)
            row.pack(fill="x", padx=10, pady=5)
            
            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True, padx=15, pady=10)
            
            ctk.CTkLabel(left, text=task['name'], font=(self.tm.main_font(), 15, "bold"), text_color=self.tm.text_main(), anchor="w").pack(fill="x")
            
            sub = ctk.CTkFrame(left, fg_color="transparent")
            sub.pack(fill="x")
            
            flag_color = self.tm.error_color() if task['priority'] == 'High' else self.tm.warning_color() if task['priority'] == 'Medium' else self.tm.success_color()
            
            ctk.CTkLabel(sub, text=task['priority'], font=(self.tm.main_font(), 11, "bold"), text_color=flag_color).pack(side="left", padx=(0, 10))
            ctk.CTkLabel(sub, text=task['subject_name'], font=(self.tm.main_font(), 11), text_color=self.tm.text_sub()).pack(side="left", padx=(0, 10))
            
            deadline_str = task.get('deadline')
            if deadline_str:
                ctk.CTkLabel(sub, text=f"📅 {deadline_str}", font=(self.tm.main_font(), 11), text_color=self.tm.accent_color()).pack(side="left")
                if deadline_str < today:
                    ctk.CTkLabel(sub, text="Overdue", font=(self.tm.main_font(), 10, "bold"), text_color="#FFFFFF", fg_color=self.tm.error_color(), corner_radius=6, width=60, height=20).pack(side="left", padx=(10, 0))

            view_btn = ctk.CTkButton(row, text="❯", font=(self.tm.main_font(), 18), text_color=self.tm.text_sub(), fg_color="transparent", hover_color=self.tm.bg_sub(), width=40,
                                     command=lambda s_id=task['subject_id'], s_name=task['subject_name']: self.show_view_callback("Tasks", s_id, s_name))
            view_btn.pack(side="right", padx=10)

        if end < len(tasks):
            self.after(10, lambda: self._render_pending_chunk(tasks, end, today, render_id, chunk_size))