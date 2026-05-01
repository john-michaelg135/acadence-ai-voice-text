import customtkinter as ctk
from utils.theme_manager import ThemeManager

class WalkthroughPopup(ctk.CTkToplevel):
    def __init__(self, master, on_complete):
        super().__init__(master)
        self.tm = ThemeManager()
        self.on_complete = on_complete
        
        self.title("Welcome to Acadence!")
        self.geometry("600x480")
        self.resizable(False, False)
        
        # Make modal
        self.transient(master)
        self.grab_set()
        
        # Center the window
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() // 2) - (600 // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (480 // 2)
        self.geometry(f"+{x}+{y}")
        
        self.configure(fg_color=self.tm.bg_main())
        
        self.steps = [
            {
                "icon": "👋",
                "title": "Welcome to Acadence",
                "description": "Acadence AI Voice to Text Tracker is your new smart academic workspace. Let's take a quick tour to help you get started!"
            },
            {
                "icon": "🏠",
                "title": "Home Dashboard",
                "description": "Your central hub. Here you'll find a quick summary of your pending tasks, overall progress, and Priority Tasks highlighting what needs your immediate attention."
            },
            {
                "icon": "📂",
                "title": "Subjects & Tasks",
                "description": "Organize your workload by creating Subjects (Major or Minor) and adding Tasks. You can sort and filter tasks by Priority and Deadline to stay laser-focused."
            },
            {
                "icon": "🎙️",
                "title": "Voice AI Entry",
                "description": "Tired of typing? Click the Voice AI button at the top right of the screen to quickly log new subjects and tasks just by speaking naturally!"
            },
            {
                "icon": "📈",
                "title": "Insights & History",
                "description": "Keep track of your productivity over time. View your completion stats in the Insights tab, and review all your finished work in History."
            }
        ]
        
        self.current_step = 0
        self.setup_ui()
        self.render_step()

    def setup_ui(self):
        # Progress indicators at top
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.pack(fill="x", pady=(30, 10), padx=40)
        
        self.dots = []
        for _ in range(len(self.steps)):
            dot = ctk.CTkFrame(self.progress_frame, width=40, height=6, corner_radius=3, fg_color=self.tm.border_main())
            dot.pack(side="left", expand=True, padx=5)
            self.dots.append(dot)
            
        # Content area
        self.content_frame = ctk.CTkFrame(self, fg_color=self.tm.bg_card(), corner_radius=15, border_color=self.tm.border_main(), border_width=2)
        self.content_frame.pack(fill="both", expand=True, padx=40, pady=10)
        
        self.icon_lbl = ctk.CTkLabel(self.content_frame, text="", font=(self.tm.main_font(), 60))
        self.icon_lbl.pack(pady=(40, 10))
        
        self.title_lbl = ctk.CTkLabel(self.content_frame, text="", font=(self.tm.main_font(), 24, "bold"), text_color=self.tm.text_main())
        self.title_lbl.pack(pady=(0, 15))
        
        self.desc_lbl = ctk.CTkLabel(self.content_frame, text="", font=(self.tm.main_font(), 16), text_color=self.tm.text_sub(), wraplength=450, justify="center")
        self.desc_lbl.pack(padx=30, pady=(0, 30))
        
        # Bottom Navigation
        self.nav_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        self.nav_frame.pack(fill="x", side="bottom", pady=20, padx=40)
        self.nav_frame.pack_propagate(False)
        
        self.skip_btn = ctk.CTkButton(self.nav_frame, text="Skip Tour", font=(self.tm.main_font(), 14, "bold"), text_color=self.tm.text_sub(), fg_color="transparent", hover_color=self.tm.bg_sub(), width=100, command=self.finish_tour)
        self.skip_btn.pack(side="left")
        
        self.next_btn = ctk.CTkButton(self.nav_frame, text="Next ❯", font=(self.tm.main_font(), 14, "bold"), text_color=self.tm.accent_text(), fg_color=self.tm.accent_color(), hover_color=self.tm.accent_hover(), width=120, height=40, corner_radius=8, command=self.next_step)
        self.next_btn.pack(side="right")
        
    def render_step(self):
        step = self.steps[self.current_step]
        
        self.icon_lbl.configure(text=step["icon"])
        self.title_lbl.configure(text=step["title"])
        self.desc_lbl.configure(text=step["description"])
        
        # Update progress dots
        for i, dot in enumerate(self.dots):
            if i <= self.current_step:
                dot.configure(fg_color=self.tm.accent_color())
            else:
                dot.configure(fg_color=self.tm.border_main())
                
        # Update Next button
        if self.current_step == len(self.steps) - 1:
            self.next_btn.configure(text="Get Started", fg_color=self.tm.success_color(), hover_color="#218838")
            self.skip_btn.pack_forget() # Hide skip on last slide
        else:
            self.next_btn.configure(text="Next ❯", fg_color=self.tm.accent_color(), hover_color=self.tm.accent_hover())
            self.skip_btn.pack(side="left")
            
    def next_step(self):
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self.render_step()
        else:
            self.finish_tour()
            
    def finish_tour(self):
        if self.on_complete:
            self.on_complete()
        self.destroy()
