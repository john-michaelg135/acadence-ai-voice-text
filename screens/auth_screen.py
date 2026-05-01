import customtkinter as ctk
from utils.theme_manager import ThemeManager
from tkinter import messagebox
from database.db_manager import DatabaseManager
from utils.security import validate_password_strength
import threading

class AuthScreen(ctk.CTkFrame):
    def __init__(self, master, on_login_success):
        self.tm = ThemeManager()
        super().__init__(master, fg_color="transparent")
        self.on_login_success = on_login_success
        self.db = DatabaseManager()

        self.current_auth_mode = ctk.StringVar(value="Log In")
        self.target_username = ""
        self.target_email = ""

        # Main wrapper to center everything perfectly
        self.wrapper = ctk.CTkFrame(self, fg_color="transparent")
        self.wrapper.place(relx=0.5, rely=0.5, anchor="center")

        self.setup_ui()

    def setup_ui(self):
        # Branding Header
        ctk.CTkLabel(self.wrapper, text="Acadence", font=(self.tm.main_font(), 42, "bold"), text_color=self.tm.accent_color()).pack(pady=(0, 5))
        ctk.CTkLabel(self.wrapper, text="AI Voice to Text Tracker", font=(self.tm.main_font(), 16), text_color=self.tm.text_sub()).pack(pady=(0, 25))

        # Main Interactive Card
        self.card = ctk.CTkFrame(self.wrapper, fg_color=self.tm.bg_card(), border_color=self.tm.border_main(), border_width=1, corner_radius=15, width=380)
        self.card.pack(fill="both", expand=True)
        self.card.pack_propagate(False)

        # Modern Toggle
        self.toggle_frame = ctk.CTkFrame(self.card, fg_color=self.tm.bg_sub(), corner_radius=20, border_color=self.tm.border_main(), border_width=1)
        self.toggle_frame.pack(pady=20, padx=25, fill="x")

        self.toggle_buttons = {}
        for mode in ["Log In", "Sign Up"]:
            btn = ctk.CTkButton(
                self.toggle_frame, text=mode, height=36, corner_radius=18,
                font=(self.tm.main_font(), 14, "bold"),
                command=lambda m=mode: self.switch_mode(m)
            )
            btn.pack(side="left", expand=True, fill="x", padx=3, pady=3)
            self.toggle_buttons[mode] = btn

        # Container for swapping forms
        self.form_container = ctk.CTkFrame(self.card, fg_color="transparent")
        self.form_container.pack(fill="both", expand=True, padx=25)

        self.login_frame = ctk.CTkFrame(self.form_container, fg_color="transparent")
        self.signup_frame = ctk.CTkFrame(self.form_container, fg_color="transparent")
        self.forgot_frame = ctk.CTkFrame(self.form_container, fg_color="transparent")

        # Step frames for forgot password wizard
        self.step1_frame = ctk.CTkFrame(self.forgot_frame, fg_color="transparent")
        self.step2_frame = ctk.CTkFrame(self.forgot_frame, fg_color="transparent")
        self.step3_frame = ctk.CTkFrame(self.forgot_frame, fg_color="transparent")

        self.input_args = {"height": 45, "corner_radius": 10, "border_color": self.tm.border_main(), "fg_color": self.tm.bg_sub(), "text_color": self.tm.text_main(), "font": (self.tm.main_font(), 14)}
        self.btn_args = {"height": 45, "corner_radius": 10, "font": (self.tm.main_font(), 15, "bold"), "fg_color": self.tm.accent_color(), "text_color": self.tm.accent_text(), "hover_color": self.tm.accent_hover()}

        self.setup_login_tab()
        self.setup_signup_tab()
        self.setup_forgot_tab()

        # Initialize
        self.switch_mode("Log In")

    @staticmethod
    def _make_eye_icon(slashed: bool):
        """Renders a high-res (64px) eye icon, displayed at 22px for crisp scaling."""
        from PIL import Image, ImageDraw
        s = 64
        color = (90, 90, 90, 255)
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Eye oval
        d.ellipse([4, 18, 60, 46], outline=color, width=4)
        # Pupil
        d.ellipse([26, 26, 38, 38], fill=color)
        # Diagonal slash (bottom-left → top-right) when visible
        if slashed:
            d.line([10, 54, 54, 10], fill=color, width=5)
        return ctk.CTkImage(light_image=img, dark_image=img, size=(22, 22))

    def _make_password_field(self, parent, placeholder, pack_pady=10):
        """Creates a styled password entry with a PIL-drawn eye icon toggle button."""
        container = ctk.CTkFrame(
            parent,
            fg_color=self.tm.bg_sub(),
            border_color=self.tm.border_main(),
            border_width=1,
            corner_radius=10,
            height=45
        )
        container.pack(pady=pack_pady, fill="x")
        container.pack_propagate(False)

        entry = ctk.CTkEntry(
            container,
            placeholder_text=placeholder,
            show="*",
            fg_color="transparent",
            border_width=0,
            text_color=self.tm.text_main(),
            font=(self.tm.main_font(), 14),
            height=43
        )
        entry.pack(side="left", fill="both", expand=True, padx=(8, 0))

        icon_show = self._make_eye_icon(slashed=False)   # plain eye  → click to reveal
        icon_hide = self._make_eye_icon(slashed=True)    # slashed eye → click to mask

        eye_btn = ctk.CTkButton(
            container, text="", image=icon_show,
            width=36, height=36,
            fg_color="transparent",
            hover_color=self.tm.border_main(),
            corner_radius=8
        )

        # State variable — avoids relying on entry.cget('show') which
        # behaves inconsistently on CTkEntry when the field is empty.
        _hidden = [True]

        def _toggle():
            if _hidden[0]:
                entry.configure(show="")
                eye_btn.configure(image=icon_hide)
                _hidden[0] = False
            else:
                entry.configure(show="*")
                eye_btn.configure(image=icon_show)
                _hidden[0] = True

        eye_btn.configure(command=_toggle)
        eye_btn.pack(side="right", padx=(0, 5))
        return entry

    def switch_mode(self, mode):
        self.current_auth_mode.set(mode)
        
        self.login_frame.pack_forget()
        self.signup_frame.pack_forget()
        self.forgot_frame.pack_forget()

        if mode == "Forgot Password":
            self.toggle_frame.pack_forget()
            self.card.configure(height=480)
            self.forgot_frame.pack(fill="both", expand=True)
            self.show_forgot_step1()
            return
            
        self.toggle_frame.pack(pady=20, padx=25, fill="x", before=self.form_container)

        for m, btn in self.toggle_buttons.items():
            if m == mode:
                btn.configure(fg_color=self.tm.accent_color(), text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover())
            else:
                btn.configure(fg_color="transparent", text_color=self.tm.text_sub(), hover_color=self.tm.border_main())

        if mode == "Log In":
            self.card.configure(height=380)
            self.login_frame.pack(fill="both", expand=True)
        else:
            self.card.configure(height=520)
            self.signup_frame.pack(fill="both", expand=True)

    # ---------------- LOGIN TAB ---------------- #
    def setup_login_tab(self):
        self.login_user_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Username", **self.input_args)
        self.login_user_entry.pack(pady=(10, 10), fill="x")

        self.login_pass_entry = self._make_password_field(self.login_frame, "Password")

        ctk.CTkButton(self.login_frame, text="Log In", command=self.handle_login, **self.btn_args).pack(pady=(20, 15), fill="x")

        forgot_lbl = ctk.CTkLabel(self.login_frame, text="Forgot Password?", font=(self.tm.main_font(), 13, "underline"), text_color=self.tm.text_sub(), cursor="hand2")
        forgot_lbl.pack()
        forgot_lbl.bind("<Button-1>", lambda e: self.switch_mode("Forgot Password"))

    # ---------------- SIGN UP TAB ---------------- #
    def setup_signup_tab(self):
        self.signup_user_entry = ctk.CTkEntry(self.signup_frame, placeholder_text="Username", **self.input_args)
        self.signup_user_entry.pack(pady=(5, 10), fill="x")

        self.signup_email_entry = ctk.CTkEntry(self.signup_frame, placeholder_text="Recovery Email", **self.input_args)
        self.signup_email_entry.pack(pady=10, fill="x")

        self.signup_pass_entry = self._make_password_field(self.signup_frame, "Password")
        self.signup_conf_entry = self._make_password_field(self.signup_frame, "Confirm Password")

        ctk.CTkButton(self.signup_frame, text="Create Account", command=self.handle_signup, **self.btn_args).pack(pady=(15, 10), fill="x")

    # ---------------- FORGOT PASSWORD ---------------- #
    def setup_forgot_tab(self):
        # Header for forgot password with back button
        hdr = ctk.CTkFrame(self.forgot_frame, fg_color="transparent")
        hdr.pack(fill="x", pady=(20, 15))
        
        ctk.CTkButton(hdr, text="← Back", width=50, fg_color="transparent", text_color=self.tm.text_sub(), hover_color=self.tm.bg_sub(), font=(self.tm.main_font(), 13), command=lambda: self.switch_mode("Log In")).pack(side="left")
        ctk.CTkLabel(hdr, text="Account Recovery", font=(self.tm.main_font(), 20, "bold"), text_color=self.tm.text_main()).pack(side="left", padx=20)

        # STEP 1
        ctk.CTkLabel(self.step1_frame, text="Enter your username and the recovery email registered to your account.", wraplength=300, font=(self.tm.main_font(), 13), text_color=self.tm.text_sub()).pack(pady=(0, 20))
        self.rec_user_entry = ctk.CTkEntry(self.step1_frame, placeholder_text="Username", **self.input_args)
        self.rec_user_entry.pack(fill="x", pady=10)
        self.rec_email_entry = ctk.CTkEntry(self.step1_frame, placeholder_text="Recovery Email", **self.input_args)
        self.rec_email_entry.pack(fill="x", pady=10)
        self.btn_send_otp = ctk.CTkButton(self.step1_frame, text="Send Verification Code", command=self.process_step1, **self.btn_args)
        self.btn_send_otp.pack(pady=20, fill="x")

        # STEP 2
        ctk.CTkLabel(self.step2_frame, text="Enter the 6-digit code sent to your email.", wraplength=300, font=(self.tm.main_font(), 13), text_color=self.tm.text_sub()).pack(pady=(0, 20))
        self.otp_entry = ctk.CTkEntry(self.step2_frame, placeholder_text="123456", justify="center", **self.input_args)
        self.otp_entry.pack(fill="x", pady=10)
        ctk.CTkButton(self.step2_frame, text="Verify Code", command=self.process_step2, **self.btn_args).pack(pady=20, fill="x")

        # STEP 3
        ctk.CTkLabel(self.step3_frame, text="Create a new strong password for your account.", wraplength=300, font=(self.tm.main_font(), 13), text_color=self.tm.text_sub()).pack(pady=(0, 20))
        self.new_pass_entry = self._make_password_field(self.step3_frame, "New Password")
        self.conf_new_pass_entry = self._make_password_field(self.step3_frame, "Confirm New Password")
        ctk.CTkButton(self.step3_frame, text="Update Password", command=self.process_step3, **self.btn_args).pack(pady=20, fill="x")

    def show_forgot_step1(self):
        self.step1_frame.pack_forget()
        self.step2_frame.pack_forget()
        self.step3_frame.pack_forget()
        self.step1_frame.pack(fill="both", expand=True)
        
    def show_forgot_step2(self):
        self.step1_frame.pack_forget()
        self.step3_frame.pack_forget()
        self.step2_frame.pack(fill="both", expand=True)

    def show_forgot_step3(self):
        self.step1_frame.pack_forget()
        self.step2_frame.pack_forget()
        self.step3_frame.pack(fill="both", expand=True)

    def process_step1(self):
        user = self.rec_user_entry.get().strip()
        email = self.rec_email_entry.get().strip()
        
        if not user or not email:
            messagebox.showerror("Error", "Fill all fields.")
            return
            
        if self.db.recover_password(user, email):
            self.target_username = user
            self.target_email = email
            from utils.email_service import send_reset_otp
            
            self.btn_send_otp.configure(text="Connecting to SMTP...", state="disabled")
            
            def _send():
                result = send_reset_otp(email)
                if result.get("ok"):
                    self.after(0, lambda: messagebox.showinfo("Email Sent", "An OTP has been sent securely to your email address."))
                    self.after(0, self.show_forgot_step2)
                else:
                    self.after(0, lambda: messagebox.showerror("Email Error", result.get("reason")))
                self.after(0, lambda: self.btn_send_otp.configure(text="Send Verification Code", state="normal"))
                            
            threading.Thread(target=_send, daemon=True).start()
        else:
            messagebox.showerror("Error", "Username or Recovery Email is incorrect.")

    def process_step2(self):
        entered = self.otp_entry.get().strip()
        from utils.email_service import verify
        result = verify(self.target_email, entered)
        if result.get("ok"):
            self.show_forgot_step3()
        else:
            messagebox.showerror("Error", result.get("reason"))

    def process_step3(self):
        new_pwd = self.new_pass_entry.get().strip()
        conf_pwd = self.conf_new_pass_entry.get().strip()
        
        if not new_pwd or new_pwd != conf_pwd:
            messagebox.showerror("Error", "Passwords do not match or are empty.")
            return
            
        is_val, msg = validate_password_strength(new_pwd)
        if not is_val:
            messagebox.showerror("Weak Password", msg)
            return
            
        self.db.admin_reset_password(self.target_username, new_pwd, is_system=False)
        messagebox.showinfo("Success", "Password updated successfully! You may now log in.")
        self.switch_mode("Log In")

    # ---------------- HANDLERS ---------------- #
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

        is_valid, msg = validate_password_strength(password)
        if not is_valid:
            messagebox.showerror("Weak Password", msg)
            return

        # Validate email format + domain existence before creating the account
        from utils.email_service import validate_email_address
        is_valid_email, email_msg = validate_email_address(email)
        if not is_valid_email:
            messagebox.showerror("Invalid Email", email_msg)
            return

        success = self.db.create_user(username, password, recovery_email=email)
        if success:
            messagebox.showinfo("Success", "Account created successfully! You can now log in.")
            self.switch_mode("Log In")
        else:
            messagebox.showerror("Error", "Username already exists.")
