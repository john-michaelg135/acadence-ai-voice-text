"""Keep packaged application data out of read-only installation directories."""

import os
import sys
from pathlib import Path


def data_root():
    if not getattr(sys, "frozen", False):
        return Path(__file__).resolve().parents[1]
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    root = base / "Acadence"
    root.mkdir(parents=True, exist_ok=True)
    return root
