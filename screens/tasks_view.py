import customtkinter as ctk
from utils.theme_manager import ThemeManager
from tkinter import messagebox, ttk
from tkcalendar import DateEntry

# Patch DateEntry to prevent disappearing when clicking arrows
_orig_focus_out = getattr(DateEntry, '_on_focus_out_cal', None)
if _orig_focus_out:
    def _safe_focus_out(self, event):
        if getattr(self, '_top_cal', None) and self._top_cal.winfo_ismapped():
            x, y = self._top_cal.winfo_pointerxy()
            xc = self._top_cal.winfo_rootx()
            yc = self._top_cal.winfo_rooty()
            w = self._top_cal.winfo_width()
            h = self._top_cal.winfo_height()
            if xc <= x <= xc + w and yc <= y <= yc + h:
                self._calendar.focus_force()
                return
        if self.focus_get() is None:
            return
        _orig_focus_out(self, event)
    DateEntry._on_focus_out_cal = _safe_focus_out
from database.db_manager import DatabaseManager
from datetime import datetime, date


class AIProgressPopup(ctk.CTkToplevel):
    """
    A non-blocking floating progress popup shown during AI Aid generation.
    Displays a modern animated progress bar, stage label, and auto-dismisses.
    """
    _W = 340
    _H = 110

    def __init__(self, master, task_name):
        self.tm = ThemeManager()
        super().__init__(master)
        
        # Windows transparent corners hack
        transparent_color = '#000001'
        self.configure(fg_color=transparent_color)
        try:
            self.attributes("-transparentcolor", transparent_color)
        except Exception:
            pass

        self._done = False
        self._anim_id = None
        self._task_name = task_name

        self.title("")
        self.geometry(f"{self._W}x{self._H}")
        self.resizable(False, False)
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        # Dragging variables
        self._drag_data = {"x": 0, "y": 0}
        
        # Position logic: Load from config, or fallback to bottom-right of screen
        try:
            self.update_idletasks()
            import os
            import json
            import sys
            if getattr(sys, 'frozen', False):
                self._pos_file = os.path.join(os.path.dirname(sys.executable), 'database', 'ai_popup_pos.json')
            else:
                self._pos_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database', 'ai_popup_pos.json')
                
            if os.path.exists(self._pos_file):
                with open(self._pos_file, 'r') as f:
                    pos = json.load(f)
                    self.geometry(f"+{pos['x']}+{pos['y']}")
            else:
                sw = master.winfo_screenwidth()
                sh = master.winfo_screenheight()
                x = sw - self._W - 40   # 40px from right edge of screen
                y = sh - self._H - 80   # 80px from bottom edge (avoids taskbar)
                self.geometry(f"+{x}+{y}")
        except Exception:
            pass

        self._build_ui()
        self._animate_shimmer()

    def _build_ui(self):
        # bg_color must match transparent_color so the corners blend into the transparency
        outer = ctk.CTkFrame(self, fg_color=self.tm.bg_card(), corner_radius=10,
                             border_width=1, border_color=self.tm.accent_color(),
                             bg_color='#000001')
        outer.pack(fill="both", expand=True, padx=2, pady=2)

        # Header: icon + title
        hdr = ctk.CTkFrame(outer, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(10, 3))
        ctk.CTkLabel(hdr, text="✦ AI Aid Generating",
                     font=(self.tm.main_font(), 12, "bold"),
                     text_color=self.tm.accent_color()).pack(side="left")

        # Task name (truncated)
        short_name = self._task_name[:40] + "…" if len(self._task_name) > 40 else self._task_name
        ctk.CTkLabel(outer, text=short_name,
                     font=(self.tm.main_font(), 10),
                     text_color=self.tm.text_sub()).pack(anchor="w", padx=14, pady=(0, 6))

        # Thin progress bar (height=7)
        bar_bg = ctk.CTkFrame(outer, fg_color=self.tm.bg_sub(), corner_radius=4, height=7)
        bar_bg.pack(fill="x", padx=14, pady=(0, 5))
        bar_bg.pack_propagate(False)

        self._bar_fill = ctk.CTkFrame(bar_bg, fg_color=self.tm.accent_color(),
                                      corner_radius=4, height=7)
        self._bar_fill.place(relx=0, rely=0, relwidth=0.05, relheight=1.0)

        # Stage status label
        self._stage_lbl = ctk.CTkLabel(outer, text="Initializing…",
                                       font=(self.tm.main_font(), 10),
                                       text_color=self.tm.text_sub())
        self._stage_lbl.pack(anchor="w", padx=14, pady=(0, 8))

        # Bind drag events to outer frame and its children
        for widget in [outer, hdr, self._stage_lbl, bar_bg]:
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._do_drag)
            widget.bind("<ButtonRelease-1>", self._end_drag)

    def update_progress(self, percent: int, message: str):
        """Called from the main thread via master.after(). Updates bar and label."""
        if self._done or not self.winfo_exists():
            return
        try:
            rel = max(0.03, min(1.0, percent / 100))
            self._bar_fill.place_configure(relwidth=rel)
            self._stage_lbl.configure(text=message)
        except Exception:
            pass

    def finish(self):
        """Called after generation completes. Shows 100% briefly then destroys."""
        if self._done:
            return
        self._done = True
        try:
            if self._anim_id:
                self.after_cancel(self._anim_id)
            self._bar_fill.place_configure(relwidth=1.0)
            self._stage_lbl.configure(text="Done! AI Aid is ready.")
        except Exception:
            pass
        self.after(1200, self._safe_destroy)

    def _safe_destroy(self):
        try:
            if self.winfo_exists():
                self.destroy()
        except Exception:
            pass

    def _animate_shimmer(self):
        """Pulse the fill between accent and accent_hover to show activity."""
        if self._done or not self.winfo_exists():
            return
        try:
            import math
            self._shimmer_pos = (getattr(self, '_shimmer_pos', 0.0) + 0.07) % 1.0
            t = (math.sin(self._shimmer_pos * 2 * math.pi) + 1) / 2
            color = self.tm.accent_color() if t > 0.5 else self.tm.accent_hover()
            self._bar_fill.configure(fg_color=color)
        except Exception:
            pass
        self._anim_id = self.after(120, self._animate_shimmer)

    def _start_drag(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _do_drag(self, event):
        x = self.winfo_x() - self._drag_data["x"] + event.x
        y = self.winfo_y() - self._drag_data["y"] + event.y
        self.geometry(f"+{x}+{y}")

    def _end_drag(self, event):
        # Save new position
        try:
            import json
            import os
            os.makedirs(os.path.dirname(self._pos_file), exist_ok=True)
            with open(self._pos_file, 'w') as f:
                json.dump({"x": self.winfo_x(), "y": self.winfo_y()}, f)
        except Exception:
            pass


class AddTaskPopup(ctk.CTkToplevel):

    def __init__(self, master, db, subject_id, subject_name, on_success, initial_data=None):
        self.tm = ThemeManager()
        super().__init__(master, fg_color=self.tm.bg_card())
        
        self.db = db
        self.subject_id = subject_id
        self.subject_name = subject_name
        self.on_success = on_success
        self.initial_data = initial_data
        self.submitted = False
        
        self.title("")
        self.geometry("800x650")
        self.attributes("-topmost", True)
        self.resizable(False, False)
        
        # Safe initialization for tkcalendar on some platforms/python versions
        try:
            style = ttk.Style()
            style.theme_use('clam')
        except:
            pass

        # Center window over root
        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() // 2) - (800 // 2)
        y = master.winfo_rooty() + (master.winfo_height() // 2) - (650 // 2) - 50
        self.geometry(f"+{x}+{y}")
        
        self.setup_ui()
        self.grab_set() # Make modal

    def setup_ui(self):
        container = ctk.CTkFrame(self, fg_color=self.tm.bg_card(), corner_radius=15)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        ctk.CTkLabel(container, text="Add New Task", font=(self.tm.main_font(), 20), text_color=self.tm.text_main()).pack(pady=(15, 20))
        
        input_args = {
            "fg_color": self.tm.bg_sub(), 
            "border_width": 1, 
            "border_color": self.tm.border_main(), 
            "text_color": self.tm.text_main(),
            "font": (self.tm.main_font(), 13),
            "corner_radius": 8,
            "height": 45
        }
        
        # Task Name
        self.name_entry = ctk.CTkEntry(container, placeholder_text="Task Name", **input_args)
        self.name_entry.pack(fill="x", padx=30, pady=(0, 15))
        
        # Subject Read-only Field
        sub_frame = ctk.CTkFrame(container, fg_color="transparent")
        sub_frame.pack(fill="x", padx=30, pady=(0, 15))
        ctk.CTkLabel(sub_frame, text="Subject", font=(self.tm.main_font(), 11), text_color=self.tm.text_sub()).pack(anchor="w")
        self.subject_entry = ctk.CTkEntry(sub_frame, **input_args)
        self.subject_entry.pack(fill="x")
        self.subject_entry.insert(0, self.subject_name)
        self.subject_entry.configure(state="disabled") # Make it read only
        
        # Deadline Entry (Centered and slightly shorter like in mockup)
        dead_frame = ctk.CTkFrame(container, fg_color="transparent")
        dead_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(dead_frame, text="Set Deadline & Time", font=(self.tm.main_font(), 11), text_color=self.tm.text_sub()).pack(anchor="w", padx=30)
        
        picker_frame = ctk.CTkFrame(dead_frame, fg_color="transparent")
        picker_frame.pack(fill="x", padx=30, pady=(5,0))
        
        # Wrapping DateEntry in a CTkFrame to perfectly simulate the custom rounded corners
        date_wrapper = ctk.CTkFrame(picker_frame, fg_color=self.tm.bg_sub(), border_width=1, border_color=self.tm.border_main(), corner_radius=8)
        date_wrapper.pack(side="left", fill="x", expand=True, ipady=2, padx=(0, 10))
        
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
            font=(self.tm.main_font(), 12), 
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
        
        # Patch for tkcalendar bug where _downarrow_name might be missing in some themes/environments
        if not hasattr(self.deadline_entry, '_downarrow_name'):
            setattr(self.deadline_entry, '_downarrow_name', 'downarrow')

        # Time picker components
        time_wrapper = ctk.CTkFrame(picker_frame, fg_color="transparent")
        time_wrapper.pack(side="right")
        
        self.hour_var = ctk.StringVar(value="12")
        self.min_var = ctk.StringVar(value="00")
        self.ampm_var = ctk.StringVar(value="PM")
        
        hours = [f"{i:02d}" for i in range(1, 13)]
        mins = ["00", "15", "30", "45"]
        
        ctk.CTkOptionMenu(time_wrapper, variable=self.hour_var, values=hours, width=60, font=(self.tm.main_font(), 12), fg_color=self.tm.bg_sub(), button_color=self.tm.border_main(), text_color=self.tm.text_main()).pack(side="left", padx=2)
        ctk.CTkLabel(time_wrapper, text=":", font=(self.tm.main_font(), 14, "bold"), text_color=self.tm.text_main()).pack(side="left")
        ctk.CTkOptionMenu(time_wrapper, variable=self.min_var, values=mins, width=60, font=(self.tm.main_font(), 12), fg_color=self.tm.bg_sub(), button_color=self.tm.border_main(), text_color=self.tm.text_main()).pack(side="left", padx=2)
        ctk.CTkOptionMenu(time_wrapper, variable=self.ampm_var, values=["AM", "PM"], width=65, font=(self.tm.main_font(), 12), fg_color=self.tm.bg_sub(), button_color=self.tm.border_main(), text_color=self.tm.text_main()).pack(side="left", padx=2)

        # Description (Taller textbox)
        desc_frame = ctk.CTkFrame(container, fg_color="transparent")
        desc_frame.pack(fill="x", padx=30, pady=(0, 20))
        ctk.CTkLabel(desc_frame, text="Description", font=(self.tm.main_font(), 11), text_color=self.tm.text_sub()).pack(anchor="w")
        self.desc_textbox = ctk.CTkTextbox(desc_frame, fg_color=self.tm.bg_sub(), border_width=1, border_color=self.tm.border_main(), 
                                           text_color=self.tm.text_main(), font=(self.tm.main_font(), 13), corner_radius=8, height=100)
        self.desc_textbox.pack(fill="x", pady=(5, 0))
        
        # Priority Section
        ctk.CTkLabel(container, text="Priority Level", font=(self.tm.main_font(), 14), text_color=self.tm.text_sub()).pack(pady=(5, 5))
        
        prio_frame = ctk.CTkFrame(container, fg_color="transparent")
        prio_frame.pack(pady=(0, 20))
        
        self.priority_var = ctk.StringVar(value="Medium")
        
        def set_priority(val):
            self.priority_var.set(val)
            update_prio_buttons()

        self.btn_low = ctk.CTkButton(prio_frame, text="« Low", width=80, height=30, corner_radius=15, font=(self.tm.main_font(), 12), command=lambda: set_priority("Low"))
        self.btn_low.pack(side="left", padx=5)
        
        self.btn_med = ctk.CTkButton(prio_frame, text="→ Medium", width=80, height=30, corner_radius=15, font=(self.tm.main_font(), 12), command=lambda: set_priority("Medium"))
        self.btn_med.pack(side="left", padx=5)
        
        self.btn_high = ctk.CTkButton(prio_frame, text="» High", width=80, height=30, corner_radius=15, font=(self.tm.main_font(), 12), command=lambda: set_priority("High"))
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
        
        update_prio_buttons()

        # Action Buttons
        actions_frame = ctk.CTkFrame(container, fg_color="transparent")
        actions_frame.pack(fill="x", padx=50, pady=(10, 20), side="bottom")

        # Cancel
        ctk.CTkButton(actions_frame, text="Cancel", font=(self.tm.main_font(), 14, "bold"), fg_color="transparent", text_color=self.tm.text_main(),
                      border_width=1, border_color=self.tm.border_main(), corner_radius=20, width=120, height=40,
                      command=self.close).pack(side="left")

        # Add Task
        ctk.CTkButton(actions_frame, text="Add Task", font=(self.tm.main_font(), 14, "bold"), fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), 
                      corner_radius=20, width=120, height=40, hover_color=self.tm.accent_hover(),
                      command=self.submit).pack(side="right")

    def close(self):
        (self.master if hasattr(self, 'master') and self.master else self).after(50, self.destroy)

    def submit(self):
        name = self.name_entry.get().strip()
        date_str = self.deadline_entry.get_date().strftime("%Y-%m-%d")
        
        h = int(self.hour_var.get())
        m = self.min_var.get()
        ampm = self.ampm_var.get()
        if ampm == "PM" and h < 12: h += 12
        if ampm == "AM" and h == 12: h = 0
        deadline = f"{date_str} {h:02d}:{m}"
        
        desc = self.desc_textbox.get("1.0", "end").strip()
            
        prio = self.priority_var.get()

        if not name:
            messagebox.showerror("Error", "Task Name is required.", parent=self)
            return

        from utils.profanity_filter import contains_profanity
        if contains_profanity(name) or contains_profanity(desc):
            messagebox.showerror("Inappropriate Content", "Please remove offensive words before proceeding.", parent=self)
            return

        if self.submitted: return
        self.submitted = True
        
        task_id = self.db.add_task(self.subject_id, name, desc, deadline, priority=prio)
        self.on_success()
        self.withdraw()
        self.update_idletasks()
        messagebox.showinfo("Success", "Task created successfully!", parent=self.master)
        
        # Safe destruction before launching background generation
        self.grab_release()
        self.update_idletasks()
        master_ref = self.master
        (master_ref if hasattr(self, 'master') and master_ref else self).after(50, self.destroy)

        # Async AI Generation with progress bar
        import threading
        import re as _re
        from utils.ai_parser import _check_online, is_research_task, generate_research_references, generate_task_tips
        import os
        import sys

        def start_generation():
            if not _check_online():
                return
            progress_popup = AIProgressPopup(master_ref, name)

            def progress_callback(stage, percent, message):
                print(f"[AI Aid] [{percent:3d}%] {message}")
                if master_ref and master_ref.winfo_exists():
                    master_ref.after(0, lambda p=percent, m=message: progress_popup.update_progress(p, m))

            def generate():
                is_research = is_research_task(name, desc)
                content = generate_research_references(name, desc, progress_callback) if is_research else generate_task_tips(name, desc, progress_callback)
                if content:
                    if getattr(sys, 'frozen', False):
                        base_dir = os.path.join(os.path.dirname(sys.executable), 'database', 'attachments')
                    else:
                        base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database', 'attachments')
                    os.makedirs(base_dir, exist_ok=True)
                    # Use sanitized task name as filename
                    safe_name = _re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')[:60]
                    file_path = os.path.join(base_dir, f"{task_id}_{safe_name}_AI_Aid.txt")
                    try:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(content)
                        def apply_update():
                            try:
                                self.db.update_task_attachment(task_id, file_path)
                                self.on_success()
                                from utils.notification_manager import NotificationManager
                                NotificationManager.send("AI Aid Ready", f"The AI Aid for '{name}' has been generated successfully.")
                            except Exception:
                                pass
                        if master_ref and master_ref.winfo_exists():
                            master_ref.after(0, apply_update)
                    except Exception:
                        pass
                if master_ref and master_ref.winfo_exists():
                    master_ref.after(500, progress_popup.finish)

            threading.Thread(target=generate, daemon=True).start()

        if master_ref and master_ref.winfo_exists():
            master_ref.after(150, start_generation)

class EditTaskPopup(ctk.CTkToplevel):
    def __init__(self, master, db, task_data, subject_name, on_success):
        self.tm = ThemeManager()
        super().__init__(master, fg_color=self.tm.bg_card())
        
        self.db = db
        self.task_data = task_data
        self.subject_name = subject_name
        self.on_success = on_success
        self.submitted = False
        
        self.title("")
        self.geometry("800x650")
        self.attributes("-topmost", True)
        self.resizable(False, False)
        
        # Safe initialization for tkcalendar
        try:
            style = ttk.Style()
            style.theme_use('clam')
        except:
            pass

        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() // 2) - (800 // 2)
        y = master.winfo_rooty() + (master.winfo_height() // 2) - (650 // 2) - 50
        self.geometry(f"+{x}+{y}")
        
        self.setup_ui()
        self.populate_data()
        self.grab_set()

    def setup_ui(self):
        container = ctk.CTkFrame(self, fg_color=self.tm.bg_card(), corner_radius=15)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(container, text="Edit Task", font=(self.tm.main_font(), 20), text_color=self.tm.text_main()).pack(pady=(15, 20))
        
        input_args = {
            "fg_color": self.tm.bg_sub(), 
            "border_width": 1, 
            "border_color": self.tm.border_main(), 
            "text_color": self.tm.text_main(),
            "font": (self.tm.main_font(), 13),
            "corner_radius": 8, 
            "height": 45
        }
        
        self.name_entry = ctk.CTkEntry(container, placeholder_text="Task Name", **input_args)
        self.name_entry.pack(fill="x", padx=30, pady=(0, 15))
        
        sub_frame = ctk.CTkFrame(container, fg_color="transparent")
        sub_frame.pack(fill="x", padx=30, pady=(0, 15))
        ctk.CTkLabel(sub_frame, text="Subject", font=(self.tm.main_font(), 11), text_color=self.tm.text_sub()).pack(anchor="w")
        self.subject_entry = ctk.CTkEntry(sub_frame, **input_args)
        self.subject_entry.pack(fill="x")
        self.subject_entry.insert(0, self.subject_name)
        self.subject_entry.configure(state="disabled")
        
        dead_frame = ctk.CTkFrame(container, fg_color="transparent")
        dead_frame.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(dead_frame, text="Set Deadline & Time", font=(self.tm.main_font(), 11), text_color=self.tm.text_sub()).pack(anchor="w", padx=30)
        
        picker_frame = ctk.CTkFrame(dead_frame, fg_color="transparent")
        picker_frame.pack(fill="x", padx=30, pady=(5,0))
        
        date_wrapper = ctk.CTkFrame(picker_frame, fg_color=self.tm.bg_sub(), border_width=1, border_color=self.tm.border_main(), corner_radius=8)
        date_wrapper.pack(side="left", fill="x", expand=True, ipady=2, padx=(0, 10))
        
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
            font=(self.tm.main_font(), 12), 
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
        
        # Patch for tkcalendar bug
        if not hasattr(self.deadline_entry, '_downarrow_name'):
            setattr(self.deadline_entry, '_downarrow_name', 'downarrow')

        time_wrapper = ctk.CTkFrame(picker_frame, fg_color="transparent")
        time_wrapper.pack(side="right")
        
        self.hour_var = ctk.StringVar(value="12")
        self.min_var = ctk.StringVar(value="00")
        self.ampm_var = ctk.StringVar(value="PM")
        
        hours = [f"{i:02d}" for i in range(1, 13)]
        mins = ["00", "15", "30", "45", "59"]
        
        ctk.CTkOptionMenu(time_wrapper, variable=self.hour_var, values=hours, width=60, font=(self.tm.main_font(), 12), fg_color=self.tm.bg_sub(), button_color=self.tm.border_main(), text_color=self.tm.text_main()).pack(side="left", padx=2)
        ctk.CTkLabel(time_wrapper, text=":", font=(self.tm.main_font(), 14, "bold"), text_color=self.tm.text_main()).pack(side="left")
        ctk.CTkOptionMenu(time_wrapper, variable=self.min_var, values=mins, width=60, font=(self.tm.main_font(), 12), fg_color=self.tm.bg_sub(), button_color=self.tm.border_main(), text_color=self.tm.text_main()).pack(side="left", padx=2)
        ctk.CTkOptionMenu(time_wrapper, variable=self.ampm_var, values=["AM", "PM"], width=65, font=(self.tm.main_font(), 12), fg_color=self.tm.bg_sub(), button_color=self.tm.border_main(), text_color=self.tm.text_main()).pack(side="left", padx=2)

        desc_frame = ctk.CTkFrame(container, fg_color="transparent")
        desc_frame.pack(fill="x", padx=30, pady=(0, 20))
        ctk.CTkLabel(desc_frame, text="Description", font=(self.tm.main_font(), 11), text_color=self.tm.text_sub()).pack(anchor="w")
        self.desc_textbox = ctk.CTkTextbox(desc_frame, fg_color=self.tm.bg_sub(), border_width=1, border_color=self.tm.border_main(), text_color=self.tm.text_main(), font=(self.tm.main_font(), 13), corner_radius=8, height=100)
        self.desc_textbox.pack(fill="x", pady=(5, 0))
        
        ctk.CTkLabel(container, text="Priority Level", font=(self.tm.main_font(), 14), text_color=self.tm.text_sub()).pack(pady=(5, 5))
        
        prio_frame = ctk.CTkFrame(container, fg_color="transparent")
        prio_frame.pack(pady=(0, 20))
        
        self.priority_var = ctk.StringVar(value="Medium")
        
        def set_priority(val):
            self.priority_var.set(val)
            update_prio_buttons()

        self.btn_low = ctk.CTkButton(prio_frame, text="« Low", width=80, height=30, corner_radius=15, font=(self.tm.main_font(), 12), command=lambda: set_priority("Low"))
        self.btn_low.pack(side="left", padx=5)
        self.btn_med = ctk.CTkButton(prio_frame, text="→ Medium", width=80, height=30, corner_radius=15, font=(self.tm.main_font(), 12), command=lambda: set_priority("Medium"))
        self.btn_med.pack(side="left", padx=5)
        self.btn_high = ctk.CTkButton(prio_frame, text="» High", width=80, height=30, corner_radius=15, font=(self.tm.main_font(), 12), command=lambda: set_priority("High"))
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

        ctk.CTkButton(actions_frame, text="Cancel", font=(self.tm.main_font(), 14, "bold"), fg_color="transparent", text_color=self.tm.text_main(), border_width=1, border_color=self.tm.border_main(), corner_radius=20, width=120, height=40, command=self.close).pack(side="left")
        ctk.CTkButton(actions_frame, text="Save Changes", font=(self.tm.main_font(), 14, "bold"), fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), corner_radius=20, width=120, height=40, hover_color=self.tm.accent_hover(), command=self.submit).pack(side="right")

    def populate_data(self):
        self.name_entry.insert(0, self.task_data.get('name', ''))
        self.desc_textbox.insert("0.0", self.task_data.get('description', ''))
        
        deadline_str = self.task_data.get('deadline')
        if deadline_str:
            import datetime
            try:
                # Format could be YYYY-MM-DD HH:MM or just YYYY-MM-DD
                parts = deadline_str.split(" ")
                dt = datetime.datetime.strptime(parts[0], "%Y-%m-%d").date()
                self.deadline_entry.set_date(dt)
                
                if len(parts) > 1:
                    time_parts = parts[1].split(":")
                    if len(time_parts) >= 2:
                        h = int(time_parts[0])
                        m = time_parts[1]
                        ampm = "AM"
                        if h >= 12:
                            ampm = "PM"
                            if h > 12: h -= 12
                        if h == 0: h = 12
                        self.hour_var.set(f"{h:02d}")
                        self.min_var.set(m)
                        self.ampm_var.set(ampm)
            except Exception as e:
                pass
                
        self.priority_var.set(self.task_data.get('priority', 'Medium'))
        self.update_prio_buttons()

    def close(self):
        (self.master if hasattr(self, 'master') and self.master else self).after(50, self.destroy)

    def submit(self):
        name = self.name_entry.get().strip()
        date_str = self.deadline_entry.get_date().strftime("%Y-%m-%d")
        
        h = int(self.hour_var.get())
        m = self.min_var.get()
        ampm = self.ampm_var.get()
        if ampm == "PM" and h < 12: h += 12
        if ampm == "AM" and h == 12: h = 0
        deadline = f"{date_str} {h:02d}:{m}"
        
        desc = self.desc_textbox.get("1.0", "end").strip()
        prio = self.priority_var.get()

        if not name:
            messagebox.showerror("Error", "Task Name is required.", parent=self)
            return

        from utils.profanity_filter import contains_profanity
        if contains_profanity(name) or contains_profanity(desc):
            messagebox.showerror("Inappropriate Content", "Please remove offensive words before proceeding.", parent=self)
            return

        if self.submitted: return
        self.submitted = True
        
        self.db.update_task(self.task_data['id'], name, desc, deadline, prio)

        from utils.ai_parser import _check_online
        will_regenerate = False
        if _check_online():
            if messagebox.askyesno("Regenerate AI Aid", "Would you like to regenerate the AI Aid based on your edits?", parent=self):
                will_regenerate = True
                old_attachment = self.task_data.get('attachment_path')
                if old_attachment:
                    import os as _os
                    try:
                        if _os.path.exists(old_attachment):
                            _os.remove(old_attachment)
                        self.db.update_task_attachment(self.task_data['id'], None)
                        self.task_data['attachment_path'] = None
                    except Exception:
                        pass

        if not will_regenerate:
            self.on_success()
            self.withdraw()
            self.update_idletasks()
            messagebox.showinfo("Success", "Task updated successfully!", parent=self.master)

        # Safe destruction
        self.grab_release()
        self.update_idletasks()
        master_ref = self.master
        task_id = self.task_data['id']
        (master_ref if hasattr(self, 'master') and master_ref else self).after(50, self.destroy)

        if will_regenerate:
            import threading
            import re as _re
            from utils.ai_parser import is_research_task, generate_research_references, generate_task_tips
            import os
            import sys

            def start_regeneration():
                progress_popup = AIProgressPopup(master_ref, name)

                def progress_callback(stage, percent, message):
                    print(f"[AI Aid] [{percent:3d}%] {message}")
                    if master_ref and master_ref.winfo_exists():
                        master_ref.after(0, lambda p=percent, m=message: progress_popup.update_progress(p, m))

                def generate():
                    is_research = is_research_task(name, desc)
                    content = generate_research_references(name, desc, progress_callback) if is_research else generate_task_tips(name, desc, progress_callback)
                    if content:
                        if getattr(sys, 'frozen', False):
                            base_dir = os.path.join(os.path.dirname(sys.executable), 'database', 'attachments')
                        else:
                            base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database', 'attachments')
                        os.makedirs(base_dir, exist_ok=True)
                        safe_name = _re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')[:60]
                        file_path = os.path.join(base_dir, f"{task_id}_{safe_name}_AI_Aid.txt")
                        try:
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(content)
                            def apply_update():
                                try:
                                    self.db.update_task_attachment(task_id, file_path)
                                    self.on_success()
                                    from utils.notification_manager import NotificationManager
                                    NotificationManager.send("AI Aid Ready", f"The new AI Aid for '{name}' is ready.")
                                except Exception:
                                    pass
                            if master_ref and master_ref.winfo_exists():
                                master_ref.after(0, apply_update)
                        except Exception:
                            pass
                    if master_ref and master_ref.winfo_exists():
                        master_ref.after(500, progress_popup.finish)

                threading.Thread(target=generate, daemon=True).start()

            if master_ref and master_ref.winfo_exists():
                master_ref.after(150, start_regeneration)

class TaskDetailsPopup(ctk.CTkToplevel):
    def __init__(self, master, task_data, db_manager, fetch_callback, subject_name=""):
        super().__init__(master)
        self.tm = ThemeManager()
        self.task_data = task_data
        self.db = db_manager
        self.fetch_callback = fetch_callback
        self.subject_name = subject_name
        
        self.title("Task Details")
        self.geometry("500x550")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        # Center on master
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() - 500) // 2
        y = master.winfo_y() + (master.winfo_height() - 550) // 2
        self.geometry(f"+{x}+{y}")
        
        self.setup_ui()

    def setup_ui(self):
        self.configure(fg_color=self.tm.bg_main())
        
        container = ctk.CTkFrame(self, fg_color=self.tm.bg_card(), corner_radius=15, border_width=1, border_color=self.tm.border_main())
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header, text="Task Details", font=(self.tm.main_font(), 22, "bold"), text_color=self.tm.text_main()).pack(side="left")
        
        # Priority pill
        prio = self.task_data.get('priority', 'Medium')
        prio_color = "#FF6B6B" if prio == 'High' else ("#EAB308" if prio == 'Medium' else "#22C55E")
        ctk.CTkLabel(header, text=prio, font=(self.tm.main_font(), 12, "bold"), text_color=prio_color).pack(side="right")
        
        # Content
        content = ctk.CTkScrollableFrame(container, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # Name
        name = self.task_data.get('name') or self.task_data.get('description', 'Unnamed Task')
        name_lbl = ctk.CTkLabel(content, text=name, font=(self.tm.main_font(), 18, "bold"), text_color=self.tm.text_main(), justify="left", wraplength=400)
        name_lbl.pack(anchor="w", pady=(0, 10))
        
        # Info grid (Status, Deadline, Subject)
        info_frame = ctk.CTkFrame(content, fg_color=self.tm.bg_sub(), corner_radius=10)
        info_frame.pack(fill="x", pady=(0, 15))
        
        status = "Completed" if self.task_data.get('status') == 'completed' else "Pending"
        status_color = self.tm.accent_color() if status == "Completed" else self.tm.text_sub()
        self.add_info_row(info_frame, "Status:", status, val_color=status_color)
        
        deadline = self.task_data.get('deadline')
        if not deadline: deadline = "No Deadline"
        self.add_info_row(info_frame, "Deadline:", deadline)
        
        if self.subject_name:
            self.add_info_row(info_frame, "Subject:", self.subject_name)
            
        created = self.task_data.get('created_at', 'Unknown')
        self.add_info_row(info_frame, "Created:", created)
        
        # Description
        desc_lbl = ctk.CTkLabel(content, text="Description", font=(self.tm.main_font(), 14, "bold"), text_color=self.tm.text_sub())
        desc_lbl.pack(anchor="w", pady=(10, 5))
        
        desc = self.task_data.get('description', 'No description provided.')
        desc_box = ctk.CTkTextbox(content, font=(self.tm.main_font(), 14), text_color=self.tm.text_main(), fg_color=self.tm.bg_sub(), wrap="word", height=150)
        desc_box.pack(fill="x", pady=(0, 10))
        desc_box.insert("0.0", desc)
        desc_box.configure(state="disabled") # read-only
        
        # AI Attachment Section
        attachment_path = self.task_data.get('attachment_path')
        if attachment_path:
            import os
            import sys
            # Dynamic path resolution in case the application folder was moved or is running as a built executable
            if not os.path.exists(attachment_path):
                filename = os.path.basename(attachment_path)
                if getattr(sys, 'frozen', False):
                    base_dir = os.path.join(os.path.dirname(sys.executable), 'database', 'attachments')
                else:
                    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database', 'attachments')
                fallback_path = os.path.join(base_dir, filename)
                if os.path.exists(fallback_path):
                    attachment_path = fallback_path
                    
            if os.path.exists(attachment_path):
                att_lbl = ctk.CTkLabel(content, text="AI Aid", font=(self.tm.main_font(), 14, "bold"), text_color=self.tm.text_sub())
                att_lbl.pack(anchor="w", pady=(10, 5))
                
                att_frame = ctk.CTkFrame(content, fg_color=self.tm.bg_sub(), corner_radius=8, border_color=self.tm.accent_color(), border_width=1)
                att_frame.pack(fill="x", pady=(0, 10))
                
                ctk.CTkLabel(att_frame, text="\U0001f4ce AI Generated Reference", font=(self.tm.main_font(), 13, "bold"), text_color=self.tm.text_main()).pack(side="left", padx=15, pady=10)
                
                def view_attachment():
                    """Open a scrollable read-only viewer popup for the AI Aid file."""
                    viewer = ctk.CTkToplevel(self)
                    viewer.title("Viewer")
                    viewer.geometry("720x600")
                    viewer.resizable(True, True)
                    viewer.transient(self)
                    viewer.grab_set()
                    viewer.configure(fg_color=self.tm.bg_main())
                    viewer.update_idletasks()
                    sw = viewer.winfo_screenwidth()
                    sh = viewer.winfo_screenheight()
                    vx = (sw - 720) // 2 + 200   # offset right so it doesn't cover the task popup
                    vy = (sh - 600) // 2
                    viewer.geometry(f"+{vx}+{vy}")

                    # Header
                    hdr = ctk.CTkFrame(viewer, fg_color="transparent")
                    hdr.pack(fill="x", padx=20, pady=(15, 5))
                    task_name_raw = self.task_data.get('name') or self.task_data.get('description', 'AI Aid')
                    ctk.CTkLabel(hdr, text=f"AI Aid \u2014 {task_name_raw}", font=(self.tm.main_font(), 16, "bold"), text_color=self.tm.text_main()).pack(side="left")

                    # Text content
                    try:
                        with open(attachment_path, "r", encoding="utf-8") as f:
                            file_content = f.read()
                    except Exception as e:
                        file_content = f"Error reading file: {e}"
                    
                    text_box = ctk.CTkTextbox(viewer, font=(self.tm.main_font(), 13), text_color=self.tm.text_main(),
                                              fg_color=self.tm.bg_card(), corner_radius=10, wrap="word")
                    text_box.pack(fill="both", expand=True, padx=20, pady=(5, 10))
                    text_box.insert("0.0", file_content)
                    text_box.configure(state="disabled")

                    # Close button
                    ctk.CTkButton(viewer, text="Close", font=(self.tm.main_font(), 13, "bold"),
                                  fg_color="transparent", text_color=self.tm.text_main(),
                                  border_width=1, border_color=self.tm.border_main(),
                                  corner_radius=20, width=100, height=34,
                                  command=viewer.destroy).pack(pady=(0, 15))

                def download_attachment():
                    from tkinter import filedialog
                    import shutil
                    import re as _re
                    task_name_raw = self.task_data.get('name') or self.task_data.get('description', 'AI_Aid')
                    safe_name = _re.sub(r'[^\w\s-]', '', task_name_raw).strip().replace(' ', '_')[:60]
                    save_path = filedialog.asksaveasfilename(
                        defaultextension=".txt",
                        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
                        initialfile=f"{safe_name}_AI_Aid.txt",
                        title="Save AI Aid",
                        parent=self
                    )
                    if save_path:
                        try:
                            shutil.copy2(attachment_path, save_path)
                            messagebox.showinfo("Success", "AI Aid saved successfully!", parent=self)
                        except Exception as e:
                            messagebox.showerror("Error", f"Failed to save: {e}", parent=self)
                
                btn_frame = ctk.CTkFrame(att_frame, fg_color="transparent")
                btn_frame.pack(side="right", padx=10, pady=10)
                
                ctk.CTkButton(btn_frame, text="View", font=(self.tm.main_font(), 12, "bold"), fg_color="transparent",
                              text_color=self.tm.accent_color(), border_width=1, border_color=self.tm.accent_color(),
                              hover_color=self.tm.bg_sub(), width=65, height=28, corner_radius=14,
                              command=view_attachment).pack(side="left", padx=(0, 5))
                
                ctk.CTkButton(btn_frame, text="Download", font=(self.tm.main_font(), 12, "bold"), fg_color=self.tm.accent_color(), 
                              text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover(), width=80, height=28, corner_radius=14,
                              command=download_attachment).pack(side="left")
        
        # Actions
        actions_frame = ctk.CTkFrame(container, fg_color="transparent")
        actions_frame.pack(fill="x", padx=20, pady=20, side="bottom")
        
        if self.task_data.get('status') == 'completed':
            # Center Close button for completed tasks
            ctk.CTkButton(actions_frame, text="Close", font=(self.tm.main_font(), 14, "bold"), fg_color="transparent", text_color=self.tm.text_main(), border_width=1, border_color=self.tm.border_main(), corner_radius=20, width=150, height=40, command=self.close).pack(expand=True)
        else:
            ctk.CTkButton(actions_frame, text="Close", font=(self.tm.main_font(), 14, "bold"), fg_color="transparent", text_color=self.tm.text_main(), border_width=1, border_color=self.tm.border_main(), corner_radius=20, width=100, height=40, command=self.close).pack(side="left")
            
            def open_edit():
                (self.master if hasattr(self, 'master') and self.master else self).after(50, self.destroy)
                EditTaskPopup(self.master, self.db, self.task_data, self.subject_name, self.fetch_callback)
                
            ctk.CTkButton(actions_frame, text="Manage Task", font=(self.tm.main_font(), 14, "bold"), fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), corner_radius=20, width=120, height=40, hover_color=self.tm.accent_hover(), command=open_edit).pack(side="right")

    def close(self):
        (self.master if hasattr(self, 'master') and self.master else self).after(50, self.destroy)

    def add_info_row(self, parent, label, value, val_color=None):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(row, text=label, font=(self.tm.main_font(), 13), text_color=self.tm.text_sub(), width=80, anchor="w").pack(side="left")
        v_color = val_color if val_color else self.tm.text_main()
        ctk.CTkLabel(row, text=value, font=(self.tm.main_font(), 13, "bold"), text_color=v_color, anchor="w").pack(side="left", padx=(10, 0))

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
        self._raw_tasks = []  # Cache — avoids redundant DB queries on filter changes
        self._render_id = 0   # Incremented on each load to cancel stale renders
        
        self.setup_ui()
        self._fetch_and_render()

    def setup_ui(self):
        # Header area
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Back button
        ctk.CTkButton(header_frame, text="← Back", font=(self.tm.main_font(), 14), width=60, fg_color="transparent", text_color=self.tm.text_sub(), 
                      command=lambda: self.show_view_callback(self.source_view)).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(header_frame, text=self.subject_name, font=(self.tm.main_font(), 24, "bold"), text_color=self.tm.text_main()).pack(side="left")
        
        # Add buttons container
        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.pack(side="right")
        
        # Text Add Button
        ctk.CTkButton(btn_frame, text="+ Add Task", width=120, font=(self.tm.main_font(), 14, "bold"), fg_color=self.tm.accent_color(), text_color=self.tm.text_main(), command=self.add_task_text).pack(side="left", padx=(0, 5))
        
        # Voice Add Button
        ctk.CTkButton(btn_frame, text="Voice AI Beta", width=100, font=(self.tm.main_font(), 14, "bold"), fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover(), command=self.add_task_voice).pack(side="left")

        # Modern Filter Buttons
        self.filter_frame = ctk.CTkFrame(self, fg_color=self.tm.bg_card(), corner_radius=20, border_color=self.tm.border_main(), border_width=1)
        self.filter_frame.pack(pady=(0, 15))
        
        self.filter_buttons = {}
        for f_val in ["All", "Pending", "Completed"]:
            btn = ctk.CTkButton(
                self.filter_frame, text=f_val, width=90, height=32, corner_radius=16,
                font=(self.tm.main_font(), 13, "bold"),
                command=lambda v=f_val: self.set_filter(v)
            )
            btn.pack(side="left", padx=5, pady=5)
            self.filter_buttons[f_val] = btn
        
        self.update_filter_buttons()

        # Scrollable list of tasks
        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=self.tm.bg_main(), scrollbar_button_hover_color=self.tm.text_sub())
        self.scrollable_frame.pack(fill="both", expand=True, padx=20, pady=10)

    def set_filter(self, value):
        self.current_filter.set(value)
        self.update_filter_buttons()
        self.filter_changed(value)

    def update_filter_buttons(self):
        """Instant color swap — all buttons update in same frame, no flicker."""
        curr = self.current_filter.get()
        for val, btn in self.filter_buttons.items():
            if val == curr:
                btn.configure(fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover())
            else:
                btn.configure(fg_color="transparent", text_color=self.tm.text_sub(), hover_color=self.tm.border_main())

    def filter_changed(self, value):
        self.load_tasks()

    def _fetch_and_render(self):
        """Fetches fresh task data from DB, then re-renders. Call after any data mutation."""
        self._raw_tasks = self.db.get_tasks(self.subject_id)
        # AC017: Sort tasks by deadline — empty deadlines go to the bottom
        self._raw_tasks.sort(key=lambda x: (x.get('deadline') or '9999-12-31', x.get('created_at', '')))
        self.load_tasks()

    def load_tasks(self):
        """Re-renders task list from cache using chunked rendering for performance."""
        self._render_id += 1
        current_render = self._render_id

        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        tasks = list(self._raw_tasks)

        # Apply filter in-memory (no DB query needed)
        curr_f = self.current_filter.get()
        if curr_f == "Pending":
            tasks = [t for t in tasks if t['status'] == 'pending']
        elif curr_f == "Completed":
            tasks = [t for t in tasks if t['status'] == 'completed']

        if not tasks:
            msg = "No tasks found." if curr_f != "All" else "No tasks. Add one to get started!"
            ctk.CTkLabel(self.scrollable_frame, text=msg, font=(self.tm.main_font(), 16), text_color=self.tm.text_sub()).pack(pady=20)
            return

        # Use full datetime for precise time-based overdue checks
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        self._render_task_chunk(tasks, 0, now_str, current_render)

    def _render_task_chunk(self, tasks, index, now_str, render_id, chunk_size=15):
        """Renders tasks in chunks to prevent UI freezing."""
        if render_id != self._render_id:
            return  # A newer render was started; abort this one
        if not self.winfo_exists():
            return  # Widget was destroyed (user navigated away)

        end = min(index + chunk_size, len(tasks))
        for i in range(index, end):
            self.create_task_card(tasks[i], now_str)

        if end < len(tasks):
            self.after(10, lambda: self._render_task_chunk(tasks, end, now_str, render_id, chunk_size))

    def create_task_card(self, task, now_str):
        is_done = (task['status'] == 'completed')
        bg_color = self.tm.bg_sub() if is_done else self.tm.bg_card()
        
        card = ctk.CTkFrame(self.scrollable_frame, fg_color=bg_color, border_color=self.tm.border_main(), border_width=2, corner_radius=10, height=65)
        card.pack(fill="x", pady=5)
        card.pack_propagate(False)

        # --- Pack action buttons FIRST (side="right") to anchor them ---
        # This guarantees buttons are always visible regardless of name length.
        act_frame = ctk.CTkFrame(card, fg_color="transparent")
        act_frame.pack(side="right", padx=15)
        
        def toggle_status():
            action_text = "mark this task as done" if not is_done else "unmark this task"
            if messagebox.askyesno("Confirm Action", f"Are you sure you want to {action_text}?", parent=self.winfo_toplevel()):
                new_status = 'completed' if task['status'] == 'pending' else 'pending'
                self.db.update_task_status(task['id'], new_status)
                self._fetch_and_render()
                messagebox.showinfo("Success", f"Task marked as {new_status}!", parent=self.winfo_toplevel())

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

        ctk.CTkButton(act_frame, text=btn_text, font=(self.tm.main_font(), 11, "bold"), width=100, height=24, corner_radius=8,
                      fg_color=btn_color, text_color=btn_text_color, hover_color=btn_hover,
                      command=toggle_status).pack(side="left", padx=5)
        
        ctk.CTkButton(act_frame, text="Manage", font=(self.tm.main_font(), 11, "bold"), width=60, height=24, corner_radius=8,
                      fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover(),
                      command=lambda t=task: self.edit_task(t)).pack(side="left", padx=5)
                      
        ctk.CTkButton(act_frame, text="Delete", font=(self.tm.main_font(), 11, "bold"), width=60, height=24, corner_radius=8,
                      fg_color=self.tm.error_color(), text_color="#FFFFFF", hover_color=self.tm.error_hover(),
                      command=lambda t=task: self.delete_task(t)).pack(side="left", padx=5)

        # --- Priority Indicator (packed right, before left content) ---
        prio_color = "#FF6B6B" if task['priority'] == 'High' else ("#EAB308" if task['priority'] == 'Medium' else "#22C55E")
        ctk.CTkLabel(card, text=task['priority'], font=(self.tm.main_font(), 13, "bold"), text_color=prio_color, width=70, anchor="w").pack(side="right", padx=(0, 5))

        # --- Left-side content (fills remaining space) ---
        # Task Name — truncated so it never overflows into the buttons
        text_color = self.tm.text_sub() if is_done else self.tm.text_main()
        display_text = task.get('name') or task.get('description', 'Unnamed Task')
        if len(display_text) > 38:
            display_text = display_text[:35] + "..."
        name_lbl = ctk.CTkLabel(card, text=display_text, font=(self.tm.main_font(), 16, "bold"), text_color=text_color, justify="left", anchor="w", width=300)
        name_lbl.pack(side="left", padx=(20, 30))
        
        # Deadline Label
        deadline_lbl = None
        overdue_lbl = None
        deadline_str = task.get('deadline')
        if deadline_str:
            deadline_lbl = ctk.CTkLabel(card, text=f"📅 {deadline_str}", font=(self.tm.main_font(), 13), text_color=self.tm.accent_color(), width=100, anchor="w", cursor="hand2")
            deadline_lbl.pack(side="left", padx=10)
            
            # If deadline is date-only, assume it's due at end of day (23:59) for overdue calculation
            compare_deadline = deadline_str if len(deadline_str) > 10 else deadline_str + " 23:59"
            
            if compare_deadline < now_str and task.get('status', 'pending') == 'pending':
                overdue_lbl = ctk.CTkLabel(card, text="Overdue", font=(self.tm.main_font(), 10, "bold"), text_color="#FFFFFF", fg_color=self.tm.error_color(), corner_radius=6, width=60, height=20, cursor="hand2")
                overdue_lbl.pack(side="left", padx=(0, 5))
        else:
            deadline_lbl = ctk.CTkLabel(card, text="📅 No Deadline", font=(self.tm.main_font(), 13), text_color=self.tm.text_sub(), width=100, anchor="w", cursor="hand2")
            deadline_lbl.pack(side="left", padx=10)

        # Make card clickable to open TaskDetailsPopup
        card.configure(cursor="hand2")
        name_lbl.configure(cursor="hand2")
        
        def on_card_click(event):
            TaskDetailsPopup(self.winfo_toplevel(), task, self.db, self._fetch_and_render, self.subject_name)
            
        card.bind("<Button-1>", on_card_click)
        name_lbl.bind("<Button-1>", on_card_click)
        if deadline_lbl: deadline_lbl.bind("<Button-1>", on_card_click)
        if overdue_lbl: overdue_lbl.bind("<Button-1>", on_card_click)
        # also bind the spacer space if they click inside the card but not on text
        for child in card.winfo_children():
            if isinstance(child, ctk.CTkFrame) and child != act_frame:
                child.configure(cursor="hand2")
                child.bind("<Button-1>", on_card_click)

    def add_task_text(self):
        # Open detailed CustomTkinter TopLevel UI
        AddTaskPopup(self.winfo_toplevel(), self.db, self.subject_id, self.subject_name, self._fetch_and_render)

    def add_task_voice(self):
        from screens.voice_popup import VoiceRecordingPopup
        
        def on_transcribed(parsed_data):
            AddTaskPopup(self.winfo_toplevel(), self.db, self.subject_id, self.subject_name, self._fetch_and_render, initial_data=parsed_data)
            
        VoiceRecordingPopup(self.winfo_toplevel(), on_transcribed, command_type='task')

    def edit_task(self, task):
        EditTaskPopup(self.winfo_toplevel(), self.db, task, self.subject_name, self._fetch_and_render)

    def delete_task(self, task):
        if messagebox.askyesno("Delete", "Are you sure you want to delete this task?", parent=self.winfo_toplevel()):
            self.db.delete_task(task['id'])
            self._fetch_and_render()
            messagebox.showinfo("Success", "Task deleted successfully!", parent=self.winfo_toplevel())
