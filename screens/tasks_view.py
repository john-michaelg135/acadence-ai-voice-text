import customtkinter as ctk
from tkinter import messagebox
from database.db_manager import DatabaseManager

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
        ctk.CTkButton(btn_frame, text="+ Add Task", width=80, fg_color="#B5B0D3", text_color="#1A1A1A", command=self.add_task_text).pack(side="left", padx=(0, 5))
        
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

        # Task Description
        text_color = "#AAAAAA" if is_done else "#1A1A1A"
        lbl = ctk.CTkLabel(card, text=task['description'], font=("Arial", 16), text_color=text_color, wraplength=200, justify="left")
        lbl.pack(side="left", padx=5)

        # Priority Indicator
        prio_color = "#FF6B6B" if task['priority'] == 'high' else "#F0F0F0"
        prio_text = "!" if task['priority'] == 'high' else ""
        if prio_text:
            ctk.CTkLabel(card, text=prio_text, font=("Arial", 16, "bold"), text_color=prio_color).pack(side="left", padx=5)

        # Actions
        ctk.CTkButton(card, text="🗑️", width=40, fg_color="transparent", text_color="#FF6B6B", hover_color="#FFE0E0",
                      command=lambda t=task: self.delete_task(t)).pack(side="right", padx=15)

    def add_task_text(self):
        dialog = ctk.CTkInputDialog(text="Enter new task description:", title="Add Task")
        desc = dialog.get_input()
        if desc and desc.strip():
            # For simplicity, defaults to normal priority.
            # In a full app, we might ask for priority as well.
            self.db.add_task(self.subject_id, desc.strip(), priority='normal')
            self.load_tasks()

    def add_task_voice(self):
        import threading
        from utils.voice_manager import listen_and_transcribe
        
        def listen_thread():
            text = listen_and_transcribe()
            if text:
                self.db.add_task(self.subject_id, text, priority='normal')
                self.after(0, self.load_tasks)
                self.after(0, lambda: messagebox.showinfo("Voice Recognized", f"Added task: {text}"))
            else:
                self.after(0, lambda: messagebox.showerror("Voice Error", "Could not recognize speech or no speech detected."))
                
        messagebox.showinfo("Voice Recording", "Click OK and start speaking your task description...")
        threading.Thread(target=listen_thread, daemon=True).start()

    def delete_task(self, task):
        if messagebox.askyesno("Delete", "Are you sure you want to delete this task?"):
            self.db.delete_task(task['id'])
            self.load_tasks()
