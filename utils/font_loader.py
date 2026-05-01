import os
import ctypes
import platform

def load_fonts():
    """
    Loads custom fonts from the assets/fonts directory so they can be used in the app.
    Supports Windows only for now as per user OS version.
    """
    if platform.system() != "Windows":
        return

    # Path to fonts directory
    font_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "fonts")
    
    if not os.path.exists(font_dir):
        print(f"Font directory not found: {font_dir}")
        return

    # Load all .ttf files in the directory
    count = 0
    for font_file in os.listdir(font_dir):
        if font_file.endswith(".ttf"):
            font_path = os.path.join(font_dir, font_file)
            
            # Using AddFontResourceExW from GDI32 to load font into session
            # FR_PRIVATE (0x10) means font is only available to this process
            # FR_NOT_ENUM (0x20) means font is not enumerable by other processes
            try:
                res = ctypes.windll.gdi32.AddFontResourceExW(font_path, 0x10, 0)
                if res:
                    count += 1
            except Exception as e:
                print(f"Error loading font {font_file}: {e}")
                
    print(f"Successfully loaded {count} custom fonts.")
