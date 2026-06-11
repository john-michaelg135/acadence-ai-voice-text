import customtkinter as ctk
import random
from utils.theme_manager import ThemeManager

class WalkthroughPopup(ctk.CTkToplevel):
    def __init__(self, master, on_complete):
        super().__init__(master)
        self.tm = ThemeManager()
        self.on_complete = on_complete
        self.master_ref = master
        
        self.title("Welcome to Acadence")
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{sw}x{sh}+0+0")
        self.overrideredirect(True)
        self.configure(fg_color=self.tm.bg_main())
        
        # Ensure it stays on top
        self.attributes("-topmost", True)
        self.transient(master)
        self.grab_set()

        self.steps = [
            {
                "icon": "✨",
                "title": "Welcome to Acadence",
                "description": "Your intelligent academic workspace designed to streamline your studies. Let's explore what makes Acadence special.",
                "bullets": [
                    "Beautiful, themeable interface",
                    "Offline-first, privacy-focused",
                    "Powered by Voice AI"
                ],
                "render_func": self.render_welcome_mock
            },
            {
                "icon": "🏠",
                "title": "Your Dashboard",
                "description": "The central hub of your academic life. Get an instant overview of your workload and what needs your attention right now.",
                "bullets": [
                    "Quick summary of pending tasks",
                    "Spotlight on high priority items",
                    "Overview of active subjects"
                ],
                "render_func": self.render_dashboard_mock
            },
            {
                "icon": "📂",
                "title": "Manage Subjects",
                "description": "Organize your curriculum efficiently. Group your tasks by subject to keep your workspace clutter-free.",
                "bullets": [
                    "Categorize as Major or Minor",
                    "Assign unique subject codes",
                    "Track progress per subject"
                ],
                "render_func": self.render_subject_mock
            },
            {
                "icon": "✅",
                "title": "Track Tasks",
                "description": "Never miss a deadline. Create detailed tasks and track them from pending to complete.",
                "bullets": [
                    "Set task priorities (High/Medium/Low)",
                    "Define exact deadlines",
                    "Mark done with a single click"
                ],
                "render_func": self.render_task_mock
            },
            {
                "icon": "🎤",
                "title": "Voice AI",
                "description": "Speak naturally to log subjects and tasks. Our on-device Voice AI understands your intent and categorizes everything automatically.",
                "bullets": [
                    "Hands-free entry",
                    "Understands conversational language",
                    "Fast and responsive"
                ],
                "render_func": self.render_voice_mock
            },
            {
                "icon": "📈",
                "title": "Insights & History",
                "description": "Visualize your productivity. Track your completion rates and review everything you've accomplished.",
                "bullets": [
                    "Bar charts for subject progress",
                    "Recent activity feed",
                    "Complete historical log"
                ],
                "render_func": self.render_insights_mock
            },
            {
                "icon": "🔔",
                "title": "Stay Notified",
                "description": "Keep on top of upcoming deadlines with smart desktop notifications.",
                "bullets": [
                    "Customizable advance notifications",
                    "Directly mark tasks done from toasts",
                    "Grouped daily summaries"
                ],
                "render_func": self.render_notifications_mock
            }
        ]
        
        self.current_step = 0
        self._animating = False
        self._animation_after_id = None
        
        self.setup_ui()
        self.render_step()

    def setup_ui(self):
        # Top Progress Bar (thin line)
        self.progress_bg = ctk.CTkFrame(self, height=4, fg_color=self.tm.bg_sub(), corner_radius=0)
        self.progress_bg.pack(fill="x", side="top")
        
        self.progress_bar = ctk.CTkFrame(self.progress_bg, height=4, fg_color=self.tm.accent_color(), corner_radius=0, width=0)
        self.progress_bar.place(x=0, y=0)
        
        # Main Split Container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)

        # ---------------- LEFT PANEL (Content) ----------------
        self.left_panel = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.left_panel.pack(side="left", fill="both", expand=True, padx=(80, 40), pady=60)
        
        # Step Badge
        self.step_badge = ctk.CTkLabel(self.left_panel, text="Step 1 of 7", font=(self.tm.main_font(), 14, "bold"),
                                       fg_color=self.tm.bg_sub(), text_color=self.tm.accent_color(), corner_radius=12,
                                       width=100, height=30)
        self.step_badge.pack(anchor="w", pady=(20, 30))

        # Content Wrapper for sliding animation
        self.content_wrapper = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.content_wrapper.pack(fill="both", expand=True)
        
        self.icon_lbl = ctk.CTkLabel(self.content_wrapper, text="", font=(self.tm.main_font(), 50))
        self.icon_lbl.pack(anchor="w", pady=(0, 20))
        
        self.title_lbl = ctk.CTkLabel(self.content_wrapper, text="", font=(self.tm.main_font(), 42, "bold"), text_color=self.tm.text_main())
        self.title_lbl.pack(anchor="w", pady=(0, 20))
        
        self.desc_lbl = ctk.CTkLabel(self.content_wrapper, text="", font=(self.tm.main_font(), 18), text_color=self.tm.text_sub(),
                                     wraplength=500, justify="left")
        self.desc_lbl.pack(anchor="w", pady=(0, 40))
        
        # Bullets Container
        self.bullets_frame = ctk.CTkFrame(self.content_wrapper, fg_color="transparent")
        self.bullets_frame.pack(anchor="w", fill="x")

        # Bottom Navigation
        self.nav_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent", height=60)
        self.nav_frame.pack(fill="x", side="bottom", pady=(0, 20))
        
        self.skip_btn = ctk.CTkButton(self.nav_frame, text="Skip Tour", font=(self.tm.main_font(), 15, "bold"),
                                      text_color=self.tm.text_sub(), fg_color="transparent", hover_color=self.tm.bg_sub(),
                                      command=self.finish_tour)
        self.skip_btn.pack(side="left")
        
        self.next_btn = ctk.CTkButton(self.nav_frame, text="Continue ❯", font=(self.tm.main_font(), 16, "bold"),
                                      text_color=self.tm.accent_text(), fg_color=self.tm.accent_color(), hover_color=self.tm.accent_hover(),
                                      width=160, height=50, corner_radius=25, command=self.next_step)
        self.next_btn.pack(side="right")
        
        self.back_btn = ctk.CTkButton(self.nav_frame, text="❮ Back", font=(self.tm.main_font(), 15, "bold"),
                                      text_color=self.tm.text_sub(), fg_color="transparent", hover_color=self.tm.bg_sub(),
                                      width=100, height=50, corner_radius=25, command=self.prev_step)
        self.back_btn.pack(side="right", padx=10)

        # ---------------- RIGHT PANEL (Preview) ----------------
        self.right_panel = ctk.CTkFrame(self.main_container, fg_color=self.tm.bg_sub(), corner_radius=0)
        self.right_panel.pack(side="right", fill="both", expand=True)
        
        # Centered Mock Container
        self.mock_container = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.mock_container.place(relx=0.5, rely=0.5, anchor="center")

    def _clear_mock(self):
        for widget in self.mock_container.winfo_children():
            widget.destroy()
        if self._animation_after_id:
            self.after_cancel(self._animation_after_id)
            self._animation_after_id = None

    def render_step(self):
        step = self.steps[self.current_step]
        
        # Update progress bar width based on screen width
        sw = self.winfo_screenwidth()
        progress_w = int((self.current_step + 1) / len(self.steps) * sw)
        self.progress_bar.configure(width=progress_w)
        
        self.step_badge.configure(text=f"Step {self.current_step + 1} of {len(self.steps)}")
        
        # Slide in animation reset
        self.content_wrapper.pack_forget()
        self.content_wrapper.pack(fill="both", expand=True, pady=(30, 0)) # Slight bump down to slide up
        self.after(20, lambda: self.content_wrapper.pack(fill="both", expand=True, pady=(0, 0)))
        
        self.icon_lbl.configure(text=step["icon"])
        self.title_lbl.configure(text=step["title"])
        self.desc_lbl.configure(text=step["description"])
        
        # Bullets
        for w in self.bullets_frame.winfo_children(): w.destroy()
        for bullet in step["bullets"]:
            row = ctk.CTkFrame(self.bullets_frame, fg_color="transparent")
            row.pack(fill="x", pady=8)
            ctk.CTkLabel(row, text="✦", font=(self.tm.main_font(), 16), text_color=self.tm.accent_color()).pack(side="left", padx=(0, 15))
            ctk.CTkLabel(row, text=bullet, font=(self.tm.main_font(), 16, "bold"), text_color=self.tm.text_main()).pack(side="left")
            
        # Nav buttons logic
        self.back_btn.configure(state="normal" if self.current_step > 0 else "disabled")
        if self.current_step == len(self.steps) - 1:
            self.next_btn.configure(text="Get Started", fg_color=self.tm.success_color(), hover_color=self.tm.success_hover())
            self.skip_btn.pack_forget()
        else:
            self.next_btn.configure(text="Continue ❯", fg_color=self.tm.accent_color(), hover_color=self.tm.accent_hover())
            self.skip_btn.pack(side="left")

        # Render mock
        self._clear_mock()
        step["render_func"]()

    def next_step(self):
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self.render_step()
        else:
            self.finish_tour()
            
    def prev_step(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.render_step()

    def finish_tour(self):
        if self._animation_after_id:
            self.after_cancel(self._animation_after_id)
        if self.on_complete:
            self.on_complete()
        self.destroy()

    # ---------------- MOCK RENDERERS ----------------
    def create_mock_card(self, width, height, title=""):
        card = ctk.CTkFrame(self.mock_container, width=width, height=height, fg_color=self.tm.bg_card(),
                            corner_radius=15, border_width=2, border_color=self.tm.border_main())
        card.pack_propagate(False)
        if title:
            # Fake title bar
            header = ctk.CTkFrame(card, height=40, fg_color="transparent")
            header.pack(fill="x", padx=15, pady=10)
            ctk.CTkLabel(header, text=title, font=(self.tm.main_font(), 16, "bold"), text_color=self.tm.text_main()).pack(side="left")
        return card

    def render_welcome_mock(self):
        card = self.create_mock_card(350, 350)
        card.pack(pady=20)
        
        lbl = ctk.CTkLabel(card, text="A", font=(self.tm.main_font(), 100, "bold"), text_color=self.tm.accent_color())
        lbl.place(relx=0.5, rely=0.4, anchor="center")
        
        sub = ctk.CTkLabel(card, text="Acadence", font=(self.tm.main_font(), 24, "bold"), text_color=self.tm.text_main())
        sub.place(relx=0.5, rely=0.7, anchor="center")
        
        # Simple pulsating animation
        def pulse(scale=1.0, growing=True):
            if not self.winfo_exists() or self.current_step != 0: return
            try:
                font_size = int(100 * scale)
                lbl.configure(font=(self.tm.main_font(), font_size, "bold"))
                if growing:
                    scale += 0.02
                    if scale >= 1.1: growing = False
                else:
                    scale -= 0.02
                    if scale <= 1.0: growing = True
                self._animation_after_id = self.after(50, lambda: pulse(scale, growing))
            except: pass
        pulse()

    def render_dashboard_mock(self):
        main_card = self.create_mock_card(400, 300)
        main_card.pack(pady=20)
        
        # 3 mini cards
        ctk.CTkLabel(main_card, text="Dashboard", font=(self.tm.main_font(), 18, "bold"), text_color=self.tm.text_main()).pack(anchor="w", padx=20, pady=20)
        
        row = ctk.CTkFrame(main_card, fg_color="transparent")
        row.pack(fill="x", padx=20)
        
        c1 = ctk.CTkFrame(row, fg_color=self.tm.accent_color(), corner_radius=10, height=120)
        c1.pack(side="left", fill="x", expand=True, padx=(0, 5))
        c1.pack_propagate(False)
        ctk.CTkLabel(c1, text="⚠️", font=(self.tm.main_font(), 24)).pack(pady=(15, 0))
        ctk.CTkLabel(c1, text="3", font=(self.tm.main_font(), 28, "bold"), text_color=self.tm.accent_text()).pack()
        
        c2 = ctk.CTkFrame(row, fg_color=self.tm.bg_sub(), corner_radius=10, border_width=1, border_color=self.tm.border_main(), height=120)
        c2.pack(side="left", fill="x", expand=True, padx=5)
        c2.pack_propagate(False)
        ctk.CTkLabel(c2, text="🔖", font=(self.tm.main_font(), 24)).pack(pady=(15, 0))
        ctk.CTkLabel(c2, text="5", font=(self.tm.main_font(), 28, "bold"), text_color=self.tm.text_main()).pack()

        c3 = ctk.CTkFrame(row, fg_color=self.tm.bg_sub(), corner_radius=10, border_width=1, border_color=self.tm.border_main(), height=120)
        c3.pack(side="left", fill="x", expand=True, padx=(5, 0))
        c3.pack_propagate(False)
        ctk.CTkLabel(c3, text="📋", font=(self.tm.main_font(), 24)).pack(pady=(15, 0))
        ctk.CTkLabel(c3, text="12", font=(self.tm.main_font(), 28, "bold"), text_color=self.tm.text_main()).pack()

    def render_subject_mock(self):
        card = self.create_mock_card(320, 380)
        card.pack(pady=20)
        
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(top, text="Major", font=(self.tm.main_font(), 12, "bold"), fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), corner_radius=8, width=60, height=24).pack(side="left")
        ctk.CTkLabel(card, text="Advanced Algorithms", font=(self.tm.main_font(), 20, "bold"), text_color=self.tm.text_main()).pack(anchor="w", padx=20, pady=5)
        ctk.CTkLabel(card, text="CS-401", font=(self.tm.main_font(), 14), text_color=self.tm.accent_color()).pack(anchor="w", padx=20)
        
        # Banner Image
        from PIL import Image, ImageDraw
        try:
            def create_rounded_image(path, size, radius):
                img = Image.open(path).convert("RGBA").resize(size, Image.Resampling.LANCZOS)
                mask = Image.new("L", size, 0)
                draw = ImageDraw.Draw(mask)
                draw.rounded_rectangle((0, 0, size[0], size[1]), radius, fill=255)
                img.putalpha(mask)
                return img

            r_img = create_rounded_image("assets/major_banner.png", (280, 120), 10)
            img_ctk = ctk.CTkImage(light_image=r_img, dark_image=r_img, size=(280, 120))
            banner = ctk.CTkLabel(card, image=img_ctk, text="")
            banner.pack(fill="x", padx=20, pady=20)
        except Exception:
            banner = ctk.CTkFrame(card, height=120, fg_color=self.tm.bg_sub(), corner_radius=10)
            banner.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(card, text="View Tasks", font=(self.tm.main_font(), 14, "bold"), fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), text_color_disabled=self.tm.accent_text(), height=40, corner_radius=8, state="disabled").pack(fill="x", padx=20, pady=(10, 20))

    def render_task_mock(self):
        card = self.create_mock_card(450, 160)
        card.pack(pady=20)
        
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="both", expand=True, padx=20, pady=20)
        
        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left")
        ctk.CTkLabel(left, text="Complete Final Project", font=(self.tm.main_font(), 18, "bold"), text_color=self.tm.text_main()).pack(anchor="w")
        ctk.CTkLabel(left, text="📅 Tomorrow, 11:59 PM", font=(self.tm.main_font(), 13), text_color=self.tm.text_sub()).pack(anchor="w", pady=(5, 0))
        
        right = ctk.CTkFrame(row, fg_color="transparent")
        right.pack(side="right")
        ctk.CTkLabel(right, text="High", font=(self.tm.main_font(), 14, "bold"), text_color=self.tm.error_color()).pack(side="left", padx=15)
        btn = ctk.CTkButton(right, text="Mark as Done", font=(self.tm.main_font(), 12, "bold"), width=100, height=30, fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), corner_radius=15)
        btn.pack(side="left")
        
        # Hover animation mock
        def blink_btn(on=True):
            if not self.winfo_exists() or self.current_step != 3: return
            try:
                btn.configure(fg_color=self.tm.accent_hover() if on else self.tm.accent_color())
                self._animation_after_id = self.after(800, lambda: blink_btn(not on))
            except: pass
        blink_btn()

    def render_voice_mock(self):
        card = self.create_mock_card(300, 350)
        card.pack(pady=20)
        
        ctk.CTkLabel(card, text="Listening...", font=(self.tm.main_font(), 18, "bold"), text_color=self.tm.accent_color()).pack(pady=(40, 20))
        
        wave_frame = ctk.CTkFrame(card, fg_color="transparent", height=80)
        wave_frame.pack(pady=10)
        
        bars = []
        for _ in range(7):
            bar = ctk.CTkFrame(wave_frame, width=8, height=10, fg_color=self.tm.accent_color(), corner_radius=4)
            bar.pack(side="left", padx=4, anchor="center")
            bars.append(bar)
            
        tb = ctk.CTkTextbox(card, height=60, font=(self.tm.main_font(), 13), fg_color=self.tm.bg_sub(), text_color=self.tm.text_main())
        tb.pack(fill="x", padx=20, pady=20)
        tb.insert("0.0", "Add a major subject called Advanced Physics...")
        tb.configure(state="disabled")

        def animate_bars():
            if not self.winfo_exists() or self.current_step != 4: return
            try:
                for b in bars:
                    b.configure(height=random.randint(10, 70))
                self._animation_after_id = self.after(150, animate_bars)
            except: pass
        animate_bars()

    def render_insights_mock(self):
        card = self.create_mock_card(400, 300)
        card.pack(pady=20)
        
        ctk.CTkLabel(card, text="Completion by Subject", font=(self.tm.main_font(), 16, "bold"), text_color=self.tm.text_main()).pack(anchor="w", padx=20, pady=(20, 10))
        
        chart = ctk.CTkFrame(card, fg_color="transparent")
        chart.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Fake bars
        vals = [8, 5, 2, 9]
        names = ["Math", "Science", "History", "Art"]
        
        for i in range(4):
            col = ctk.CTkFrame(chart, fg_color="transparent")
            col.pack(side="left", fill="both", expand=True)
            
            bar_container = ctk.CTkFrame(col, fg_color="transparent")
            bar_container.pack(fill="both", expand=True, side="top", pady=(0, 5))
            
            h = int((vals[i]/10) * 150)
            bar = ctk.CTkFrame(bar_container, width=30, height=0, fg_color=self.tm.accent_color(), corner_radius=4)
            bar.place(relx=0.5, rely=1.0, anchor="s")
            
            lbl_val = ctk.CTkLabel(bar_container, text=f"{vals[i]}", font=(self.tm.main_font(), 11, "bold"), text_color=self.tm.text_main())
            lbl_val.place(relx=0.5, y=0, rely=1.0, anchor="s")
            
            ctk.CTkLabel(col, text=names[i], font=(self.tm.main_font(), 12, "bold"), text_color=self.tm.text_sub()).pack(side="bottom")
            
            # Animate height
            def grow(b=bar, l=lbl_val, target_h=h, curr_h=0):
                if not self.winfo_exists() or self.current_step != 5: return
                try:
                    curr_h += 10
                    if curr_h > target_h: curr_h = target_h
                    b.configure(height=curr_h)
                    l.place(relx=0.5, y=-curr_h - 5, rely=1.0, anchor="s")
                    if curr_h < target_h:
                        self.after(20, lambda b=b, l=l, th=target_h, ch=curr_h: grow(b, l, th, ch))
                except: pass
            grow()

    def render_notifications_mock(self):
        card = self.create_mock_card(350, 200)
        card.pack(pady=20)
        
        ctk.CTkLabel(card, text="🔔 System Notification", font=(self.tm.main_font(), 14, "bold"), text_color=self.tm.text_sub()).pack(anchor="w", padx=20, pady=(20, 5))
        
        toast = ctk.CTkFrame(card, fg_color=self.tm.bg_sub(), corner_radius=10, border_width=1, border_color=self.tm.border_main())
        toast.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        ctk.CTkLabel(toast, text="Task Due Soon!", font=(self.tm.main_font(), 16, "bold"), text_color=self.tm.text_main()).pack(anchor="w", padx=15, pady=(15, 5))
        ctk.CTkLabel(toast, text="Database Architecture is due in 1 day.", font=(self.tm.main_font(), 13), text_color=self.tm.text_sub()).pack(anchor="w", padx=15)
        
        btn = ctk.CTkButton(toast, text="Mark Done", font=(self.tm.main_font(), 12, "bold"), width=100, height=30, fg_color=self.tm.success_color(), text_color=self.tm.text_main(), corner_radius=15)
        btn.pack(anchor="e", padx=15, pady=10)
        
        def slide_in(y_offset=20):
            if not self.winfo_exists() or self.current_step != 6: return
            try:
                if y_offset > 0:
                    y_offset -= 2
                    toast.pack_configure(pady=(y_offset, 20 - y_offset))
                    self._animation_after_id = self.after(16, lambda: slide_in(y_offset))
            except: pass
        slide_in()
