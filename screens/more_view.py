import customtkinter as ctk
from utils.theme_manager import ThemeManager
import webbrowser
import os
from PIL import Image

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
        ctk.CTkLabel(self, text="Settings & More", font=(self.tm.main_font(), 28, "bold"), text_color=self.tm.text_main()).pack(anchor="w", padx=20, pady=(20, 10))
        
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=self.tm.bg_main(), scrollbar_button_hover_color=self.tm.text_sub())
        scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 1. Customization Card
        cust_card = ctk.CTkFrame(scroll, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=2, corner_radius=15)
        cust_card.pack(fill="x", pady=(0, 15), padx=10)
        
        ctk.CTkLabel(cust_card, text="Customization", font=(self.tm.main_font(), 18, "bold"), text_color=self.tm.text_main()).pack(anchor="w", padx=20, pady=(15, 10))
        
        # Modern Mode Toggle
        mode_frame = ctk.CTkFrame(cust_card, fg_color="transparent")
        mode_frame.pack(fill="x", padx=20, pady=10)
        
        mode_info = ctk.CTkFrame(mode_frame, fg_color="transparent")
        mode_info.pack(side="left")
        ctk.CTkLabel(mode_info, text="Appearance Mode", font=(self.tm.main_font(), 15, "bold"), text_color=self.tm.text_main()).pack(anchor="w")
        ctk.CTkLabel(mode_info, text="Choose between light, dark, or system default themes.", font=(self.tm.main_font(), 12), text_color=self.tm.text_sub()).pack(anchor="w")
        
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
                font=(self.tm.main_font(), 12, "bold"),
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
        ctk.CTkLabel(accent_info, text="Accent Color Theme", font=(self.tm.main_font(), 15, "bold"), text_color=self.tm.text_main()).pack(anchor="w")
        ctk.CTkLabel(accent_info, text="Personalize the app with your favorite pastel color palette.", font=(self.tm.main_font(), 12), text_color=self.tm.text_sub()).pack(anchor="w")
        
        self.accent_var = ctk.StringVar(value=self.tm.current_accent)
        
        def change_accent(val):
            self.tm.current_accent = val
            self.reload_callback() # Rebuild the whole UI using the new color scheme
            
        self.accent_menu = ctk.CTkOptionMenu(accent_frame, values=self.tm.get_theme_names(),
                                        variable=self.accent_var, command=change_accent,
                                        fg_color=self.tm.accent_color(), button_color=self.tm.accent_hover(), button_hover_color=self.tm.accent_color(),
                                        text_color=self.tm.accent_text(),
                                        font=(self.tm.main_font(), 13), dropdown_font=(self.tm.main_font(), 13))
        self.accent_menu.pack(side="right")
        
        # 2. About Card
        about_card = ctk.CTkFrame(scroll, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=2, corner_radius=15)
        about_card.pack(fill="x", pady=15, padx=10)
        
        ctk.CTkLabel(about_card, text="About Acadence", font=(self.tm.main_font(), 18, "bold"), text_color=self.tm.text_main()).pack(anchor="w", padx=20, pady=(15, 5))
        
        ctk.CTkLabel(about_card, text="Version 1.0.0", font=(self.tm.main_font(), 12, "bold"), text_color=self.tm.accent_color()).pack(anchor="w", padx=20)
        
        desc = (
            "Acadence AI Voice to Text Tracker is an advanced academic management tool built to redefine how students and professionals "
            "handle their daily tasks. By seamlessly integrating state-of-the-art voice recognition with intelligent task monitoring, "
            "Acadence allows you to effortlessly capture notes, track deadlines, and organize subjects without breaking your workflow.\n\n"
            "Whether you are managing major university courses, tracking high-priority assignments, or simply organizing your academic "
            "life, Acadence's dynamic pastel-themed interface provides a focused, beautiful, and highly productive environment tailored precisely to your needs."
        )
        ctk.CTkLabel(about_card, text=desc, font=(self.tm.main_font(), 14), text_color=self.tm.text_sub(), wraplength=800, justify="left").pack(anchor="w", padx=20, pady=(10, 20))
        
        # 3. Contact Support Card
        support_card = ctk.CTkFrame(scroll, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=2, corner_radius=15)
        support_card.pack(fill="x", pady=15, padx=10)
        
        ctk.CTkLabel(support_card, text="Contact Support", font=(self.tm.main_font(), 18, "bold"), text_color=self.tm.text_main()).pack(anchor="w", padx=20, pady=(15, 10))
        
        socials_container = ctk.CTkFrame(support_card, fg_color="transparent")
        socials_container.pack(fill="x", padx=20, pady=(0, 20))
        
        # Create high-res circular indicator procedurally
        def create_circle_img(color):
            size = 64 # High res base
            img = Image.new("RGBA", (size, size), (0,0,0,0))
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            draw.ellipse((2, 2, size-2, size-2), fill=color)
            return img

        # Generate circles for light/dark (following accent color)
        accent = self.tm.accent_color()
        # handle tuple or string
        light_c = accent[0] if isinstance(accent, tuple) else accent
        dark_c = accent[1] if isinstance(accent, tuple) else accent
        
        circle_img = ctk.CTkImage(
            light_image=create_circle_img(light_c),
            dark_image=create_circle_img(dark_c),
            size=(18, 18)
        )

        # Social Items (Replicating the screenshot's vertical timeline style)
        socials = [
            ("Facebook", "@John Michael Garcia", "https://www.facebook.com/johnmichael.garcia.75"),
            ("Instagram", "@kaelculated_", "https://instagram.com/kaelculated_"),
            ("GitHub", "@john-michaelg135", "https://github.com/john-michaelg135")
        ]
        
        for name, handle, url in socials:
            item_frame = ctk.CTkFrame(socials_container, fg_color="transparent")
            item_frame.pack(fill="x", pady=8)
            
            # Themed High-Res Circle Indicator
            circle_lbl = ctk.CTkLabel(item_frame, image=circle_img, text="", cursor="hand2")
            circle_lbl.pack(side="left", padx=(5, 15))
            
            text_frame = ctk.CTkFrame(item_frame, fg_color="transparent", cursor="hand2")
            text_frame.pack(side="left")
            
            name_lbl = ctk.CTkLabel(text_frame, text=name, font=(self.tm.main_font(), 14, "bold"), text_color=self.tm.text_main())
            name_lbl.pack(anchor="w")
            
            handle_lbl = ctk.CTkLabel(text_frame, text=handle, font=(self.tm.main_font(), 12), text_color=self.tm.accent_color())
            handle_lbl.pack(anchor="w")
            
            # Bind all parts to the URL
            for w in [circle_lbl, text_frame, name_lbl, handle_lbl]:
                w.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
                w.configure(cursor="hand2")

        # 4. Legal Information Section
        ctk.CTkLabel(scroll, text="Legal Information", font=(self.tm.main_font(), 28, "bold"), text_color=self.tm.text_main()).pack(anchor="w", padx=10, pady=(30, 10))
        
        # Terms Card
        terms_card = ctk.CTkFrame(scroll, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=2, corner_radius=15)
        terms_card.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(terms_card, text="Terms & Conditions", font=(self.tm.main_font(), 18, "bold"), text_color=self.tm.text_main()).pack(anchor="w", padx=20, pady=(15, 5))
        ctk.CTkLabel(terms_card, text="Last Updated: May 3, 2026", font=(self.tm.main_font(), 12), text_color=self.tm.text_sub()).pack(anchor="w", padx=20)
        
        terms_text = (
            "Welcome to Acadence! By using our app, you agree to the following terms:\n\n"
            "1. Purpose: Acadence helps students manage academic tasks by organizing them by subject, priority, and deadlines.\n\n"
            "2. User Responsibilities: Use the app responsibly and avoid any unauthorized or illegal activities.\n\n"
            "3. Account: Keep your login credentials secure.\n\n"
            "4. Intellectual Property: The app’s design and features are owned by Acadence and cannot be copied or redistributed without permission.\n\n"
            "5. Liability: Acadence is provided \"as is,\" and we are not responsible for any damages from its use.\n\n"
            "6. Updates: We may modify the app or terms, and continued use signifies your acceptance."
        )
        ctk.CTkLabel(terms_card, text=terms_text, font=(self.tm.main_font(), 13), text_color=self.tm.text_sub(), wraplength=800, justify="left").pack(anchor="w", padx=20, pady=(10, 20))
        
        # Privacy Card
        privacy_card = ctk.CTkFrame(scroll, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=2, corner_radius=15)
        privacy_card.pack(fill="x", pady=(10, 30), padx=10)
        
        ctk.CTkLabel(privacy_card, text="Privacy Policy", font=(self.tm.main_font(), 18, "bold"), text_color=self.tm.text_main()).pack(anchor="w", padx=20, pady=(15, 5))
        ctk.CTkLabel(privacy_card, text="Last Updated: May 3, 2026", font=(self.tm.main_font(), 12), text_color=self.tm.text_sub()).pack(anchor="w", padx=20)
        
        privacy_text = (
            "Acadence values your privacy. Here’s how we handle your data:\n\n"
            "1. Data Collection: Personal Information: Collected during login (e.g., email).\n\n"
            "2. Usage Data: Task details and usage patterns to improve the app.\n\n"
            "3. Data Usage: To securely store and manage your tasks. To enhance functionality and provide insights into your progress.\n\n"
            "4. Data Sharing: We do not sell or share your data, except when required by law or for app functionality.\n\n"
            "5. Security: Data is stored securely, and users are responsible for protecting their account credentials.\n\n"
            "6. Your Rights: You have the ability to access, update, or delete your data at any time. If you choose to delete your account, all stored information will be erased.\n\n"
            "7. Policy Updates: Changes to this policy will be communicated here."
        )
        ctk.CTkLabel(privacy_card, text=privacy_text, font=(self.tm.main_font(), 13), text_color=self.tm.text_sub(), wraplength=800, justify="left").pack(anchor="w", padx=20, pady=(10, 5))
        
        email_frame = ctk.CTkFrame(privacy_card, fg_color="transparent")
        email_frame.pack(anchor="w", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(email_frame, text="For questions, contact us at ", font=(self.tm.main_font(), 13), text_color=self.tm.text_sub()).pack(side="left")
        
        email_lbl = ctk.CTkLabel(email_frame, text="aiyosui@gmail.com", font=(self.tm.main_font(), 13, "bold"), text_color=self.tm.accent_color(), cursor="hand2")
        email_lbl.pack(side="left")
        email_lbl.bind("<Button-1>", lambda e: webbrowser.open("mailto:aiyosui@gmail.com"))
        
    def update_mode_buttons(self, current_mode):
        for val, btn in self.mode_buttons.items():
            if val == current_mode:
                btn.configure(fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover())
            else:
                btn.configure(fg_color="transparent", text_color=self.tm.text_sub(), hover_color=self.tm.border_main())
