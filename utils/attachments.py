import os
import re
import tempfile
from pathlib import Path

from database.db_manager import db_dir


def save_ai_attachment(task_id: int, task_name: str, content: str) -> str:
    """Atomically save UTF-8 guidance for a task and return its absolute path.

    Creates the attachment directory. Raises OSError on write or replacement failure;
    an existing attachment remains intact until the replacement is complete.
    """
    directory = Path(db_dir) / "attachments"
    directory.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^\w\s-]", "", task_name).strip().replace(" ", "_")[:60]
    destination = directory / f"{task_id}_{safe_name}_AI_Aid.txt"
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=directory, delete=False
        ) as stream:
            temporary_path = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, destination)
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()
    return str(destination.resolve())
