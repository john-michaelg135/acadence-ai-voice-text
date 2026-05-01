import customtkinter as ctk
from utils.theme_manager import ThemeManager

class MoreView(ctk.CTkFrame):
    def __init__(self, master, user_info, on_logout, reload_callback):
        self.tm = ThemeManager()
        super().__init__(master, fg_color="transparent")
        self.user_info = user_info
        self.on_logout = on_logout
        self.reload_callback = reload_callback
        
        self.setup_ui()

    def setup_ui(self):
        # Header
        ctk.CTkLabel(self, text="Settings & More", font=("Arial", 28, "bold"), text_color=self.tm.text_main()).pack(anchor="w", padx=20, pady=(20, 10))
        
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=self.tm.bg_main(), scrollbar_button_hover_color=self.tm.text_sub())
        scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 1. Customization Card
        cust_card = ctk.CTkFrame(scroll, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=2, corner_radius=15)
        cust_card.pack(fill="x", pady=(0, 15), padx=10)
        
        ctk.CTkLabel(cust_card, text="Customization", font=("Arial", 18, "bold"), text_color=self.tm.text_main()).pack(anchor="w", padx=20, pady=(15, 10))
        
        # Modern Mode Toggle
        mode_frame = ctk.CTkFrame(cust_card, fg_color="transparent")
        mode_frame.pack(fill="x", padx=20, pady=10)
        
        mode_info = ctk.CTkFrame(mode_frame, fg_color="transparent")
        mode_info.pack(side="left")
        ctk.CTkLabel(mode_info, text="Appearance Mode", font=("Arial", 15, "bold"), text_color=self.tm.text_main()).pack(anchor="w")
        ctk.CTkLabel(mode_info, text="Choose between light, dark, or system default themes.", font=("Arial", 12), text_color=self.tm.text_sub()).pack(anchor="w")
        
        current_mode = ctk.get_appearance_mode()
        
        mode_toggle_frame = ctk.CTkFrame(mode_frame, fg_color=self.tm.bg_sub(), corner_radius=16)
        mode_toggle_frame.pack(side="right")
        
        self.mode_buttons = {}
        
        def toggle_mode(v):
            ctk.set_appearance_mode(v)
            self.update_mode_buttons(v)
            
        for m_val in ["Light", "Dark", "System"]:
            btn = ctk.CTkButton(
                mode_toggle_frame, text=m_val, width=70, height=28, corner_radius=14,
                font=("Arial", 12, "bold"),
                command=lambda v=m_val: toggle_mode(v)
            )
            btn.pack(side="left", padx=3, pady=3)
            self.mode_buttons[m_val] = btn
            
        self.update_mode_buttons(current_mode)
        
        # Accent Color
        accent_frame = ctk.CTkFrame(cust_card, fg_color="transparent")
        accent_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        accent_info = ctk.CTkFrame(accent_frame, fg_color="transparent")
        accent_info.pack(side="left")
        ctk.CTkLabel(accent_info, text="Accent Color Theme", font=("Arial", 15, "bold"), text_color=self.tm.text_main()).pack(anchor="w")
        ctk.CTkLabel(accent_info, text="Personalize the app with your favorite pastel color palette.", font=("Arial", 12), text_color=self.tm.text_sub()).pack(anchor="w")
        
        self.accent_var = ctk.StringVar(value=self.tm.current_accent)
        
        def change_accent(val):
            self.tm.current_accent = val
            self.reload_callback() # Rebuild the whole UI using the new color scheme
            
        self.accent_menu = ctk.CTkOptionMenu(accent_frame, values=self.tm.get_theme_names(),
                                        variable=self.accent_var, command=change_accent,
                                        fg_color=self.tm.accent_color(), button_color=self.tm.accent_hover(), button_hover_color=self.tm.accent_color(),
                                        text_color=self.tm.accent_text())
        self.accent_menu.pack(side="right")
        
        # 2. About Card
        about_card = ctk.CTkFrame(scroll, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=2, corner_radius=15)
        about_card.pack(fill="x", pady=15, padx=10)
        
        ctk.CTkLabel(about_card, text="About Acadence", font=("Arial", 18, "bold"), text_color=self.tm.text_main()).pack(anchor="w", padx=20, pady=(15, 5))
        
        ctk.CTkLabel(about_card, text="Version 1.0.0", font=("Arial", 12, "bold"), text_color=self.tm.accent_color()).pack(anchor="w", padx=20)
        
        desc = (
            "Acadence AI Voice to Text Tracker is an advanced academic management tool built to redefine how students and professionals "
            "handle their daily tasks. By seamlessly integrating state-of-the-art voice recognition with intelligent task monitoring, "
            "Acadence allows you to effortlessly capture notes, track deadlines, and organize subjects without breaking your workflow.\n\n"
            "Whether you are managing major university courses, tracking high-priority assignments, or simply organizing your academic "
            "life, Acadence's dynamic pastel-themed interface provides a focused, beautiful, and highly productive environment tailored precisely to your needs."
        )
        ctk.CTkLabel(about_card, text=desc, font=("Arial", 14), text_color=self.tm.text_sub(), wraplength=800, justify="left").pack(anchor="w", padx=20, pady=(10, 20))
        
    def update_mode_buttons(self, current_mode):
        for val, btn in self.mode_buttons.items():
            if val == current_mode:
                btn.configure(fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover())
            else:
                btn.configure(fg_color="transparent", text_color=self.tm.text_sub(), hover_color=self.tm.border_main())
