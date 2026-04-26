import customtkinter as ctk

class ThemeManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ThemeManager, cls).__new__(cls)
            cls._instance.current_accent = "Pastel Purple"
        return cls._instance

    # Core Backgrounds & Elements
    def bg_main(self): return ("#FFFFFF", "#121212")
    def bg_sub(self): return ("#F4F5F7", "#1E1E1E")
    def bg_card(self): return ("#FFFFFF", "#1A1A1A")
    def bg_completed(self): return ("#F9FAFB", "#2B2B2B")
    
    def border_main(self): return ("#E5E7EB", "#333333")
    
    # Text
    def text_main(self): return ("#1A1A1A", "#F9FAFB")
    def text_sub(self): return ("#666666", "#A1A1AA")
    def text_inverse(self): return ("#FFFFFF", "#1A1A1A")
    
    # States
    def error_color(self): return ("#FF6B6B", "#EF4444")
    def error_hover(self): return ("#FF4C4C", "#DC2626")
    def warning_color(self): return ("#EAB308", "#F59E0B")
    def success_color(self): return ("#22C55E", "#10B981")
    
    @property
    def palettes(self):
        # 8 Pastel Themes
        # Dictionary Mapping: Name -> (Normal_Light, Normal_Dark, Hover_Color)
        return {
            "Pastel Purple": ("#B5B0D3", "#897AE0", "#9F8FF3"),
            "Pastel Pink": ("#FFB6C1", "#FF69B4", "#FF9EAD"),
            "Pastel Blue": ("#AEC6CF", "#779ECB", "#9AB9C6"),
            "Pastel Green": ("#B2E2E2", "#66C2A5", "#9BD5D5"),
            "Pastel Yellow": ("#FDFD96", "#FADA5E", "#F6F684"),
            "Pastel Peach": ("#FFDAB9", "#FFB347", "#FFCAA0"),
            "Pastel Mint": ("#98FF98", "#3EB489", "#82F582"),
            "Pastel Lavender": ("#E6E6FA", "#CCCCFF", "#D4D4F5")
        }
        
    def accent_color(self):
        pal = self.palettes.get(self.current_accent, self.palettes["Pastel Purple"])
        return (pal[0], pal[1])

    def accent_hover(self):
        pal = self.palettes.get(self.current_accent, self.palettes["Pastel Purple"])
        return (pal[2], pal[2])

    def accent_text(self):
        # Pastels often look best with dark text in light mode, but white text in dark mode (if dark mode accent is deeper)
        return ("#1A1A1A", "#FFFFFF")
        
    def get_theme_names(self):
        return list(self.palettes.keys())
