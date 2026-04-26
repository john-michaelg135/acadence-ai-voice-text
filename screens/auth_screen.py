import customtkinter as ctk
from utils.theme_manager import ThemeManager
from tkinter import messagebox
from database.db_manager import DatabaseManager
from utils.security import validate_password_strength

class AuthScreen(ctk.CTkFrame):
    def __init__(self, master, on_login_success):
        self.tm = ThemeManager()
        super().__init__(master, fg_color="transparent")
        self.on_login_success = on_login_success
        self.db = DatabaseManager()

        self.setup_ui()

    def setup_ui(self):
        # Header
        ctk.CTkLabel(self, text="Acadence", font=("Arial", 36, "bold"), text_color=self.tm.accent_color()).pack(pady=(40, 10))
        ctk.CTkLabel(self, text="AI Voice to Text Tracker", font=("Arial", 16)).pack(pady=(0, 20))

        # Tabview for Login / Sign Up
        self.tabview = ctk.CTkTabview(self, width=300)
        self.tabview.pack(padx=20, pady=10)

        self.tabview.add("Log In")
        self.tabview.add("Sign Up")

        self.setup_login_tab(self.tabview.tab("Log In"))
        self.setup_signup_tab(self.tabview.tab("Sign Up"))

    def setup_login_tab(self, parent):
        self.login_user_entry = ctk.CTkEntry(parent, placeholder_text="Username")
        self.login_user_entry.pack(pady=(10, 5), fill="x", padx=20)

        self.login_pass_entry = ctk.CTkEntry(parent, placeholder_text="Password", show="*")
        self.login_pass_entry.pack(pady=5, fill="x", padx=20)

        ctk.CTkButton(parent, text="Log In", fg_color=self.tm.accent_color(), text_color=self.tm.text_main(), command=self.handle_login).pack(pady=15, padx=20, fill="x")

        # Forgot Password
        forgot_lbl = ctk.CTkLabel(parent, text="Forgot Password?", font=("Arial", 12, "underline"), text_color=self.tm.text_sub(), cursor="hand2")
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

        ctk.CTkButton(parent, text="Sign Up", fg_color=self.tm.accent_color(), text_color=self.tm.text_main(), command=self.handle_signup).pack(pady=15, padx=20, fill="x")

    def handle_login(self):
        username = self.login_user_entry.get().strip()
        password = self.login_pass_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Please fill all fields.")
            return

        user, err_msg = self.db.authenticate_user(username, password)
        if user:
            self.on_login_success(user)
        else:
            messagebox.showerror("Login Failed", err_msg)

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

        # OAuth Style Password Strength Check
        is_valid, msg = validate_password_strength(password)
        if not is_valid:
            messagebox.showerror("Weak Password", msg)
            return

        success = self.db.create_user(username, password, recovery_email=email)
        if success:
            messagebox.showinfo("Success", "Account created successfully! You can now log in.")
            self.tabview.set("Log In")
        else:
            messagebox.showerror("Error", "Username already exists.")

    def show_forgot_password(self):
        ForgotPasswordPopup(self, self.db)


class ForgotPasswordPopup(ctk.CTkToplevel):
    def __init__(self, master, db):
        self.tm = ThemeManager()
        super().__init__(master)
        self.title("Recover Account")
        self.geometry("350x400")
        self.db = db
        self.attributes("-topmost", True)
        
        self.target_username = ""
        self.valid_otp = ""
        
        # Step frames
        self.step1_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.step2_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.step3_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        self.show_step1()
        
    def clear_frames(self):
        self.step1_frame.pack_forget()
        self.step2_frame.pack_forget()
        self.step3_frame.pack_forget()
        
    def show_step1(self):
        self.clear_frames()
        self.step1_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(self.step1_frame, text="Account Recovery", font=("Arial", 20, "bold")).pack(pady=(0, 20))
        ctk.CTkLabel(self.step1_frame, text="Enter your username and the recovery email registered to your account.", wraplength=300).pack(pady=(0, 20))
        
        self.user_entry = ctk.CTkEntry(self.step1_frame, placeholder_text="Username")
        self.user_entry.pack(fill="x", pady=5)
        
        self.email_entry = ctk.CTkEntry(self.step1_frame, placeholder_text="Recovery Email")
        self.email_entry.pack(fill="x", pady=5)
        
        ctk.CTkButton(self.step1_frame, text="Send Verification Code", fg_color=self.tm.accent_color(), text_color=self.tm.text_main(), command=self.process_step1).pack(pady=20)
        
    def process_step1(self):
        user = self.user_entry.get().strip()
        email = self.email_entry.get().strip()
        
        if not user or not email:
            messagebox.showerror("Error", "Fill all fields.", parent=self)
            return
            
        if self.db.recover_password(user, email):
            self.target_username = user
            self.target_email = email
            
            from utils.email_service import send_reset_otp
            import threading
            
            # Set the button to a loading state to inform the user it's processing
            for widget in self.step1_frame.winfo_children():
                if isinstance(widget, ctk.CTkButton):
                    widget.configure(text="Connecting to SMTP Server...", state="disabled")
            
            def _send():
                result = send_reset_otp(email)
                if result.get("ok"):
                    self.after(0, lambda: messagebox.showinfo("Email Sent", "An OTP has been sent securely to your email address.", parent=self))
                    self.after(0, self.show_step2)
                else:
                    self.after(0, lambda: messagebox.showerror("Email Error", result.get("reason"), parent=self))
                    # Reset button natively
                    for widget in self.step1_frame.winfo_children():
                        if isinstance(widget, ctk.CTkButton):
                            self.after(0, lambda w=widget: w.configure(text="Send Verification Code", state="normal"))
                            
            threading.Thread(target=_send, daemon=True).start()
        else:
            messagebox.showerror("Error", "Username or Recovery Email is incorrect.", parent=self)
            
    def show_step2(self):
        self.clear_frames()
        self.step2_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(self.step2_frame, text="Verify OTP", font=("Arial", 20, "bold")).pack(pady=(0, 20))
        ctk.CTkLabel(self.step2_frame, text="Enter the 6-digit code sent to your email.", wraplength=300).pack(pady=(0, 20))
        
        self.otp_entry = ctk.CTkEntry(self.step2_frame, placeholder_text="123456")
        self.otp_entry.pack(fill="x", pady=5)
        
        ctk.CTkButton(self.step2_frame, text="Verify", fg_color=self.tm.accent_color(), text_color=self.tm.text_main(), command=self.process_step2).pack(pady=20)
        
    def process_step2(self):
        entered = self.otp_entry.get().strip()
        from utils.email_service import verify
        result = verify(self.target_email, entered)
        
        if result.get("ok"):
            self.show_step3()
        else:
            messagebox.showerror("Error", result.get("reason"), parent=self)
            
    def show_step3(self):
        self.clear_frames()
        self.step3_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(self.step3_frame, text="Reset Password", font=("Arial", 20, "bold")).pack(pady=(0, 20))
        
        self.new_pass_entry = ctk.CTkEntry(self.step3_frame, placeholder_text="New Password", show="*")
        self.new_pass_entry.pack(fill="x", pady=5)
        
        self.conf_pass_entry = ctk.CTkEntry(self.step3_frame, placeholder_text="Confirm New Password", show="*")
        self.conf_pass_entry.pack(fill="x", pady=5)
        
        ctk.CTkButton(self.step3_frame, text="Update Password", fg_color=self.tm.accent_color(), text_color=self.tm.text_main(), command=self.process_step3).pack(pady=20)
        
    def process_step3(self):
        new_pwd = self.new_pass_entry.get().strip()
        conf_pwd = self.conf_pass_entry.get().strip()
        
        if not new_pwd or new_pwd != conf_pwd:
            messagebox.showerror("Error", "Passwords do not match or are empty.", parent=self)
            return
            
        from utils.security import validate_password_strength
        is_val, msg = validate_password_strength(new_pwd)
        if not is_val:
            messagebox.showerror("Weak Password", msg, parent=self)
            return
            
        self.db.admin_reset_password(self.target_username, new_pwd, is_system=False)
        messagebox.showinfo("Success", "Password updated successfully! You may now log in.", parent=self)
        self.destroy()
