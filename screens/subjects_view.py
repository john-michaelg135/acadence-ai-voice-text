import customtkinter as ctk
from utils.theme_manager import ThemeManager
from tkinter import messagebox
from database.db_manager import DatabaseManager

class AddSubjectPopup(ctk.CTkToplevel):
    def __init__(self, master, db, user_id, on_success):
        self.tm = ThemeManager()
        super().__init__(master, fg_color=self.tm.bg_card())
        
        self.db = db
        self.user_id = user_id
        self.on_success = on_success
        
        self.title("")
        self.geometry("700x450")
        self.attributes("-topmost", True)
        self.resizable(False, False)
        
        # Center window over root
        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() // 2) - (700 // 2)
        y = master.winfo_rooty() + (master.winfo_height() // 2) - (450 // 2)
        self.geometry(f"+{x}+{y}")
        
        self.setup_ui()
        self.grab_set() # Make modal

    def setup_ui(self):
        # Container to simulate rounded white card
        container = ctk.CTkFrame(self, fg_color=self.tm.bg_card(), corner_radius=15)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        ctk.CTkLabel(container, text="Add New Subject", font=("Arial", 20), text_color=self.tm.text_main()).pack(pady=(15, 20))
        
        # Inputs Config
        input_args = {
            "fg_color": "#F4F5F7", 
            "border_width": 1, 
            "border_color": "#E5E7EB", 
            "text_color": "#1A1A1A",
            "corner_radius": 8,
            "height": 45
        }
        
        # Subject Name
        self.name_entry = ctk.CTkEntry(container, placeholder_text="Subject Name", **input_args)
        self.name_entry.pack(fill="x", padx=30, pady=(0, 15))
        
        # Subject Code
        self.code_entry = ctk.CTkEntry(container, placeholder_text="Subject Code", **input_args)
        self.code_entry.pack(fill="x", padx=30, pady=(0, 15))
        
        # Subject Description
        self.desc_entry = ctk.CTkEntry(container, placeholder_text="Subject Description", **input_args)
        self.desc_entry.pack(fill="x", padx=30, pady=(0, 20))
        
        # Category Section
        ctk.CTkLabel(container, text="Category", font=("Arial", 14), text_color=self.tm.text_sub()).pack(pady=(5, 5))
        
        # Custom Toggle for Major/Minor
        cat_frame = ctk.CTkFrame(container, fg_color="transparent")
        cat_frame.pack(pady=(0, 20))
        
        self.category_var = ctk.StringVar(value="Major")
        
        def set_category(val):
            self.category_var.set(val)
            update_buttons()

        self.btn_major = ctk.CTkButton(
            cat_frame, text="Major", width=80, height=30, corner_radius=15,
            command=lambda: set_category("Major")
        )
        self.btn_major.pack(side="left", padx=5)
        
        self.btn_minor = ctk.CTkButton(
            cat_frame, text="Minor", width=80, height=30, corner_radius=15,
            command=lambda: set_category("Minor")
        )
        self.btn_minor.pack(side="left", padx=5)
        
        def update_buttons():
            if self.category_var.get() == "Major":
                self.btn_major.configure(fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover())
                self.btn_minor.configure(fg_color="transparent", text_color=self.tm.text_main(), hover_color=self.tm.bg_sub(), border_width=0)
            else:
                self.btn_minor.configure(fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover())
                self.btn_major.configure(fg_color="transparent", text_color=self.tm.text_main(), hover_color=self.tm.bg_sub(), border_width=0)
                
        update_buttons() # init state

        # Action Buttons
        actions_frame = ctk.CTkFrame(container, fg_color="transparent")
        actions_frame.pack(fill="x", padx=50, pady=(10, 20), side="bottom")

        # Cancel
        ctk.CTkButton(
            actions_frame, text="Cancel", fg_color="transparent", text_color=self.tm.text_main(),
            border_width=1, border_color=self.tm.border_main(), corner_radius=20, width=120, height=40,
            command=self.destroy
        ).pack(side="left")

        # Add Subject
        ctk.CTkButton(
            actions_frame, text="Add Subject", fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), 
            corner_radius=20, width=120, height=40, hover_color=self.tm.accent_hover(),
            command=self.submit
        ).pack(side="right")

    def submit(self):
        name = self.name_entry.get().strip()
        code = self.code_entry.get().strip()
        desc = self.desc_entry.get().strip()
        cat = self.category_var.get()

        if not name:
            messagebox.showerror("Error", "Subject Name is required.", parent=self)
            return

        self.db.add_subject(self.user_id, name, code, desc, cat)
        self.on_success()
        self.destroy()

class EditSubjectPopup(ctk.CTkToplevel):
    def __init__(self, master, db, subject, on_success):
        self.tm = ThemeManager()
        super().__init__(master, fg_color=self.tm.bg_card())
        
        self.db = db
        self.subject = subject
        self.on_success = on_success
        
        self.title("")
        self.geometry("700x450")
        self.attributes("-topmost", True)
        self.resizable(False, False)
        
        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() // 2) - (700 // 2)
        y = master.winfo_rooty() + (master.winfo_height() // 2) - (450 // 2)
        self.geometry(f"+{x}+{y}")
        
        self.setup_ui()
        self.grab_set()

    def setup_ui(self):
        container = ctk.CTkFrame(self, fg_color=self.tm.bg_card(), corner_radius=15)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(container, text="Edit Subject", font=("Arial", 20), text_color=self.tm.text_main()).pack(pady=(15, 20))
        
        input_args = {
            "fg_color": "#F4F5F7", "border_width": 1, "border_color": "#E5E7EB", 
            "text_color": "#1A1A1A", "corner_radius": 8, "height": 45
        }
        
        self.name_entry = ctk.CTkEntry(container, placeholder_text="Subject Name", **input_args)
        self.name_entry.pack(fill="x", padx=30, pady=(0, 15))
        self.name_entry.insert(0, self.subject['name'])
        
        self.code_entry = ctk.CTkEntry(container, placeholder_text="Subject Code", **input_args)
        self.code_entry.pack(fill="x", padx=30, pady=(0, 15))
        self.code_entry.insert(0, self.subject.get('code', ''))
        
        self.desc_entry = ctk.CTkEntry(container, placeholder_text="Subject Description", **input_args)
        self.desc_entry.pack(fill="x", padx=30, pady=(0, 20))
        self.desc_entry.insert(0, self.subject.get('description', ''))
        
        ctk.CTkLabel(container, text="Category", font=("Arial", 14), text_color=self.tm.text_sub()).pack(pady=(5, 5))
        
        cat_frame = ctk.CTkFrame(container, fg_color="transparent")
        cat_frame.pack(pady=(0, 20))
        
        self.category_var = ctk.StringVar(value=self.subject.get('category', 'Major'))
        
        def set_category(val):
            self.category_var.set(val)
            update_buttons()

        self.btn_major = ctk.CTkButton(cat_frame, text="Major", width=80, height=30, corner_radius=15, command=lambda: set_category("Major"))
        self.btn_major.pack(side="left", padx=5)
        
        self.btn_minor = ctk.CTkButton(cat_frame, text="Minor", width=80, height=30, corner_radius=15, command=lambda: set_category("Minor"))
        self.btn_minor.pack(side="left", padx=5)
        
        def update_buttons():
            if self.category_var.get() == "Major":
                self.btn_major.configure(fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover())
                self.btn_minor.configure(fg_color="transparent", text_color=self.tm.text_main(), hover_color=self.tm.bg_sub(), border_width=0)
            else:
                self.btn_minor.configure(fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover())
                self.btn_major.configure(fg_color="transparent", text_color=self.tm.text_main(), hover_color=self.tm.bg_sub(), border_width=0)
                
        update_buttons() 

        actions_frame = ctk.CTkFrame(container, fg_color="transparent")
        actions_frame.pack(fill="x", padx=50, pady=(10, 20), side="bottom")

        ctk.CTkButton(actions_frame, text="Cancel", fg_color="transparent", text_color=self.tm.text_main(),
            border_width=1, border_color=self.tm.border_main(), corner_radius=20, width=120, height=40, command=self.destroy).pack(side="left")

        ctk.CTkButton(actions_frame, text="Save Changes", fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), 
            corner_radius=20, width=120, height=40, hover_color=self.tm.accent_hover(), command=self.submit).pack(side="right")

    def submit(self):
        name = self.name_entry.get().strip()
        code = self.code_entry.get().strip()
        desc = self.desc_entry.get().strip()
        cat = self.category_var.get()

        if not name:
            messagebox.showerror("Error", "Subject Name is required.", parent=self)
            return

        self.db.update_subject(self.subject['id'], name, code, desc, cat)
        self.on_success()
        self.destroy()

class SubjectsView(ctk.CTkFrame):
    def __init__(self, master, user_info, show_view_callback):
        self.tm = ThemeManager()
        super().__init__(master, fg_color="transparent")
        self.user_info = user_info
        self.show_view_callback = show_view_callback
        self.db = DatabaseManager()
        self.user_id = self.user_info['id'] if self.user_info else None
        
        self.setup_ui()
        self.load_subjects()

    def setup_ui(self):
        # Header area
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header_frame, text="Your Subjects", font=("Arial", 24, "bold"), text_color=self.tm.text_main()).pack(side="left")
        
        # Add buttons container
        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.pack(side="right")
        
        # Text Add Button
        ctk.CTkButton(btn_frame, text="+ Add Subject", width=120, fg_color=self.tm.accent_color(), text_color=self.tm.text_main(), command=self.add_subject_text).pack(side="left", padx=(0, 5))
        
        # Voice Add Button Placeholder
        ctk.CTkButton(btn_frame, text="🎤", width=40, fg_color=self.tm.accent_color(), text_color=self.tm.text_main(), command=self.add_subject_voice).pack(side="left")

        # Scrollable list of subjects
        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scrollable_frame.pack(fill="both", expand=True, padx=20, pady=10)

    def load_subjects(self):
        if not self.user_id:
            ctk.CTkLabel(self.scrollable_frame, text="Guest users cannot save subjects permanently yet.", text_color=self.tm.text_sub()).pack(pady=20)
            return

        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        subjects = self.db.get_subjects(self.user_id)
        if not subjects:
            ctk.CTkLabel(self.scrollable_frame, text="No subjects found. Add one!", text_color=self.tm.text_sub()).pack(pady=20)
            return

        grid_container = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        grid_container.pack(fill="both", expand=True)
        
        columns = 3
        for i, sub in enumerate(subjects):
            row = i // columns
            col = i % columns
            self.create_subject_card(grid_container, sub, row, col)

    def create_subject_card(self, parent, subject, row, col):
        card = ctk.CTkFrame(parent, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=1, corner_radius=15, width=280)
        card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
        parent.grid_columnconfigure(col, weight=1)

        # Category Pill & Actions
        top_frame = ctk.CTkFrame(card, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=(15, 5))
        
        category = subject.get("category", "Major")
        pill_color = "#9F8FF3" if category == "Major" else "#D1D5DB"
        # Optional: using theme accent color if preferred, but falling back to explicit colors
        
        ctk.CTkLabel(top_frame, text=category, font=("Arial", 11, "bold"), text_color=self.tm.accent_text(), fg_color=pill_color, corner_radius=8, width=50, height=24).pack(side="left")

        btn_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        btn_frame.pack(side="right")
        
        ctk.CTkButton(btn_frame, text="Manage", font=("Arial", 11, "bold"), fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover(), corner_radius=8, height=24, width=60,
                      command=lambda s=subject: self.edit_subject(s)).pack(side="left", padx=3)
                      
        ctk.CTkButton(btn_frame, text="Delete", font=("Arial", 11, "bold"), fg_color=self.tm.error_color(), text_color="#FFFFFF", hover_color=self.tm.error_hover(), corner_radius=8, height=24, width=60,
                      command=lambda s=subject: self.delete_subject(s)).pack(side="left", padx=3)

        # Subject Name
        ctk.CTkLabel(card, text=subject['name'], font=("Arial", 22, "bold"), text_color=self.tm.text_main(), anchor="w").pack(fill="x", padx=15, pady=(5, 0))
        
        # Subject Code
        code = subject.get('code')
        if code:
            ctk.CTkLabel(card, text=code, font=("Arial", 13, "bold"), text_color=self.tm.accent_color(), anchor="w").pack(fill="x", padx=15, pady=(0, 5))
        else:
            ctk.CTkFrame(card, fg_color="transparent", height=5).pack() # Spacer

        # Description
        desc = subject.get('description', '')
        if desc:
            ctk.CTkLabel(card, text=desc, font=("Arial", 13), text_color=self.tm.text_sub(), anchor="w", justify="left", wraplength=240).pack(fill="x", padx=15)

        ctk.CTkFrame(card, fg_color="transparent").pack(expand=True) # Spacer

        # View Button
        ctk.CTkButton(card, text="View Tasks", fg_color=pill_color, text_color=self.tm.accent_text(), 
                      hover_color=pill_color, font=("Arial", 14, "bold"), height=40, corner_radius=8,
                      command=lambda s=subject: self.open_subject(s)).pack(fill="x", side="bottom", padx=15, pady=15)

    def open_subject(self, subject):
        self.show_view_callback("Tasks", subject_id=subject['id'], subject_name=subject['name'], source_view="Subjects")
        
    def edit_subject(self, subject):
        EditSubjectPopup(self.winfo_toplevel(), self.db, subject, self.load_subjects)

    def add_subject_text(self):
        if not self.user_id:
            messagebox.showinfo("Guest", "You need to log in to save subjects.")
            return
            
        # Open detailed CustomTkinter TopLevel UI
        AddSubjectPopup(self.winfo_toplevel(), self.db, self.user_id, self.load_subjects)

    def add_subject_voice(self):
        if not self.user_id:
            messagebox.showinfo("Guest", "You need to log in to save subjects.")
            return
            
        import threading
        from utils.voice_manager import listen_and_transcribe
        
        def listen_thread():
            text = listen_and_transcribe()
            if text:
                # Store full text to description but only use first 3 words for name
                name_guess = " ".join(text.split()[:3])
                self.db.add_subject(self.user_id, name_guess, description=text, category='Major')
                self.after(0, self.load_subjects)
                self.after(0, lambda: messagebox.showinfo("Voice Recognized", f"Added subject: {name_guess}"))
            else:
                self.after(0, lambda: messagebox.showerror("Voice Error", "Could not recognize speech or no speech detected."))
        
        messagebox.showinfo("Voice Recording", "Click OK and start speaking your subject details...")
        threading.Thread(target=listen_thread, daemon=True).start()

    def delete_subject(self, subject):
        if messagebox.askyesno("Delete", f"Are you sure you want to delete '{subject['name']}'?"):
            self.db.delete_subject(subject['id'])
            self.load_subjects()
