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
        
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 1. Customization Card
        cust_card = ctk.CTkFrame(scroll, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=1, corner_radius=15)
        cust_card.pack(fill="x", pady=(0, 15), padx=10)
        
        ctk.CTkLabel(cust_card, text="Customization", font=("Arial", 18, "bold"), text_color=self.tm.text_main()).pack(anchor="w", padx=20, pady=(15, 10))
        
        # Dark Mode Toggle
        mode_frame = ctk.CTkFrame(cust_card, fg_color="transparent")
        mode_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(mode_frame, text="Appearance Mode", font=("Arial", 14), text_color=self.tm.text_sub()).pack(side="left")
        
        current_mode = ctk.get_appearance_mode()
        self.mode_var = ctk.StringVar(value=current_mode)
        
        def toggle_mode():
            ctk.set_appearance_mode(self.mode_var.get())
            
        mode_switch = ctk.CTkSegmentedButton(mode_frame, values=["Light", "Dark", "System"], 
                                             variable=self.mode_var, command=lambda _: toggle_mode(),
                                             selected_color=self.tm.accent_color(), selected_hover_color=self.tm.accent_hover())
        mode_switch.pack(side="right")
        
        # Accent Color
        accent_frame = ctk.CTkFrame(cust_card, fg_color="transparent")
        accent_frame.pack(fill="x", padx=20, pady=(10, 10))
        
        ctk.CTkLabel(accent_frame, text="Accent Color Theme", font=("Arial", 14), text_color=self.tm.text_sub()).pack(side="left")
        
        self.accent_var = ctk.StringVar(value=self.tm.current_accent)
        
        def change_accent(val):
            self.tm.current_accent = val
            self.reload_callback() # Rebuild the whole UI using the new color scheme
            
        accent_menu = ctk.CTkOptionMenu(accent_frame, values=self.tm.get_theme_names(),
                                        variable=self.accent_var, command=change_accent,
                                        fg_color=self.tm.accent_color(), button_color=self.tm.accent_hover(), button_hover_color=self.tm.accent_color())
        accent_menu.pack(side="right")
        
        # 2. About Card
        about_card = ctk.CTkFrame(scroll, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=1, corner_radius=15)
        about_card.pack(fill="x", pady=15, padx=10)
        
        ctk.CTkLabel(about_card, text="About Acadence", font=("Arial", 18, "bold"), text_color=self.tm.text_main()).pack(anchor="w", padx=20, pady=(15, 5))
        
        ctk.CTkLabel(about_card, text="Version 1.0.0", font=("Arial", 12, "bold"), text_color=self.tm.accent_color()).pack(anchor="w", padx=20)
        
        desc = "Acadence AI Voice to Text Tracker is an advanced academic management tool designed to streamline note-taking, task monitoring, and productivity through intelligent integration."
        ctk.CTkLabel(about_card, text=desc, font=("Arial", 13), text_color=self.tm.text_sub(), wraplength=320, justify="left").pack(anchor="w", padx=20, pady=10)
        
        # 3. Logout Section
        logout_card = ctk.CTkFrame(scroll, fg_color="transparent")
        logout_card.pack(fill="x", pady=20, padx=10)
        
        ctk.CTkButton(logout_card, text="Log Out", fg_color=self.tm.error_color(), text_color="#FFFFFF", 
                      hover_color=self.tm.error_hover(), command=self.on_logout, width=200, height=45, corner_radius=22, font=("Arial", 14, "bold")).pack(pady=10)
