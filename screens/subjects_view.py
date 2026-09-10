import customtkinter as ctk
from utils.theme_manager import ThemeManager
from tkinter import messagebox
from database.db_manager import DatabaseManager

class AddSubjectPopup(ctk.CTkToplevel):
    def __init__(self, master, db, user_id, on_success, initial_data=None):
        self.tm = ThemeManager()
        super().__init__(master, fg_color=self.tm.bg_card())
        
        self.db = db
        self.user_id = user_id
        self.on_success = on_success
        self.initial_data = initial_data
        self.submitted = False
        
        self.title("")
        self.geometry("700x600")
        self.attributes("-topmost", True)
        self.resizable(False, False)
        
        # Center window over root
        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() // 2) - (700 // 2)
        y = master.winfo_rooty() + (master.winfo_height() // 2) - (600 // 2) - 70
        self.geometry(f"+{x}+{y}")
        
        self.setup_ui()
        self.grab_set() # Make modal

    def setup_ui(self):
        # Container to simulate rounded white card
        container = ctk.CTkFrame(self, fg_color=self.tm.bg_card(), corner_radius=15)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        ctk.CTkLabel(container, text="Add New Subject", font=(self.tm.main_font(), 20), text_color=self.tm.text_main()).pack(pady=(15, 20))
        
        # Inputs Config
        input_args = {
            "fg_color": self.tm.bg_sub(), 
            "border_width": 1, 
            "border_color": self.tm.border_main(), 
            "text_color": self.tm.text_main(),
            "font": (self.tm.main_font(), 13),
            "corner_radius": 8,
            "height": 45
        }
        
        # Subject Name
        self.name_entry = ctk.CTkEntry(container, placeholder_text="Subject Name", **input_args)
        self.name_entry.pack(fill="x", padx=30, pady=(0, 4))
        
        # Char counter label
        _name_count_lbl = ctk.CTkLabel(container, text="0/32",
                                        font=(self.tm.main_font(), 10),
                                        text_color=self.tm.text_sub())
        _name_count_lbl.pack(anchor="e", padx=32, pady=(0, 11))
        
        # Validation: block special chars, cap at 32
        import re as _re
        def _val_subj_name(proposed):
            if proposed and _re.search(r"[^a-zA-Z0-9 .\-']", proposed):
                return False
            if len(proposed) > 32:
                return False
            c = len(proposed)
            _name_count_lbl.configure(
                text=f"{c}/32",
                text_color=self.tm.error_color() if c >= 28 else self.tm.text_sub()
            )
            return True
        _vcmd = (self.name_entry._entry.register(_val_subj_name), '%P')
        self.name_entry._entry.configure(validate="key", validatecommand=_vcmd)
        
        # --- Allow Subject Code: Custom ON/OFF pill toggle ---
        self.allow_code_var = ctk.BooleanVar(value=True)
        
        toggle_row = ctk.CTkFrame(container, fg_color="transparent")
        toggle_row.pack(fill="x", padx=30, pady=(0, 8))
        
        ctk.CTkLabel(toggle_row, text="Allow Subject Code",
                     font=(self.tm.main_font(), 13), text_color=self.tm.text_main()).pack(side="left")
        
        # Pill container
        pill = ctk.CTkFrame(toggle_row, fg_color=self.tm.bg_sub(),
                            corner_radius=20, border_width=1, border_color=self.tm.border_main())
        pill.pack(side="left", padx=(12, 0))
        
        self._code_btn_on = ctk.CTkButton(
            pill, text="ON", width=52, height=28, corner_radius=16,
            font=(self.tm.main_font(), 12, "bold"),
            fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(),
            hover_color=self.tm.accent_hover(),
            command=lambda: self._set_allow_code(True)
        )
        self._code_btn_on.pack(side="left", padx=3, pady=3)
        
        self._code_btn_off = ctk.CTkButton(
            pill, text="OFF", width=52, height=28, corner_radius=16,
            font=(self.tm.main_font(), 12, "bold"),
            fg_color="transparent", text_color=self.tm.text_sub(),
            hover_color=self.tm.bg_sub(),
            command=lambda: self._set_allow_code(False)
        )
        self._code_btn_off.pack(side="left", padx=3, pady=3)
        
        # Subject Code Entry
        self.code_entry = ctk.CTkEntry(container, placeholder_text="Subject Code", **input_args)
        self.code_entry.pack(fill="x", padx=30, pady=(0, 4))
        
        _code_count_lbl = ctk.CTkLabel(container, text="0/32",
                                        font=(self.tm.main_font(), 10),
                                        text_color=self.tm.text_sub())
        _code_count_lbl.pack(anchor="e", padx=32, pady=(0, 11))
        
        def _val_subj_code(proposed):
            if proposed and _re.search(r"[^a-zA-Z0-9 .\-']", proposed): return False
            if len(proposed) > 32: return False
            c = len(proposed)
            _code_count_lbl.configure(text=f"{c}/32", text_color=self.tm.error_color() if c >= 28 else self.tm.text_sub())
            return True
        self.code_entry._entry.configure(validate="key", validatecommand=(self.code_entry._entry.register(_val_subj_code), '%P'))
        
        # Subject Description
        self.desc_entry = ctk.CTkEntry(container, placeholder_text="Subject Description", **input_args)
        self.desc_entry.pack(fill="x", padx=30, pady=(0, 4))
        
        _desc_count_lbl = ctk.CTkLabel(container, text="0/250",
                                        font=(self.tm.main_font(), 10),
                                        text_color=self.tm.text_sub())
        _desc_count_lbl.pack(anchor="e", padx=32, pady=(0, 11))
        
        def _val_subj_desc(proposed):
            if proposed and _re.search(r"[^a-zA-Z0-9 .\-']", proposed): return False
            if len(proposed) > 250: return False
            c = len(proposed)
            _desc_count_lbl.configure(text=f"{c}/250", text_color=self.tm.error_color() if c >= 240 else self.tm.text_sub())
            return True
        self.desc_entry._entry.configure(validate="key", validatecommand=(self.desc_entry._entry.register(_val_subj_desc), '%P'))
        
        if self.initial_data:
            self.name_entry.insert(0, self.initial_data.get('name', ''))
            
            code_val = self.initial_data.get('code', '')
            if code_val:
                self.code_entry.insert(0, code_val)
            else:
                self._set_allow_code(False)
                
            self.desc_entry.insert(0, self.initial_data.get('description', ''))
        
        # Category Section
        ctk.CTkLabel(container, text="Category", font=(self.tm.main_font(), 14), text_color=self.tm.text_sub()).pack(pady=(5, 5))
        
        # Custom Toggle for Major/Minor/None
        cat_frame = ctk.CTkFrame(container, fg_color="transparent")
        cat_frame.pack(pady=(0, 20))
        
        self.category_var = ctk.StringVar(value="Major")
        
        def set_category(val):
            self.category_var.set(val)
            update_buttons()

        self.btn_major = ctk.CTkButton(
            cat_frame, text="Major", width=80, height=30, corner_radius=15,
            font=(self.tm.main_font(), 12), command=lambda: set_category("Major")
        )
        self.btn_major.pack(side="left", padx=5)
        
        self.btn_minor = ctk.CTkButton(
            cat_frame, text="Minor", width=80, height=30, corner_radius=15,
            font=(self.tm.main_font(), 12), command=lambda: set_category("Minor")
        )
        self.btn_minor.pack(side="left", padx=5)

        self.btn_none = ctk.CTkButton(
            cat_frame, text="None", width=80, height=30, corner_radius=15,
            font=(self.tm.main_font(), 12), command=lambda: set_category("None")
        )
        self.btn_none.pack(side="left", padx=5)
        
        def update_buttons():
            current = self.category_var.get()
            for btn, val in [(self.btn_major, "Major"), (self.btn_minor, "Minor"), (self.btn_none, "None")]:
                if current == val:
                    btn.configure(fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover(), border_width=0)
                else:
                    btn.configure(fg_color="transparent", text_color=self.tm.text_main(), hover_color=self.tm.bg_sub(), border_width=0)
                
        update_buttons() # init state
        
        if self.initial_data and 'is_major' in self.initial_data:
            if self.initial_data['is_major']:
                set_category("Major")
            else:
                set_category("Minor")

        # Action Buttons
        actions_frame = ctk.CTkFrame(container, fg_color="transparent")
        actions_frame.pack(fill="x", padx=50, pady=(10, 20), side="bottom")

        ctk.CTkButton(
            actions_frame, text="Cancel", font=(self.tm.main_font(), 14, "bold"),
            fg_color="transparent", text_color=self.tm.text_main(),
            border_width=1, border_color=self.tm.border_main(),
            corner_radius=20, width=120, height=40, command=self.destroy
        ).pack(side="left")

        ctk.CTkButton(
            actions_frame, text="Add Subject", font=(self.tm.main_font(), 14, "bold"),
            fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(),
            corner_radius=20, width=120, height=40, hover_color=self.tm.accent_hover(),
            command=self.submit
        ).pack(side="right")

    def _set_allow_code(self, enabled: bool):
        """Switches the ON/OFF pill toggle and enables/disables the code entry."""
        self.allow_code_var.set(enabled)
        if enabled:
            self._code_btn_on.configure(
                fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(),
                hover_color=self.tm.accent_hover()
            )
            self._code_btn_off.configure(
                fg_color="transparent", text_color=self.tm.text_sub(),
                hover_color=self.tm.bg_sub()
            )
            self.code_entry.configure(
                state="normal",
                fg_color=self.tm.bg_sub(),
                text_color=self.tm.text_main(),
                placeholder_text_color=self.tm.text_sub(),
                placeholder_text="Subject Code"
            )
        else:
            self._code_btn_off.configure(
                fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(),
                hover_color=self.tm.accent_hover()
            )
            self._code_btn_on.configure(
                fg_color="transparent", text_color=self.tm.text_sub(),
                hover_color=self.tm.bg_sub()
            )
            self.code_entry.delete(0, "end")
            self.code_entry.configure(
                state="disabled",
                fg_color=self.tm.bg_sub(),
                text_color=("#AAAAAA", "#666666"),
                placeholder_text="Subject Code",
                placeholder_text_color=("#999999", "#666666")
            )

    def toggle_code_entry(self):
        """Legacy compatibility wrapper."""
        self._set_allow_code(self.allow_code_var.get())

    def submit(self):
        name = self.name_entry.get().strip()
        code = self.code_entry.get().strip()
        desc = self.desc_entry.get().strip()
        cat = self.category_var.get()

        if not name:
            messagebox.showerror("Error", "Subject Name is required.", parent=self)
            return

        from utils.profanity_filter import contains_profanity
        if contains_profanity(name) or contains_profanity(desc):
            messagebox.showerror("Inappropriate Content", "Please remove offensive words before proceeding.", parent=self)
            return

        dup_error = self.db.check_subject_duplicate(self.user_id, name, code)
        if dup_error:
            messagebox.showerror("Duplicate Subject", dup_error, parent=self)
            return

        if self.submitted: return
        self.submitted = True
        
        self.db.add_subject(self.user_id, name, code, desc, cat)
        try:
            self.grab_release()
            self.withdraw()
            self.update_idletasks()
        except Exception:
            pass
        self.on_success()
        messagebox.showinfo("Success", "Subject created successfully!", parent=self.master)
        
        # Safe destruction
        try:
            self.destroy()
        except Exception:
            pass

class EditSubjectPopup(ctk.CTkToplevel):
    def __init__(self, master, db, subject, on_success):
        self.tm = ThemeManager()
        super().__init__(master, fg_color=self.tm.bg_card())
        
        self.db = db
        self.subject = subject
        self.on_success = on_success
        self.submitted = False
        
        self.title("")
        self.geometry("700x600")
        self.attributes("-topmost", True)
        self.resizable(False, False)
        
        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() // 2) - (700 // 2)
        y = master.winfo_rooty() + (master.winfo_height() // 2) - (600 // 2) - 70
        self.geometry(f"+{x}+{y}")
        
        self.setup_ui()
        self.grab_set()

    def setup_ui(self):
        container = ctk.CTkFrame(self, fg_color=self.tm.bg_card(), corner_radius=15)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(container, text="Edit Subject", font=(self.tm.main_font(), 20), text_color=self.tm.text_main()).pack(pady=(15, 20))
        
        input_args = {
            "fg_color": self.tm.bg_sub(), 
            "border_width": 1, 
            "border_color": self.tm.border_main(), 
            "text_color": self.tm.text_main(),
            "font": (self.tm.main_font(), 13),
            "corner_radius": 8, 
            "height": 45
        }
        
        self.name_entry = ctk.CTkEntry(container, placeholder_text="Subject Name", **input_args)
        self.name_entry.pack(fill="x", padx=30, pady=(0, 4))
        
        # Char counter label
        self._name_count_lbl = ctk.CTkLabel(container, text="0/32",
                                             font=(self.tm.main_font(), 10),
                                             text_color=self.tm.text_sub())
        self._name_count_lbl.pack(anchor="e", padx=32, pady=(0, 11))
        
        # Validation: block special chars, cap at 32
        import re as _re
        def _val_subj_name(proposed):
            if proposed and _re.search(r"[^a-zA-Z0-9 .\-']", proposed):
                return False
            if len(proposed) > 32:
                return False
            c = len(proposed)
            self._name_count_lbl.configure(
                text=f"{c}/32",
                text_color=self.tm.error_color() if c >= 28 else self.tm.text_sub()
            )
            return True
        _vcmd = (self.name_entry._entry.register(_val_subj_name), '%P')
        self.name_entry._entry.configure(validate="key", validatecommand=_vcmd)
        
        self.name_entry.insert(0, self.subject['name'])
        _n = len(self.subject['name'])
        self._name_count_lbl.configure(
            text=f"{_n}/32",
            text_color=self.tm.error_color() if _n >= 28 else self.tm.text_sub()
        )
        
        # --- Allow Subject Code: Custom ON/OFF pill toggle ---
        self.allow_code_var = ctk.BooleanVar(value=True)
        
        toggle_row = ctk.CTkFrame(container, fg_color="transparent")
        toggle_row.pack(fill="x", padx=30, pady=(0, 8))
        
        ctk.CTkLabel(toggle_row, text="Allow Subject Code",
                     font=(self.tm.main_font(), 13), text_color=self.tm.text_main()).pack(side="left")
        
        pill = ctk.CTkFrame(toggle_row, fg_color=self.tm.bg_sub(),
                            corner_radius=20, border_width=1, border_color=self.tm.border_main())
        pill.pack(side="left", padx=(12, 0))
        
        self._code_btn_on = ctk.CTkButton(
            pill, text="ON", width=52, height=28, corner_radius=16,
            font=(self.tm.main_font(), 12, "bold"),
            fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(),
            hover_color=self.tm.accent_hover(),
            command=lambda: self._set_allow_code(True)
        )
        self._code_btn_on.pack(side="left", padx=3, pady=3)
        
        self._code_btn_off = ctk.CTkButton(
            pill, text="OFF", width=52, height=28, corner_radius=16,
            font=(self.tm.main_font(), 12, "bold"),
            fg_color="transparent", text_color=self.tm.text_sub(),
            hover_color=self.tm.bg_sub(),
            command=lambda: self._set_allow_code(False)
        )
        self._code_btn_off.pack(side="left", padx=3, pady=3)
        
        # Subject Code Entry
        self.code_entry = ctk.CTkEntry(container, placeholder_text="Subject Code", **input_args)
        self.code_entry.pack(fill="x", padx=30, pady=(0, 4))
        
        self._code_count_lbl = ctk.CTkLabel(container, text="0/32", font=(self.tm.main_font(), 10), text_color=self.tm.text_sub())
        self._code_count_lbl.pack(anchor="e", padx=32, pady=(0, 11))
        
        def _val_subj_code(proposed):
            if proposed and _re.search(r"[^a-zA-Z0-9 .\-']", proposed): return False
            if len(proposed) > 32: return False
            c = len(proposed)
            self._code_count_lbl.configure(text=f"{c}/32", text_color=self.tm.error_color() if c >= 28 else self.tm.text_sub())
            return True
        self.code_entry._entry.configure(validate="key", validatecommand=(self.code_entry._entry.register(_val_subj_code), '%P'))
        
        code_val = self.subject.get('code', '')
        if code_val:
            self.code_entry.insert(0, code_val)
            _c = len(code_val)
            self._code_count_lbl.configure(text=f"{_c}/32", text_color=self.tm.error_color() if _c >= 28 else self.tm.text_sub())
        else:
            self._set_allow_code(False)
        
        self.desc_entry = ctk.CTkEntry(container, placeholder_text="Subject Description", **input_args)
        self.desc_entry.pack(fill="x", padx=30, pady=(0, 4))
        
        self._desc_count_lbl = ctk.CTkLabel(container, text="0/250", font=(self.tm.main_font(), 10), text_color=self.tm.text_sub())
        self._desc_count_lbl.pack(anchor="e", padx=32, pady=(0, 11))
        
        def _val_subj_desc(proposed):
            if proposed and _re.search(r"[^a-zA-Z0-9 .\-']", proposed): return False
            if len(proposed) > 250: return False
            c = len(proposed)
            self._desc_count_lbl.configure(text=f"{c}/250", text_color=self.tm.error_color() if c >= 240 else self.tm.text_sub())
            return True
        self.desc_entry._entry.configure(validate="key", validatecommand=(self.desc_entry._entry.register(_val_subj_desc), '%P'))
        
        _d = self.subject.get('description', '')
        self.desc_entry.insert(0, _d)
        _dn = len(_d)
        self._desc_count_lbl.configure(text=f"{_dn}/250", text_color=self.tm.error_color() if _dn >= 240 else self.tm.text_sub())
        
        ctk.CTkLabel(container, text="Category", font=(self.tm.main_font(), 14), text_color=self.tm.text_sub()).pack(pady=(5, 5))
        
        cat_frame = ctk.CTkFrame(container, fg_color="transparent")
        cat_frame.pack(pady=(0, 20))
        
        self.category_var = ctk.StringVar(value=self.subject.get('category', 'Major'))
        
        def set_category(val):
            self.category_var.set(val)
            update_buttons()

        self.btn_major = ctk.CTkButton(cat_frame, text="Major", width=80, height=30, corner_radius=15, font=(self.tm.main_font(), 12), command=lambda: set_category("Major"))
        self.btn_major.pack(side="left", padx=5)
        
        self.btn_minor = ctk.CTkButton(cat_frame, text="Minor", width=80, height=30, corner_radius=15, font=(self.tm.main_font(), 12), command=lambda: set_category("Minor"))
        self.btn_minor.pack(side="left", padx=5)

        self.btn_none = ctk.CTkButton(cat_frame, text="None", width=80, height=30, corner_radius=15, font=(self.tm.main_font(), 12), command=lambda: set_category("None"))
        self.btn_none.pack(side="left", padx=5)
        
        def update_buttons():
            current = self.category_var.get()
            for btn, val in [(self.btn_major, "Major"), (self.btn_minor, "Minor"), (self.btn_none, "None")]:
                if current == val:
                    btn.configure(fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover(), border_width=0)
                else:
                    btn.configure(fg_color="transparent", text_color=self.tm.text_main(), hover_color=self.tm.bg_sub(), border_width=0)
                
        update_buttons()

        actions_frame = ctk.CTkFrame(container, fg_color="transparent")
        actions_frame.pack(fill="x", padx=50, pady=(10, 20), side="bottom")

        ctk.CTkButton(
            actions_frame, text="Cancel", font=(self.tm.main_font(), 14, "bold"),
            fg_color="transparent", text_color=self.tm.text_main(),
            border_width=1, border_color=self.tm.border_main(),
            corner_radius=20, width=120, height=40, command=self.destroy
        ).pack(side="left")

        ctk.CTkButton(
            actions_frame, text="Save Changes", font=(self.tm.main_font(), 14, "bold"),
            fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(),
            corner_radius=20, width=120, height=40, hover_color=self.tm.accent_hover(),
            command=self.submit
        ).pack(side="right")

    def _set_allow_code(self, enabled: bool):
        """Switches the ON/OFF pill toggle and enables/disables the code entry."""
        self.allow_code_var.set(enabled)
        if enabled:
            self._code_btn_on.configure(
                fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(),
                hover_color=self.tm.accent_hover()
            )
            self._code_btn_off.configure(
                fg_color="transparent", text_color=self.tm.text_sub(),
                hover_color=self.tm.bg_sub()
            )
            self.code_entry.configure(
                state="normal",
                fg_color=self.tm.bg_sub(),
                text_color=self.tm.text_main(),
                placeholder_text_color=self.tm.text_sub(),
                placeholder_text="Subject Code"
            )
        else:
            self._code_btn_off.configure(
                fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(),
                hover_color=self.tm.accent_hover()
            )
            self._code_btn_on.configure(
                fg_color="transparent", text_color=self.tm.text_sub(),
                hover_color=self.tm.bg_sub()
            )
            self.code_entry.delete(0, "end")
            self.code_entry.configure(
                state="disabled",
                fg_color=self.tm.bg_sub(),
                text_color=("#AAAAAA", "#666666"),
                placeholder_text="Subject Code",
                placeholder_text_color=("#999999", "#666666")
            )

    def toggle_code_entry(self):
        """Legacy compatibility wrapper."""
        self._set_allow_code(self.allow_code_var.get())

    def submit(self):
        name = self.name_entry.get().strip()
        code = self.code_entry.get().strip()
        desc = self.desc_entry.get().strip()
        cat = self.category_var.get()

        if not name:
            messagebox.showerror("Error", "Subject Name is required.", parent=self)
            return

        from utils.profanity_filter import contains_profanity
        if contains_profanity(name) or contains_profanity(desc):
            messagebox.showerror("Inappropriate Content", "Please remove offensive words before proceeding.", parent=self)
            return

        dup_error = self.db.check_subject_duplicate(self.subject['user_id'], name, code, exclude_id=self.subject['id'])
        if dup_error:
            messagebox.showerror("Duplicate Subject", dup_error, parent=self)
            return

        if self.submitted: return
        self.submitted = True
        
        self.db.update_subject(self.subject['id'], name, code, desc, cat)
        try:
            self.grab_release()
            self.withdraw()
            self.update_idletasks()
        except Exception:
            pass
        self.on_success()
        messagebox.showinfo("Success", "Subject updated successfully!", parent=self.master)
        
        # Safe destruction
        try:
            self.destroy()
        except Exception:
            pass

class SubjectsView(ctk.CTkFrame):
    def __init__(self, master, user_info, show_view_callback):
        self.tm = ThemeManager()
        super().__init__(master, fg_color="transparent")
        self.user_info = user_info
        self.show_view_callback = show_view_callback
        self.db = DatabaseManager()
        self.user_id = self.user_info['id'] if self.user_info else None
        self._render_id = 0  # Incremented on each load to cancel stale renders
        self._last_subjects = None  # Cache list of subjects to avoid redrawing widgets if they haven't changed
        
        self.setup_ui()
        self.load_subjects()

    def setup_ui(self):
        # Header area
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header_frame, text="Your Subjects", font=(self.tm.main_font(), 24, "bold"), text_color=self.tm.text_main()).pack(side="left")
        
        # Add buttons container
        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.pack(side="right")
        
        # Text Add Button
        ctk.CTkButton(btn_frame, text="+ Add Subject", width=120, font=(self.tm.main_font(), 14, "bold"), fg_color=self.tm.accent_color(), text_color=self.tm.text_main(), command=self.add_subject_text).pack(side="left", padx=(0, 5))
        
        # Voice Add Button
        ctk.CTkButton(btn_frame, text="Voice AI", width=100, font=(self.tm.main_font(), 14, "bold"), fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover(), command=self.add_subject_voice).pack(side="left")

        # Scrollable list of subjects
        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=self.tm.bg_main(), scrollbar_button_hover_color=self.tm.text_sub())
        self.scrollable_frame.pack(fill="both", expand=True, padx=20, pady=10)

    def load_subjects(self):
        self._render_id += 1
        current_render = self._render_id

        if not self.user_id:
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            ctk.CTkLabel(self.scrollable_frame, text="Guest users cannot save subjects permanently yet.", text_color=self.tm.text_sub()).pack(pady=20)
            return

        subjects = self.db.get_subjects(self.user_id)
        
        # Check if the list of subjects has actually changed since the last load.
        # This prevents destroying and recreating dozens of complex CustomTkinter widgets 
        # when the user is simply navigating back and forth between tabs without modifying any subjects.
        if self._last_subjects is not None and self._last_subjects == subjects:
            return
        self._last_subjects = subjects

        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not subjects:
            ctk.CTkLabel(self.scrollable_frame, text="No subjects found. Add one!", font=(self.tm.main_font(), 16), text_color=self.tm.text_sub()).pack(pady=20)
            return

        grid_container = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        grid_container.pack(fill="both", expand=True)
        
        columns = 3
        # Force 3 uniform columns so cards don't expand infinitely when there are < 3 subjects
        grid_container.grid_columnconfigure((0, 1, 2), weight=1, uniform="card_col")
        
        # Render all subjects immediately to avoid pop-in animation
        for i, subject in enumerate(subjects):
            row = i // columns
            col = i % columns
            self.create_subject_card(grid_container, subject, row, col)



    def create_subject_card(self, parent, subject, row, col):
        card = ctk.CTkFrame(parent, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=2, corner_radius=15, width=280)
        card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

        # Category Pill & Actions
        top_frame = ctk.CTkFrame(card, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=(15, 5))
        
        category = subject.get("category", "Major")
        pill_color = "#9F8FF3" if category == "Major" else "#D1D5DB"
        # Optional: using theme accent color if preferred, but falling back to explicit colors
        
        ctk.CTkLabel(top_frame, text=category, font=(self.tm.main_font(), 11, "bold"), text_color=self.tm.accent_text(), fg_color=pill_color, corner_radius=8, width=50, height=24).pack(side="left")

        btn_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        btn_frame.pack(side="right")
        
        ctk.CTkButton(btn_frame, text="Manage", font=(self.tm.main_font(), 11, "bold"), fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover(), corner_radius=8, height=24, width=60,
                      command=lambda s=subject: self.edit_subject(s)).pack(side="left", padx=3)
                      
        ctk.CTkButton(btn_frame, text="Delete", font=(self.tm.main_font(), 11, "bold"), fg_color=self.tm.error_color(), text_color="#FFFFFF", hover_color=self.tm.error_hover(), corner_radius=8, height=24, width=60,
                      command=lambda s=subject: self.delete_subject(s)).pack(side="left", padx=3)

        # Subject Name
        display_name = subject['name']
        if len(display_name) > 26:
            display_name = display_name[:23] + "..."
        ctk.CTkLabel(card, text=display_name, font=(self.tm.main_font(), 22, "bold"), text_color=self.tm.text_main(), anchor="w").pack(fill="x", padx=15, pady=(5, 0))
        
        # Subject Code Container (Fixed Height)
        code_container = ctk.CTkFrame(card, fg_color="transparent", height=25)
        code_container.pack(fill="x", padx=15, pady=(0, 5))
        code_container.pack_propagate(False)
        
        code = subject.get('code')
        if code:
            ctk.CTkLabel(code_container, text=code, font=(self.tm.main_font(), 13, "bold"), text_color=self.tm.accent_color(), anchor="w").pack(fill="both", expand=True)

        # Description Container (Fixed Height)
        desc_container = ctk.CTkFrame(card, fg_color="transparent", height=65)
        desc_container.pack(fill="x", padx=15)
        desc_container.pack_propagate(False)
        
        desc = subject.get('description', '')
        if desc:
            ctk.CTkLabel(desc_container, text=desc, font=(self.tm.main_font(), 13), text_color=self.tm.text_sub(), anchor="nw", justify="left", wraplength=310).pack(fill="both", expand=True)

        banner_ctk = self._get_cached_banner(category)
        if banner_ctk:
            ctk.CTkLabel(card, text="", image=banner_ctk).pack(expand=True, pady=(20, 15))
        else:
            ctk.CTkFrame(card, fg_color="transparent").pack(expand=True) # Spacer

        # View Button
        ctk.CTkButton(card, text="View Tasks", fg_color=pill_color, text_color=self.tm.accent_text(), 
                      hover_color=pill_color, font=(self.tm.main_font(), 14, "bold"), height=40, corner_radius=8,
                      command=lambda s=subject: self.open_subject(s)).pack(fill="x", side="bottom", padx=15, pady=15)

    _global_banner_cache = {}

    def _get_cached_banner(self, category):
        if category in SubjectsView._global_banner_cache:
            return SubjectsView._global_banner_cache[category]
            
        import os
        import sys
        
        if getattr(sys, 'frozen', False):
            # If bundled via PyInstaller, assets are in _MEIPASS (which PyInstaller maps to _internal in onedir mode)
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        else:
            # If running from source, base_path is the project root (one level up from screens folder)
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        banner_file = "major_banner.png" if category == "Major" else "minor_banner.png"
        banner_path = os.path.join(base_path, "assets", banner_file)
        
        if os.path.exists(banner_path):
            try:
                from PIL import Image, ImageDraw, ImageOps
                display_size = (340, 200)
                # Render at 2x resolution for crisp display on high-DPI screens
                render_size = (display_size[0] * 2, display_size[1] * 2)
                radius = 30  # 2x radius for the 2x render
                img = Image.open(banner_path).convert("RGBA")
                img = ImageOps.fit(img, render_size, Image.Resampling.LANCZOS)
                
                mask = Image.new('L', render_size, 0)
                draw = ImageDraw.Draw(mask)
                draw.rounded_rectangle((0, 0) + render_size, radius=radius, fill=255)
                output = Image.new('RGBA', render_size, (0, 0, 0, 0))
                output.paste(img, (0, 0), mask=mask)
                
                banner_ctk = ctk.CTkImage(light_image=output, dark_image=output, size=display_size)
                SubjectsView._global_banner_cache[category] = banner_ctk
                return banner_ctk
            except Exception as e:
                print("Error loading banner:", e)
                
        SubjectsView._global_banner_cache[category] = None
        return None

    def open_subject(self, subject):
        self.show_view_callback("Tasks", subject_id=subject['id'], subject_name=subject['name'], source_view="Subjects")
        
    def edit_subject(self, subject):
        EditSubjectPopup(self.winfo_toplevel(), self.db, subject, self.load_subjects)

    def _check_subject_limit(self):
        subjects = self.db.get_subjects(self.user_id)
        if len(subjects) >= 12:
            messagebox.showwarning("Limit Reached", "You can only add up to 12 subjects max.\nPlease delete an existing subject to add a new one.")
            return False
        return True

    def add_subject_text(self):
        if not self.user_id:
            messagebox.showinfo("Guest", "You need to log in to save subjects.")
            return
            
        if not self._check_subject_limit():
            return

        # Open detailed CustomTkinter TopLevel UI
        AddSubjectPopup(self.winfo_toplevel(), self.db, self.user_id, self.load_subjects)

    def add_subject_voice(self):
        if not self.user_id:
            messagebox.showinfo("Guest", "You need to log in to save subjects.")
            return
            
        if not self._check_subject_limit():
            return

        from screens.voice_popup import VoiceRecordingPopup
        
        def on_transcribed(parsed_data):
            AddSubjectPopup(self.winfo_toplevel(), self.db, self.user_id, self.load_subjects, initial_data=parsed_data)
            
        VoiceRecordingPopup(self.winfo_toplevel(), on_transcribed, command_type='subject')

    def delete_subject(self, subject):
        if messagebox.askyesno("Delete", f"Are you sure you want to delete '{subject['name']}'?", parent=self.winfo_toplevel()):
            self.db.delete_subject(subject['id'])
            self.load_subjects()
            messagebox.showinfo("Success", "Subject deleted successfully!", parent=self.winfo_toplevel())

    def refresh(self):
        """Called by DashboardScreen when the cached view is shown to refresh data."""
        self.load_subjects()
