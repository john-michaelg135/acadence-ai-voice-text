import customtkinter as ctk
from tkinter import messagebox
from database.db_manager import DatabaseManager

class AuthScreen(ctk.CTkFrame):
    def __init__(self, master, on_login_success):
        super().__init__(master, fg_color="transparent")
        self.on_login_success = on_login_success
        self.db = DatabaseManager()

        self.setup_ui()

    def setup_ui(self):
        # Header
        ctk.CTkLabel(self, text="Acadence", font=("Arial", 36, "bold"), text_color="#B5B0D3").pack(pady=(40, 10))
        ctk.CTkLabel(self, text="AI Voice Text Tracker", font=("Arial", 16)).pack(pady=(0, 20))

        # Tabview for Login / Sign Up
        self.tabview = ctk.CTkTabview(self, width=300)
        self.tabview.pack(padx=20, pady=10)

        self.tabview.add("Log In")
        self.tabview.add("Sign Up")

        self.setup_login_tab(self.tabview.tab("Log In"))
        self.setup_signup_tab(self.tabview.tab("Sign Up"))

        # Guest Mode Bottom Frame
        guest_frame = ctk.CTkFrame(self, fg_color="transparent")
        guest_frame.pack(fill="x", pady=20)
        ctk.CTkButton(guest_frame, text="Continue as Guest", fg_color="transparent", 
                      border_width=1, text_color="#1A1A1A", command=self.guest_login).pack()

    def setup_login_tab(self, parent):
        self.login_user_entry = ctk.CTkEntry(parent, placeholder_text="Username")
        self.login_user_entry.pack(pady=(10, 5), fill="x", padx=20)

        self.login_pass_entry = ctk.CTkEntry(parent, placeholder_text="Password", show="*")
        self.login_pass_entry.pack(pady=5, fill="x", padx=20)

        ctk.CTkButton(parent, text="Log In", fg_color="#B5B0D3", text_color="#1A1A1A", command=self.handle_login).pack(pady=15, padx=20, fill="x")

        # Forgot Password
        forgot_lbl = ctk.CTkLabel(parent, text="Forgot Password?", font=("Arial", 12, "underline"), text_color="#666666", cursor="hand2")
        forgot_lbl.pack(pady=(0, 10))
        forgot_lbl.bind("<Button-1>", lambda e: self.show_forgot_password())

    def setup_signup_tab(self, parent):
        self.signup_user_entry = ctk.CTkEntry(parent, placeholder_text="Username")
        self.signup_user_entry.pack(pady=(5, 5), fill="x", padx=20)

        self.signup_email_entry = ctk.CTkEntry(parent, placeholder_text="Recovery Email")
        self.signup_email_entry.pack(pady=5, fill="x", padx=20)

        self.signup_pass_entry = ctk.CTkEntry(parent, placeholder_text="Password", show="*")
        self.signup_pass_entry.pack(pady=5, fill="x", padx=20)

        self.signup_conf_entry = ctk.CTkEntry(parent, placeholder_text="Confirm Password", show="*")
        self.signup_conf_entry.pack(pady=5, fill="x", padx=20)

        ctk.CTkButton(parent, text="Sign Up", fg_color="#B5B0D3", text_color="#1A1A1A", command=self.handle_signup).pack(pady=15, padx=20, fill="x")

    def handle_login(self):
        username = self.login_user_entry.get().strip()
        password = self.login_pass_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Please fill all fields.")
            return

        user = self.db.authenticate_user(username, password)
        if user:
            self.on_login_success(user)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    def handle_signup(self):
        username = self.signup_user_entry.get().strip()
        email = self.signup_email_entry.get().strip()
        password = self.signup_pass_entry.get().strip()
        conf_pass = self.signup_conf_entry.get().strip()

        if not all([username, email, password, conf_pass]):
            messagebox.showerror("Error", "Please fill all fields.")
            return

        if password != conf_pass:
            messagebox.showerror("Error", "Passwords do not match.")
            return

        success = self.db.create_user(username, password, recovery_email=email)
        if success:
            messagebox.showinfo("Success", "Account created successfully! You can now log in.")
            self.tabview.set("Log In")
        else:
            messagebox.showerror("Error", "Username already exists.")

    def guest_login(self):
        self.on_login_success(None)

    def show_forgot_password(self):
        # Placeholder for forgot password dialog
        messagebox.showinfo("Forgot Password", "Forgot password flow to be implemented (OTP to email).")
