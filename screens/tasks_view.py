import customtkinter as ctk
from tkinter import messagebox
from database.db_manager import DatabaseManager

class AddTaskPopup(ctk.CTkToplevel):
    def __init__(self, master, db, subject_id, subject_name, on_success):
        super().__init__(master, fg_color="#FFFFFF")
        
        self.db = db
        self.subject_id = subject_id
        self.subject_name = subject_name
        self.on_success = on_success
        
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
        container = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=15)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        ctk.CTkLabel(container, text="Add New Task", font=("Arial", 20), text_color="#1A1A1A").pack(pady=(15, 20))
        
        input_args = {
            "fg_color": "#F4F5F7", 
            "border_width": 1, 
            "border_color": "#E5E7EB", 
            "text_color": "#1A1A1A",
            "corner_radius": 8,
            "height": 45
        }
        
        # Task Name
        self.name_entry = ctk.CTkEntry(container, placeholder_text="Task Name", **input_args)
        self.name_entry.pack(fill="x", padx=30, pady=(0, 15))
        
        # Subject Read-only Field
        sub_frame = ctk.CTkFrame(container, fg_color="transparent")
        sub_frame.pack(fill="x", padx=30, pady=(0, 15))
        ctk.CTkLabel(sub_frame, text="Subject", font=("Arial", 11), text_color="#666666").pack(anchor="w")
        self.subject_entry = ctk.CTkEntry(sub_frame, **input_args)
        self.subject_entry.pack(fill="x")
        self.subject_entry.insert(0, self.subject_name)
        self.subject_entry.configure(state="disabled") # Make it read only
        
        # Deadline Entry (Centered and slightly shorter like in mockup)
        dead_frame = ctk.CTkFrame(container, fg_color="transparent")
        dead_frame.pack(fill="x", pady=(0, 15))
        self.deadline_entry = ctk.CTkEntry(dead_frame, placeholder_text="Set Deadline", width=250, **input_args)
        self.deadline_entry.pack()

        # Description (Taller textbox)
        self.desc_textbox = ctk.CTkTextbox(container, fg_color="#F4F5F7", border_width=1, border_color="#E5E7EB", 
                                           text_color="#1A1A1A", corner_radius=8, height=100)
        self.desc_textbox.pack(fill="x", padx=30, pady=(0, 20))
        self.desc_textbox.insert("0.0", "Description") # Placeholder
        
        # Priority Section
        ctk.CTkLabel(container, text="Priority Level (Optional)", font=("Arial", 14), text_color="#666666").pack(pady=(5, 5))
        
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
                    btn.configure(fg_color="#9F8FF3", text_color="white", hover_color="#897AE0")
                else:
                    btn.configure(fg_color="transparent", text_color="#666666", hover_color="#F0F0F0", border_width=0)
                    
        update_prio_buttons()

        # Action Buttons
        actions_frame = ctk.CTkFrame(container, fg_color="transparent")
        actions_frame.pack(fill="x", padx=50, pady=(10, 20), side="bottom")

        # Cancel
        ctk.CTkButton(actions_frame, text="Cancel", fg_color="transparent", text_color="#1A1A1A",
                      border_width=1, border_color="#E5E7EB", corner_radius=20, width=120, height=40,
                      command=self.destroy).pack(side="left")

        # Add Task
        ctk.CTkButton(actions_frame, text="Add Task", fg_color="#9F8FF3", text_color="white", 
                      corner_radius=20, width=120, height=40, hover_color="#897AE0",
                      command=self.submit).pack(side="right")

    def submit(self):
        name = self.name_entry.get().strip()
        deadline = self.deadline_entry.get().strip()
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

class TasksView(ctk.CTkFrame):
    def __init__(self, master, user_info, show_view_callback, subject_id, subject_name):
        super().__init__(master, fg_color="transparent")
        self.user_info = user_info
        self.show_view_callback = show_view_callback
        self.subject_id = subject_id
        self.subject_name = subject_name
        self.db = DatabaseManager()
        
        self.setup_ui()
        self.load_tasks()

    def setup_ui(self):
        # Header area
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Back button
        ctk.CTkButton(header_frame, text="← Back", width=60, fg_color="transparent", text_color="#666666", 
                      command=lambda: self.show_view_callback("Subjects")).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(header_frame, text=self.subject_name, font=("Arial", 24, "bold"), text_color="#1A1A1A").pack(side="left")
        
        # Add buttons container
        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.pack(side="right")
        
        # Text Add Button
        ctk.CTkButton(btn_frame, text="+ Add Task", width=120, fg_color="#B5B0D3", text_color="#1A1A1A", command=self.add_task_text).pack(side="left", padx=(0, 5))
        
        # Voice Add Button Placeholder
        ctk.CTkButton(btn_frame, text="🎤", width=40, fg_color="#B5B0D3", text_color="#1A1A1A", command=self.add_task_voice).pack(side="left")

        # Scrollable list of tasks
        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scrollable_frame.pack(fill="both", expand=True, padx=20, pady=10)

    def load_tasks(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        tasks = self.db.get_tasks(self.subject_id)
        if not tasks:
            ctk.CTkLabel(self.scrollable_frame, text="No tasks. Add one to get started!", text_color="#666666").pack(pady=20)
            return

        for task in tasks:
            self.create_task_card(task)

    def create_task_card(self, task):
        card = ctk.CTkFrame(self.scrollable_frame, fg_color="#FFFFFF", border_color="#E0E0E0", border_width=1, corner_radius=10, height=80)
        card.pack(fill="x", pady=5)
        card.pack_propagate(False)

        # Status Checkbox
        is_done = (task['status'] == 'completed')
        checkbox_var = ctk.StringVar(value="on" if is_done else "off")
        
        def toggle_status():
            new_status = 'completed' if checkbox_var.get() == "on" else 'pending'
            self.db.update_task_status(task['id'], new_status)
            lbl.configure(text_color="#AAAAAA" if new_status == 'completed' else "#1A1A1A")

        cb = ctk.CTkCheckBox(card, text="", variable=checkbox_var, onvalue="on", offvalue="off", command=toggle_status, width=30)
        cb.pack(side="left", padx=(15, 5))

        # Task Name/Description Display
        text_color = "#AAAAAA" if is_done else "#1A1A1A"
        # Since older tasks might not have a name if they were created before schema update, default to description
        display_text = task.get('name') or task.get('description', 'Unnamed Task')
        lbl = ctk.CTkLabel(card, text=display_text, font=("Arial", 16), text_color=text_color, wraplength=200, justify="left")
        lbl.pack(side="left", padx=5)

        # Priority Indicator
        prio_color = "#FF6B6B" if task['priority'] == 'High' else ("#EAB308" if task['priority'] == 'Medium' else "#F0F0F0")
        prio_text = "!" if task['priority'] == 'High' else ("" if task['priority'] == 'Medium' else "v")
        if prio_text:
            ctk.CTkLabel(card, text=prio_text, font=("Arial", 16, "bold"), text_color=prio_color).pack(side="left", padx=5)

        # Actions
        ctk.CTkButton(card, text="🗑️", width=40, fg_color="transparent", text_color="#FF6B6B", hover_color="#FFE0E0",
                      command=lambda t=task: self.delete_task(t)).pack(side="right", padx=15)

    def add_task_text(self):
        # Open detailed CustomTkinter TopLevel UI
        AddTaskPopup(self.winfo_toplevel(), self.db, self.subject_id, self.subject_name, self.load_tasks)

    def add_task_voice(self):
        import threading
        from utils.voice_manager import listen_and_transcribe
        
        def listen_thread():
            text = listen_and_transcribe()
            if text:
                # Store full text as description, guess first 3 words for name
                name_guess = " ".join(text.split()[:3])
                self.db.add_task(self.subject_id, name_guess, description=text, priority='Medium')
                self.after(0, self.load_tasks)
                self.after(0, lambda: messagebox.showinfo("Voice Recognized", f"Added task: {name_guess}"))
            else:
                self.after(0, lambda: messagebox.showerror("Voice Error", "Could not recognize speech or no speech detected."))
                
        messagebox.showinfo("Voice Recording", "Click OK and start speaking your task details...")
        threading.Thread(target=listen_thread, daemon=True).start()

    def delete_task(self, task):
        if messagebox.askyesno("Delete", "Are you sure you want to delete this task?"):
            self.db.delete_task(task['id'])
            self.load_tasks()
