import os
import ctypes
import platform
import pathlib
from utils.logger import logger

def load_fonts():
    """
    Loads custom fonts from the assets/fonts directory so they can be used in the app.
    Supports Windows only for now as per user OS version.
    Uses pathlib for safe path handling and validates against path traversal.
    """
    if platform.system() != "Windows":
        return

    import sys
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        # Running as a script
        bundle_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Path to fonts directory
    font_dir_path = pathlib.Path(bundle_dir, "assets", "fonts")
    
    if not font_dir_path.exists():
        logger.warning(f"Font directory not found: {font_dir_path}")
        return

    # Load all .ttf files in the directory
    count = 0
    for font_file in font_dir_path.iterdir():
        if font_file.suffix.lower() == ".ttf" and font_file.is_file():
            # Verify the file is actually inside the fonts directory (no path traversal)
            try:
                font_file.resolve().relative_to(font_dir_path.resolve())
            except ValueError:
                logger.warning(f"Font file outside safe directory, skipping: {font_file.name}")
                continue
            
            # Using AddFontResourceExW from GDI32 to load font into session
            # FR_PRIVATE (0x10) means font is only available to this process
            # FR_NOT_ENUM (0x20) means font is not enumerable by other processes
            try:
                res = ctypes.windll.gdi32.AddFontResourceExW(str(font_file), 0x10, 0)
                if res:
                    count += 1
            except Exception as e:
                logger.error(f"Error loading font {font_file.name}: {e}")
                
    logger.info(f"Successfully loaded {count} custom fonts.")
