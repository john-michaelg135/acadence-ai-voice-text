import customtkinter as ctk
import threading

class ThemeManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ThemeManager, cls).__new__(cls)
                    cls._instance.current_accent = "Pastel Purple"
                    cls._instance._color_cache = {}
        return cls._instance

    def _invalidate_cache(self):
        """Clear cached color values when accent theme changes."""
        self._color_cache.clear()

    def set_accent(self, accent_name: str):
        """Set the current accent theme and invalidate cached colors."""
        if accent_name in self.palettes:
            self.current_accent = accent_name
            self._invalidate_cache()

    def main_font(self): return "Poppins"

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
    def success_color(self): return ("#4ADE80", "#10B981")
    def success_hover(self): return ("#22C55E", "#059669")
    
    @property
    def palettes(self):
        # 8 Pastel Themes
        # Dictionary Mapping: Name -> (Normal_Light, Normal_Dark, Hover_Color)
        return {
            "Pastel Purple": ("#B5B0D3", "#897AE0", "#9F8FF3"),
            "Pastel Pink": ("#FFB6C1", "#FF69B4", "#FF9EAD"),
            "Pastel Blue": ("#AEC6CF", "#779ECB", "#9AB9C6"),
            "Pastel Green": ("#B2E2E2", "#66C2A5", "#9BD5D5"),
            "Pastel Yellow": ("#FDF0B5", "#FADA5E", "#FCE883"),
            "Pastel Peach": ("#FFDAB9", "#FFB347", "#FFCAA0"),
            "Pastel Mint": ("#98FF98", "#3EB489", "#82F582"),
            "Pastel Lavender": ("#E6E6FA", "#CCCCFF", "#D4D4F5")
        }
        
    def accent_color(self):
        cache_key = ("accent_color", self.current_accent)
        if cache_key not in self._color_cache:
            pal = self.palettes.get(self.current_accent, self.palettes["Pastel Purple"])
            self._color_cache[cache_key] = (pal[0], pal[1])
        return self._color_cache[cache_key]

    def accent_hover(self):
        cache_key = ("accent_hover", self.current_accent)
        if cache_key not in self._color_cache:
            pal = self.palettes.get(self.current_accent, self.palettes["Pastel Purple"])
            self._color_cache[cache_key] = (pal[2], pal[2])
        return self._color_cache[cache_key]

    def accent_text(self):
        # Pastels often look best with dark text in light mode, but white text in dark mode (if dark mode accent is deeper)
        return ("#1A1A1A", "#FFFFFF")
        
    def get_theme_names(self):
        return list(self.palettes.keys())
