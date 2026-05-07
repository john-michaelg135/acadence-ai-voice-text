import customtkinter as ctk
import threading
import random
from tkinter import messagebox
from utils.theme_manager import ThemeManager
from utils.voice_manager import start_continuous_listening
from utils.ai_parser import parse_voice_command
from utils.logger import logger

class VoiceRecordingPopup(ctk.CTkToplevel):
    def __init__(self, master, on_complete_callback, command_type='subject'):
        self.tm = ThemeManager()
        super().__init__(master, fg_color=self.tm.bg_card())
        self.on_complete_callback = on_complete_callback
        self.command_type = command_type
        self.is_listening = True
        self.stop_listening_func = None
        # Guard flag: set True BEFORE super().destroy() so background threads
        # never schedule new after() callbacks onto a mid-destruction window.
        self._destroyed = False
        
        self.title("Voice Assistant")
        self.geometry("450x450")
        self.attributes("-topmost", True)
        self.resizable(False, False)
        
        # Center over master
        self.update_idletasks()
        try:
            x = master.winfo_rootx() + (master.winfo_width() // 2) - (450 // 2)
            y = master.winfo_rooty() + (master.winfo_height() // 2) - (450 // 2)
            self.geometry(f"+{x}+{y}")
        except:
            pass
        
        self.setup_ui()
        self.grab_set()
        
        # Start continuous listening
        self.stop_listening_func = start_continuous_listening(self.on_phrase_transcribed)
        self.animate_wave()

    def destroy(self):
        """Override destroy to set the guard flag first, preventing race conditions."""
        self._destroyed = True
        self.is_listening = False
        try:
            super().destroy()
        except Exception:
            pass

    def setup_ui(self):
        self.container = ctk.CTkFrame(self, fg_color=self.tm.bg_card(), corner_radius=15)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # --- Waveform Section ---
        self.wave_frame = ctk.CTkFrame(self.container, fg_color="transparent", height=120)
        self.wave_frame.pack(pady=(10, 10))
        self.wave_frame.pack_propagate(False)
        
        self.bars = []
        num_bars = 9
        for i in range(num_bars):
            bar = ctk.CTkFrame(self.wave_frame, width=10, height=10, fg_color=self.tm.accent_color(), corner_radius=5)
            bar.pack(side="left", padx=5, anchor="center")
            self.bars.append(bar)
            
        self.status_lbl = ctk.CTkLabel(self.container, text="Listening... Please speak now.", font=(self.tm.main_font(), 16, "bold"), text_color=self.tm.accent_color())
        self.status_lbl.pack(pady=(0, 15))
        
        # --- Review Section (Always visible now to show live text) ---
        self.review_frame = ctk.CTkFrame(self.container, fg_color=self.tm.bg_sub(), corner_radius=10)
        self.review_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(self.review_frame, text="Live Transcription:", font=(self.tm.main_font(), 12, "bold"), text_color=self.tm.text_main()).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.text_box = ctk.CTkTextbox(self.review_frame, height=80, fg_color="transparent", text_color=self.tm.text_sub(), font=(self.tm.main_font(), 13))
        self.text_box.pack(fill="x", padx=10, pady=(0, 10))
        
        # --- Actions Section ---
        self.actions_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.actions_frame.pack(side="bottom", fill="x", pady=(10, 0))
        
        self.cancel_btn = ctk.CTkButton(self.actions_frame, text="Cancel", width=100, fg_color="transparent", border_width=1, 
                      text_color=self.tm.text_sub(), border_color=self.tm.border_main(), hover_color=self.tm.bg_sub(), font=(self.tm.main_font(), 13, "bold"),
                      command=self.on_cancel)
        self.cancel_btn.pack(side="left", padx=5)
        
        self.stop_btn = ctk.CTkButton(self.actions_frame, text="Done Speaking", width=120, fg_color=self.tm.accent_color(),
                      text_color=self.tm.accent_text(), hover_color=self.tm.accent_hover(), font=(self.tm.main_font(), 13, "bold"),
                      command=self.on_stop_speaking)
        self.stop_btn.pack(side="right", padx=5)

        self.confirm_btn = ctk.CTkButton(self.actions_frame, text="Process", width=160, fg_color=self.tm.success_color(),
                      text_color=self.tm.text_main(), hover_color=self.tm.success_hover(), font=(self.tm.main_font(), 13, "bold"),
                      command=self.on_confirm)

    def on_phrase_transcribed(self, text):
        # _destroyed guard prevents after() calls onto a mid-destruction window
        if not self._destroyed and self.is_listening:
            try:
                self.after(0, lambda: self._append_text(text))
            except Exception as e:
                logger.error(f"Failed to append transcribed text: {e}", exc_info=True)
            
    def _append_text(self, text):
        current = self.text_box.get("0.0", "end").strip()
        if current:
            self.text_box.insert("end", " " + text)
        else:
            self.text_box.insert("end", text)

    def animate_wave(self):
        if self._destroyed or not self.is_listening:
            return
        try:
            if not self.winfo_exists():
                return
            for bar in self.bars:
                new_h = random.randint(20, 110)
                bar.configure(height=new_h)
            self.after(120, self.animate_wave)
        except Exception:
            pass

    def on_stop_speaking(self):
        self.is_listening = False
        if self.stop_listening_func:
            self.stop_listening_func()
            
        self.status_lbl.configure(text="Transcription Complete", text_color=self.tm.text_main())
        self.stop_btn.pack_forget()
        self.confirm_btn.pack(side="right", padx=5)
        
    def on_cancel(self):
        if self.stop_listening_func:
            try:
                self.stop_listening_func()
            except Exception as e:
                logger.warning(f"Error stopping listening on cancel: {e}")
        self.destroy()
        
    def on_confirm(self):
        final_text = self.text_box.get("0.0", "end").strip()
        if not final_text:
            messagebox.showerror("Voice Error", "No transcription available to confirm.", parent=self)
            return
            
        self.status_lbl.configure(text="AI Mapping Text...", text_color=self.tm.accent_color())
        self.confirm_btn.configure(state="disabled", text="Parsing...")
        self.update()
        
        # Run parsing in background so we don't freeze the UI
        def parse_thread():
            parsed_data = parse_voice_command(final_text, self.command_type)
            self.after(0, lambda: self._finish_confirm(parsed_data))
            
        threading.Thread(target=parse_thread, daemon=True).start()
        
    def _finish_confirm(self, parsed_data):
        if not self._destroyed:
            self.destroy()
            self.on_complete_callback(parsed_data)
