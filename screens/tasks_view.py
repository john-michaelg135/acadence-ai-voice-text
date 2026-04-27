import customtkinter as ctk
from utils.theme_manager import ThemeManager
from tkinter import messagebox
from tkcalendar import DateEntry
from database.db_manager import DatabaseManager

class AddTaskPopup(ctk.CTkToplevel):
    def __init__(self, master, db, subject_id, subject_name, on_success, initial_data=None):
        self.tm = ThemeManager()
        super().__init__(master, fg_color=self.tm.bg_card())
        
        self.db = db
        self.subject_id = subject_id
        self.subject_name = subject_name
        self.on_success = on_success
        self.initial_data = initial_data
        
        self.title("")
        self.geometry("800x600")
        self.attributes("-topmost", True)
        self.resizable(False, False)
        
        # Center window over root
        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() // 2) - (800 // 2)
        y = master.winfo_rooty() + (master.winfo_height() // 2) - (600 // 2)
        self.geometry(f"+{x}+{y}")
        
        self.setup_ui()
        self.grab_set() # Make modal

    def setup_ui(self):
        container = ctk.CTkFrame(self, fg_color=self.tm.bg_card(), corner_radius=15)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        ctk.CTkLabel(container, text="Add New Task", font=("Arial", 20), text_color=self.tm.text_main()).pack(pady=(15, 20))
        
        input_args = {
            "fg_color": self.tm.bg_sub(), 
            "border_width": 1, 
            "border_color": self.tm.border_main(), 
            "text_color": self.tm.text_main(),
            "corner_radius": 8,
            "height": 45
        }
        
        # Task Name
        self.name_entry = ctk.CTkEntry(container, placeholder_text="Task Name", **input_args)
        self.name_entry.pack(fill="x", padx=30, pady=(0, 15))
        
        # Subject Read-only Field
        sub_frame = ctk.CTkFrame(container, fg_color="transparent")
        sub_frame.pack(fill="x", padx=30, pady=(0, 15))
        ctk.CTkLabel(sub_frame, text="Subject", font=("Arial", 11), text_color=self.tm.text_sub()).pack(anchor="w")
        self.subject_entry = ctk.CTkEntry(sub_frame, **input_args)
        self.subject_entry.pack(fill="x")
        self.subject_entry.insert(0, self.subject_name)
        self.subject_entry.configure(state="disabled") # Make it read only
        
        # Deadline Entry (Centered and slightly shorter like in mockup)
        dead_frame = ctk.CTkFrame(container, fg_color="transparent")
        dead_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(dead_frame, text="Set Deadline", font=("Arial", 11), text_color=self.tm.text_sub()).pack(anchor="w", padx=30)
        
        # Wrapping DateEntry in a CTkFrame to perfectly simulate the custom rounded corners
        date_wrapper = ctk.CTkFrame(dead_frame, fg_color=self.tm.bg_sub(), border_width=1, border_color=self.tm.border_main(), corner_radius=8)
        date_wrapper.pack(fill="x", padx=30, pady=(5,0), ipady=2)
        
        from datetime import date
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_color = self.tm.bg_sub()[1] if is_dark else self.tm.bg_sub()[0]
        fg_color = self.tm.text_main()[1] if is_dark else self.tm.text_main()[0]
        header_bg = self.tm.bg_card()[1] if is_dark else self.tm.bg_card()[0]
        sub_fg = self.tm.text_sub()[1] if is_dark else self.tm.text_sub()[0]
        acc_bg = self.tm.accent_color()[1] if is_dark else self.tm.accent_color()[0]
        acc_hover = self.tm.accent_hover()[1] if is_dark else self.tm.accent_hover()[0]

        self.deadline_entry = DateEntry(
            date_wrapper, 
            background=acc_bg, 
            foreground='white', 
            borderwidth=0, 
            font=("Arial", 12), 
            date_pattern='yyyy-mm-dd',
            mindate=date.today(),
            headersbackground=header_bg,
            headersforeground=fg_color,
            selectbackground=acc_hover,
            selectforeground='white',
            normalbackground=bg_color,
            normalforeground=fg_color,
            weekendbackground=bg_color,
            weekendforeground=fg_color,
            othermonthforeground=sub_fg,
            othermonthbackground=bg_color,
            othermonthweforeground=sub_fg,
            othermonthwebackground=bg_color
        )
        self.deadline_entry.pack(fill="x", padx=10, pady=5)

        # Description (Taller textbox)
        self.desc_textbox = ctk.CTkTextbox(container, fg_color=self.tm.bg_sub(), border_width=1, border_color=self.tm.border_main(), 
                                           text_color=self.tm.text_main(), corner_radius=8, height=100)
        self.desc_textbox.pack(fill="x", padx=30, pady=(0, 20))
        
        # Priority Section
        ctk.CTkLabel(container, text="Priority Level (Optional)", font=("Arial", 14), text_color=self.tm.text_sub()).pack(pady=(5, 5))
        
        prio_frame = ctk.CTkFrame(container, fg_color="transparent")
        prio_frame.pack(pady=(0, 20))
        
        self.priority_var = ctk.StringVar(value="Medium")
        
        def set_priority(val):
            self.priority_var.set(val)
            update_prio_buttons()

        self.btn_low = ctk.CTkButton(prio_frame, text="« Low", width=80, height=30, corner_radius=15, command=lambda: set_priority("Low"))
        self.btn_low.pack(side="left", padx=5)
        
        self.btn_med = ctk.CTkButton(prio_frame, text="→ Medium", width=80, height=30, corner_radius=15, command=lambda: set_priority("Medium"))
        self.btn_med.pack(side="left", padx=5)
        
        self.btn_high = ctk.CTkButton(prio_frame, text="» High", width=80, height=30, corner_radius=15, command=lambda: set_priority("High"))
        self.btn_high.pack(side="left", padx=5)
        
        def update_prio_buttons():
            for btn, val in [(self.btn_low, "Low"), (self.btn_med, "Medium"), (self.btn_high, "High")]:
                if self.priority_var.get() == val:
                    btn.configure(fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover())
                else:
                    btn.configure(fg_color="transparent", text_color=self.tm.text_sub(), hover_color=self.tm.bg_sub(), border_width=0)
                    
        # Apply initial priority before running update
        if self.initial_data:
            self.name_entry.insert(0, self.initial_data.get('name', ''))
            self.desc_textbox.insert("0.0", self.initial_data.get('description', ''))
            p = self.initial_data.get('priority', 'Medium')
            if p in ['Low', 'Medium', 'High']:
                set_priority(p)
        else:
            self.desc_textbox.insert("0.0", "Description") # Placeholder
            
        update_prio_buttons()
                    
        update_prio_buttons()

        # Action Buttons
        actions_frame = ctk.CTkFrame(container, fg_color="transparent")
        actions_frame.pack(fill="x", padx=50, pady=(10, 20), side="bottom")

        # Cancel
        ctk.CTkButton(actions_frame, text="Cancel", fg_color="transparent", text_color=self.tm.text_main(),
                      border_width=1, border_color=self.tm.border_main(), corner_radius=20, width=120, height=40,
                      command=self.destroy).pack(side="left")

        # Add Task
        ctk.CTkButton(actions_frame, text="Add Task", fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), 
                      corner_radius=20, width=120, height=40, hover_color=self.tm.accent_hover(),
                      command=self.submit).pack(side="right")

    def submit(self):
        name = self.name_entry.get().strip()
        deadline = self.deadline_entry.get_date().strftime("%Y-%m-%d")
        # Textbox includes trailing newline from Tkinter, strip it
        desc = self.desc_textbox.get("1.0", "end").strip()
        if desc == "Description": # The placeholder
            desc = ""
            
        prio = self.priority_var.get()

        if not name:
            messagebox.showerror("Error", "Task Name is required.", parent=self)
            return

        self.db.add_task(self.subject_id, name, desc, deadline, priority=prio)
        self.on_success()
        self.destroy()

class EditTaskPopup(ctk.CTkToplevel):
    def __init__(self, master, db, task_data, subject_name, on_success):
        self.tm = ThemeManager()
        super().__init__(master, fg_color=self.tm.bg_card())
        
        self.db = db
        self.task_data = task_data
        self.subject_name = subject_name
        self.on_success = on_success
        
        self.title("")
        self.geometry("800x600")
        self.attributes("-topmost", True)
        self.resizable(False, False)
        
        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() // 2) - (800 // 2)
        y = master.winfo_rooty() + (master.winfo_height() // 2) - (600 // 2)
        self.geometry(f"+{x}+{y}")
        
        self.setup_ui()
        self.populate_data()
        self.grab_set()

    def setup_ui(self):
        container = ctk.CTkFrame(self, fg_color=self.tm.bg_card(), corner_radius=15)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(container, text="Edit Task", font=("Arial", 20), text_color=self.tm.text_main()).pack(pady=(15, 20))
        
        input_args = {
            "fg_color": self.tm.bg_sub(), 
            "border_width": 1, 
            "border_color": self.tm.border_main(), 
            "text_color": self.tm.text_main(),
            "corner_radius": 8, 
            "height": 45
        }
        
        self.name_entry = ctk.CTkEntry(container, placeholder_text="Task Name", **input_args)
        self.name_entry.pack(fill="x", padx=30, pady=(0, 15))
        
        sub_frame = ctk.CTkFrame(container, fg_color="transparent")
        sub_frame.pack(fill="x", padx=30, pady=(0, 15))
        ctk.CTkLabel(sub_frame, text="Subject", font=("Arial", 11), text_color=self.tm.text_sub()).pack(anchor="w")
        self.subject_entry = ctk.CTkEntry(sub_frame, **input_args)
        self.subject_entry.pack(fill="x")
        self.subject_entry.insert(0, self.subject_name)
        self.subject_entry.configure(state="disabled")
        
        dead_frame = ctk.CTkFrame(container, fg_color="transparent")
        dead_frame.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(dead_frame, text="Set Deadline", font=("Arial", 11), text_color=self.tm.text_sub()).pack(anchor="w", padx=30)
        
        date_wrapper = ctk.CTkFrame(dead_frame, fg_color=self.tm.bg_sub(), border_width=1, border_color=self.tm.border_main(), corner_radius=8)
        date_wrapper.pack(fill="x", padx=30, pady=(5,0), ipady=2)
        
        from datetime import date
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_color = self.tm.bg_sub()[1] if is_dark else self.tm.bg_sub()[0]
        fg_color = self.tm.text_main()[1] if is_dark else self.tm.text_main()[0]
        header_bg = self.tm.bg_card()[1] if is_dark else self.tm.bg_card()[0]
        sub_fg = self.tm.text_sub()[1] if is_dark else self.tm.text_sub()[0]
        acc_bg = self.tm.accent_color()[1] if is_dark else self.tm.accent_color()[0]
        acc_hover = self.tm.accent_hover()[1] if is_dark else self.tm.accent_hover()[0]

        self.deadline_entry = DateEntry(
            date_wrapper, 
            background=acc_bg, 
            foreground='white', 
            borderwidth=0, 
            font=("Arial", 12), 
            date_pattern='yyyy-mm-dd',
            headersbackground=header_bg,
            headersforeground=fg_color,
            selectbackground=acc_hover,
            selectforeground='white',
            normalbackground=bg_color,
            normalforeground=fg_color,
            weekendbackground=bg_color,
            weekendforeground=fg_color,
            othermonthforeground=sub_fg,
            othermonthbackground=bg_color,
            othermonthweforeground=sub_fg,
            othermonthwebackground=bg_color
        )
        self.deadline_entry.pack(fill="x", padx=10, pady=5)

        self.desc_textbox = ctk.CTkTextbox(container, fg_color=self.tm.bg_sub(), border_width=1, border_color=self.tm.border_main(), text_color=self.tm.text_main(), corner_radius=8, height=100)
        self.desc_textbox.pack(fill="x", padx=30, pady=(0, 20))
        
        ctk.CTkLabel(container, text="Priority Level", font=("Arial", 14), text_color=self.tm.text_sub()).pack(pady=(5, 5))
        
        prio_frame = ctk.CTkFrame(container, fg_color="transparent")
        prio_frame.pack(pady=(0, 20))
        
        self.priority_var = ctk.StringVar(value="Medium")
        
        def set_priority(val):
            self.priority_var.set(val)
            update_prio_buttons()

        self.btn_low = ctk.CTkButton(prio_frame, text="« Low", width=80, height=30, corner_radius=15, command=lambda: set_priority("Low"))
        self.btn_low.pack(side="left", padx=5)
        self.btn_med = ctk.CTkButton(prio_frame, text="→ Medium", width=80, height=30, corner_radius=15, command=lambda: set_priority("Medium"))
        self.btn_med.pack(side="left", padx=5)
        self.btn_high = ctk.CTkButton(prio_frame, text="» High", width=80, height=30, corner_radius=15, command=lambda: set_priority("High"))
        self.btn_high.pack(side="left", padx=5)
        
        def update_prio_buttons():
            for btn, val in [(self.btn_low, "Low"), (self.btn_med, "Medium"), (self.btn_high, "High")]:
                if self.priority_var.get() == val:
                    btn.configure(fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover())
                else:
                    btn.configure(fg_color="transparent", text_color=self.tm.text_sub(), hover_color=self.tm.bg_sub(), border_width=0)
                    
        self.update_prio_buttons = update_prio_buttons

        actions_frame = ctk.CTkFrame(container, fg_color="transparent")
        actions_frame.pack(fill="x", padx=50, pady=(10, 20), side="bottom")

        ctk.CTkButton(actions_frame, text="Cancel", fg_color="transparent", text_color=self.tm.text_main(), border_width=1, border_color=self.tm.border_main(), corner_radius=20, width=120, height=40, command=self.destroy).pack(side="left")
        ctk.CTkButton(actions_frame, text="Save Changes", fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), corner_radius=20, width=120, height=40, hover_color=self.tm.accent_hover(), command=self.submit).pack(side="right")

    def populate_data(self):
        self.name_entry.insert(0, self.task_data.get('name', ''))
        self.desc_textbox.insert("0.0", self.task_data.get('description', ''))
        
        deadline_str = self.task_data.get('deadline')
        if deadline_str:
            import datetime
            try:
                dt = datetime.datetime.strptime(deadline_str, "%Y-%m-%d").date()
                self.deadline_entry.set_date(dt)
            except Exception:
                pass
                
        self.priority_var.set(self.task_data.get('priority', 'Medium'))
        self.update_prio_buttons()

    def submit(self):
        name = self.name_entry.get().strip()
        deadline = self.deadline_entry.get_date().strftime("%Y-%m-%d")
        desc = self.desc_textbox.get("1.0", "end").strip()
        prio = self.priority_var.get()

        if not name:
            messagebox.showerror("Error", "Task Name is required.", parent=self)
            return

        self.db.update_task(self.task_data['id'], name, desc, deadline, prio)
        self.on_success()
        self.destroy()

class TasksView(ctk.CTkFrame):
    def __init__(self, master, user_info, show_view_callback, subject_id, subject_name, source_view="Subjects"):
        self.tm = ThemeManager()
        super().__init__(master, fg_color="transparent")
        self.user_info = user_info
        self.show_view_callback = show_view_callback
        self.db = DatabaseManager()
        
        self.subject_id = subject_id
        self.subject_name = subject_name
        self.source_view = source_view
        self.current_filter = ctk.StringVar(value="All")
        
        self.setup_ui()
        self.load_tasks()

    def setup_ui(self):
        # Header area
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Back button
        ctk.CTkButton(header_frame, text="← Back", width=60, fg_color="transparent", text_color=self.tm.text_sub(), 
                      command=lambda: self.show_view_callback(self.source_view)).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(header_frame, text=self.subject_name, font=("Arial", 24, "bold"), text_color=self.tm.text_main()).pack(side="left")
        
        # Add buttons container
        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.pack(side="right")
        
        # Text Add Button
        ctk.CTkButton(btn_frame, text="+ Add Task", width=120, fg_color=self.tm.accent_color(), text_color=self.tm.text_main(), command=self.add_task_text).pack(side="left", padx=(0, 5))
        
        # Voice Add Button
        ctk.CTkButton(btn_frame, text="Voice AI", width=100, fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover(), command=self.add_task_voice).pack(side="left")

        # Modern Filter Buttons
        self.filter_frame = ctk.CTkFrame(self, fg_color=self.tm.bg_card(), corner_radius=20, border_color=self.tm.border_main(), border_width=1)
        self.filter_frame.pack(pady=(0, 15))
        
        self.filter_buttons = {}
        for f_val in ["All", "Pending", "Completed"]:
            btn = ctk.CTkButton(
                self.filter_frame, text=f_val, width=90, height=32, corner_radius=16,
                font=("Arial", 13, "bold"),
                command=lambda v=f_val: self.set_filter(v)
            )
            btn.pack(side="left", padx=5, pady=5)
            self.filter_buttons[f_val] = btn
            
        self.update_filter_buttons()

        # Scrollable list of tasks
        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scrollable_frame.pack(fill="both", expand=True, padx=20, pady=10)

    def set_filter(self, value):
        self.current_filter.set(value)
        self.update_filter_buttons()
        self.filter_changed(value)

    def update_filter_buttons(self):
        curr = self.current_filter.get()
        for val, btn in self.filter_buttons.items():
            if val == curr:
                btn.configure(fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover())
            else:
                btn.configure(fg_color="transparent", text_color=self.tm.text_sub(), hover_color=self.tm.border_main())

    def filter_changed(self, value):
        self.load_tasks()

    def load_tasks(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        tasks = self.db.get_tasks(self.subject_id)
        
        # AC017: Sort tasks by deadline
        # Empty deadlines go to the bottom ('9999-12-31')
        tasks.sort(key=lambda x: (x.get('deadline') or '9999-12-31', x.get('created_at', '')))
        
        # Apply filter
        curr_f = self.current_filter.get()
        if curr_f == "Pending":
            tasks = [t for t in tasks if t['status'] == 'pending']
        elif curr_f == "Completed":
            tasks = [t for t in tasks if t['status'] == 'completed']

        if not tasks:
            msg = "No tasks found." if curr_f != "All" else "No tasks. Add one to get started!"
            ctk.CTkLabel(self.scrollable_frame, text=msg, text_color=self.tm.text_sub()).pack(pady=20)
            return

        for task in tasks:
            self.create_task_card(task)

    def create_task_card(self, task):
        from tkinter import messagebox
        is_done = (task['status'] == 'completed')
        bg_color = self.tm.bg_sub() if is_done else self.tm.bg_card()
        
        card = ctk.CTkFrame(self.scrollable_frame, fg_color=bg_color, border_color=self.tm.border_main(), border_width=1, corner_radius=10, height=65)
        card.pack(fill="x", pady=5)
        card.pack_propagate(False)
        
        # Task Name/Description Display
        text_color = self.tm.text_sub() if is_done else self.tm.text_main()
        display_text = task.get('name') or task.get('description', 'Unnamed Task')
        lbl = ctk.CTkLabel(card, text=display_text, font=("Arial", 16, "bold"), text_color=text_color, justify="left", width=250, anchor="w")
        lbl.pack(side="left", padx=15)
        
        # Description snippet
        desc_text = task.get('description', '')
        if len(desc_text) > 30: desc_text = desc_text[:30] + "..."
        ctk.CTkLabel(card, text=desc_text, font=("Arial", 13), text_color=self.tm.text_sub(), width=250, anchor="w").pack(side="left", padx=10)

        # Deadline Label
        deadline_str = task.get('deadline')
        if deadline_str:
            ctk.CTkLabel(card, text=f"📅 {deadline_str}", font=("Arial", 13), text_color=self.tm.accent_color(), width=100, anchor="w").pack(side="left", padx=10)
            from datetime import datetime
            today = datetime.today().strftime('%Y-%m-%d')
            if deadline_str < today and task.get('status', 'pending') == 'pending':
                ctk.CTkLabel(card, text="Overdue", font=("Arial", 10, "bold"), text_color="#FFFFFF", fg_color=self.tm.error_color(), corner_radius=6, width=60, height=20).pack(side="left", padx=(0, 10))
            else:
                ctk.CTkFrame(card, fg_color="transparent", width=60, height=20).pack(side="left", padx=(0, 10)) # Spacer to maintain alignment
        else:
            ctk.CTkLabel(card, text=f"📅 No Deadline", font=("Arial", 13), text_color=self.tm.text_sub(), width=100, anchor="w").pack(side="left", padx=10)
            ctk.CTkFrame(card, fg_color="transparent", width=60, height=20).pack(side="left", padx=(0, 10)) # Spacer

        # Priority Indicator
        prio_color = "#FF6B6B" if task['priority'] == 'High' else ("#EAB308" if task['priority'] == 'Medium' else "#22C55E")
        ctk.CTkLabel(card, text=task['priority'], font=("Arial", 13, "bold"), text_color=prio_color, width=90, anchor="w").pack(side="left", padx=15)

        # Actions
        act_frame = ctk.CTkFrame(card, fg_color="transparent")
        act_frame.pack(side="right", padx=15)
        
        def toggle_status():
            action_text = "mark this task as done" if not is_done else "unmark this task"
            if messagebox.askyesno("Confirm Action", f"Are you sure you want to {action_text}?"):
                new_status = 'pending' if is_done else 'completed'
                self.db.update_task_status(task['id'], new_status)
                self.load_tasks()

        if is_done:
            btn_text = "Unmark Task"
            btn_color = self.tm.text_sub()
            btn_text_color = "#FFFFFF"
            btn_hover = self.tm.border_main()
        else:
            btn_text = "Mark as Done"
            btn_color = self.tm.accent_color()
            btn_text_color = self.tm.accent_text()
            btn_hover = self.tm.accent_hover()

        ctk.CTkButton(act_frame, text=btn_text, font=("Arial", 11, "bold"), width=100, height=24, corner_radius=8,
                      fg_color=btn_color, text_color=btn_text_color, hover_color=btn_hover,
                      command=toggle_status).pack(side="left", padx=5)
        
        ctk.CTkButton(act_frame, text="Manage", font=("Arial", 11, "bold"), width=60, height=24, corner_radius=8,
                      fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover(),
                      command=lambda t=task: self.edit_task(t)).pack(side="left", padx=5)
                      
        ctk.CTkButton(act_frame, text="Delete", font=("Arial", 11, "bold"), width=60, height=24, corner_radius=8,
                      fg_color=self.tm.error_color(), text_color="#FFFFFF", hover_color=self.tm.error_hover(),
                      command=lambda t=task: self.delete_task(t)).pack(side="left", padx=5)

    def add_task_text(self):
        # Open detailed CustomTkinter TopLevel UI
        AddTaskPopup(self.winfo_toplevel(), self.db, self.subject_id, self.subject_name, self.load_tasks)

    def add_task_voice(self):
        from screens.voice_popup import VoiceRecordingPopup
        
        def on_transcribed(parsed_data):
            AddTaskPopup(self.winfo_toplevel(), self.db, self.subject_id, self.subject_name, self.load_tasks, initial_data=parsed_data)
            
        VoiceRecordingPopup(self.winfo_toplevel(), on_transcribed, command_type='task')

    def edit_task(self, task):
        EditTaskPopup(self.winfo_toplevel(), self.db, task, self.subject_name, self.load_tasks)

    def delete_task(self, task):
        if messagebox.askyesno("Delete", "Are you sure you want to delete this task?"):
            self.db.delete_task(task['id'])
            self.load_tasks()
