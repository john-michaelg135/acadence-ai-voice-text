import customtkinter as ctk
from tkinter import messagebox
from database.db_manager import DatabaseManager

class SubjectsView(ctk.CTkFrame):
    def __init__(self, master, user_info, show_view_callback):
        super().__init__(master, fg_color="transparent")
        self.user_info = user_info
        self.show_view_callback = show_view_callback
        self.db = DatabaseManager()
        self.user_id = self.user_info['id'] if self.user_info else None
        
        self.setup_ui()
        self.load_subjects()

    def setup_ui(self):
        # Header area
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header_frame, text="Your Subjects", font=("Arial", 24, "bold"), text_color="#1A1A1A").pack(side="left")
        
        # Add buttons container
        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.pack(side="right")
        
        # Text Add Button
        ctk.CTkButton(btn_frame, text="+ Add", width=60, fg_color="#B5B0D3", text_color="#1A1A1A", command=self.add_subject_text).pack(side="left", padx=(0, 5))
        
        # Voice Add Button Placeholder
        ctk.CTkButton(btn_frame, text="🎤", width=40, fg_color="#B5B0D3", text_color="#1A1A1A", command=self.add_subject_voice).pack(side="left")

        # Scrollable list of subjects
        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scrollable_frame.pack(fill="both", expand=True, padx=20, pady=10)

    def load_subjects(self):
        if not self.user_id:
            ctk.CTkLabel(self.scrollable_frame, text="Guest users cannot save subjects permanently yet.", text_color="#666666").pack(pady=20)
            return

        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        subjects = self.db.get_subjects(self.user_id)
        if not subjects:
            ctk.CTkLabel(self.scrollable_frame, text="No subjects found. Add one!", text_color="#666666").pack(pady=20)
            return

        for sub in subjects:
            self.create_subject_card(sub)

    def create_subject_card(self, subject):
        card = ctk.CTkFrame(self.scrollable_frame, fg_color="#FFFFFF", border_color="#E0E0E0", border_width=1, corner_radius=10, height=80)
        card.pack(fill="x", pady=5)
        card.pack_propagate(False)

        # Subject Name
        lbl = ctk.CTkLabel(card, text=subject['name'], font=("Arial", 18, "bold"), text_color="#1A1A1A")
        lbl.pack(side="left", padx=15)

        # Actions
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(side="right", padx=15)

        ctk.CTkButton(btn_frame, text="Open", width=60, fg_color="#F0F0F0", text_color="#1A1A1A", hover_color="#E0E0E0",
                      command=lambda s=subject: self.open_subject(s)).pack(side="left", padx=(0, 10))
                      
        ctk.CTkButton(btn_frame, text="🗑️", width=40, fg_color="#FF6B6B", text_color="white", hover_color="#FF4C4C",
                      command=lambda s=subject: self.delete_subject(s)).pack(side="left")

    def open_subject(self, subject):
        self.show_view_callback("Tasks", subject_id=subject['id'], subject_name=subject['name'])

    def add_subject_text(self):
        if not self.user_id:
            messagebox.showinfo("Guest", "You need to log in to save subjects.")
            return
            
        dialog = ctk.CTkInputDialog(text="Enter new subject name:", title="Add Subject")
        name = dialog.get_input()
        if name and name.strip():
            self.db.add_subject(self.user_id, name.strip())
            self.load_subjects()

    def add_subject_voice(self):
        if not self.user_id:
            messagebox.showinfo("Guest", "You need to log in to save subjects.")
            return
            
        import threading
        from utils.voice_manager import listen_and_transcribe
        
        # simple thread to prevent UI freezing
        def listen_thread():
            text = listen_and_transcribe()
            if text:
                self.db.add_subject(self.user_id, text)
                self.after(0, self.load_subjects)
                self.after(0, lambda: messagebox.showinfo("Voice Recognized", f"Added subject: {text}"))
            else:
                self.after(0, lambda: messagebox.showerror("Voice Error", "Could not recognize speech or no speech detected."))
        
        messagebox.showinfo("Voice Recording", "Click OK and start speaking your subject name...")
        threading.Thread(target=listen_thread, daemon=True).start()

    def delete_subject(self, subject):
        if messagebox.askyesno("Delete", f"Are you sure you want to delete '{subject['name']}'?"):
            self.db.delete_subject(subject['id'])
            self.load_subjects()
