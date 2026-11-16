import os
import ctypes
import sys
import pathlib
from utils.logger import logger


def load_fonts():
    """
    Loads custom fonts from the assets/fonts directory so they can be used in the app.
    Supports Windows only for now as per user OS version.
    Uses pathlib for safe path handling and validates against path traversal.
    """
    if sys.platform != "win32":
        return

    if getattr(sys, "frozen", False):
        bundle_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        bundle_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    font_dir_path = pathlib.Path(bundle_dir, "assets", "fonts")

    if not font_dir_path.exists():
        logger.warning(f"Font directory not found: {font_dir_path}")
        return

    count = 0
    for font_file in font_dir_path.iterdir():
        if font_file.suffix.lower() == ".ttf" and font_file.is_file():
            try:
                font_file.resolve().relative_to(font_dir_path.resolve())
            except ValueError:
                logger.warning(f"Font file outside safe directory, skipping: {font_file.name}")
                continue

            # FR_PRIVATE (0x10) means font is only available to this process
            try:
                res = ctypes.windll.gdi32.AddFontResourceExW(str(font_file), 0x10, 0)
                if res:
                    count += 1
            except Exception as e:
                logger.error(f"Error loading font {font_file.name}: {e}")

    logger.info(f"Successfully loaded {count} custom fonts.")
