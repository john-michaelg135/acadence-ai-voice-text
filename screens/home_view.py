import customtkinter as ctk

class HomeView(ctk.CTkFrame):
    def __init__(self, master, user_info):
        super().__init__(master, fg_color="transparent")
        self.user_info = user_info
        self.text_dark = "#1A1A1A"
        self.text_gray = "#666666"
        self.purple_main = "#B5B0D3"
        
        self.setup_ui()

    def setup_ui(self):
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=25, pady=(40, 20))

        display_name = "Guest" if not self.user_info else self.user_info.get("username", "User")

        welcome_label = ctk.CTkLabel(
            header_frame, text=f"Welcome back, {display_name}!", 
            font=("Arial", 28, "bold"), text_color=self.text_dark
        )
        welcome_label.pack(anchor="w")

        sub_header = ctk.CTkLabel(
            header_frame, text="Here is your Academic overview", 
            font=("Arial", 16), text_color=self.text_gray
        )
        sub_header.pack(anchor="w")

        # Priority Card
        priority_card = ctk.CTkFrame(self, fg_color=self.purple_main, corner_radius=25, height=180)
        priority_card.pack(fill="x", padx=25, pady=10)
        priority_card.pack_propagate(False)

        ctk.CTkLabel(priority_card, text="Priority Card", font=("Arial", 18, "bold"), text_color=self.text_dark).pack(pady=(15, 0))
        
        p_content = ctk.CTkFrame(priority_card, fg_color="transparent")
        p_content.pack(expand=True)
        ctk.CTkLabel(p_content, text="⚠️  0", font=("Arial", 40, "bold"), text_color=self.text_dark).pack()

        ctk.CTkLabel(
            priority_card, 
            text="These are the number of pending\ntask with high priority.", 
            font=("Arial", 14), text_color=self.text_dark
        ).pack(pady=(0, 15))

        # Subjects Card
        subjects_card = ctk.CTkFrame(self, fg_color="white", border_color="#E0E0E0", border_width=2, corner_radius=25, height=200)
        subjects_card.pack(fill="x", padx=25, pady=10)
        subjects_card.pack_propagate(False)

        ctk.CTkLabel(subjects_card, text="Subjects", font=("Arial", 18, "bold"), text_color=self.text_dark).pack(pady=(15, 0))
        
        s_content = ctk.CTkFrame(subjects_card, fg_color="transparent")
        s_content.pack(expand=True)
        ctk.CTkLabel(s_content, text="🔖  0", font=("Arial", 50, "bold"), text_color=self.text_dark).pack()

        ctk.CTkLabel(
            subjects_card, 
            text="Added subjects will appear as\ncontainers in the bottom.", 
            font=("Arial", 14), text_color=self.text_gray
        ).pack(pady=(0, 15))
