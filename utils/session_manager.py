import os
import json
import logging
import tempfile

_logger = logging.getLogger(__name__)

SESSION_FILE = "session.json"

_DEFAULT_NOTIFICATION_SETTINGS = {
    "enabled": True,
    "persistent": True,
    "group_notifications": False,
    "high_advance_days": 2,
    "medium_advance_days": 1,
    "low_advance_days": 0,
}


def _read_session_data():
    """Reads the full session JSON, returns empty dict on failure."""
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            _logger.warning("Unable to read session settings", exc_info=True)
            return {}
    return {}


def _write_session_data(data):
    """Atomically replace session JSON; preserve the previous file on failure."""
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=os.path.dirname(os.path.abspath(SESSION_FILE)),
            prefix=".session-",
            suffix=".tmp",
            delete=False,
        ) as f:
            temporary_path = f.name
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary_path, SESSION_FILE)
    except (OSError, TypeError, ValueError):
        _logger.warning("Unable to save session settings", exc_info=True)
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)


def save_session(username):
    data = _read_session_data()
    data["username"] = username
    _write_session_data(data)


def get_session():
    data = _read_session_data()
    username = data.get("username")
    return username if isinstance(username, str) and username else None


def clear_session():
    data = _read_session_data()
    if "username" in data:
        del data["username"]
        _write_session_data(data)


def save_notification_settings(settings: dict, user_id: int | None = None):
    """Saves notification preference settings to the database (per-user) and session file."""

    data = _read_session_data()
    data["notification_settings"] = settings
    _write_session_data(data)

    if user_id:
        try:
            from database.db_manager import DatabaseManager

            db = DatabaseManager()
            db.save_notification_preferences(user_id, settings)
        except Exception:
            pass


def get_notification_settings(user_id: int | None = None) -> dict:
    """Returns notification settings with defaults for any missing keys.
    Loads from database first (per-user persistent), falls back to session file."""
    saved = {}

    if user_id:
        try:
            from database.db_manager import DatabaseManager

            db = DatabaseManager()
            db_prefs = db.get_notification_preferences(user_id)
            if db_prefs:
                saved = db_prefs
        except Exception:
            pass

    if not saved:
        data = _read_session_data()
        saved = data.get("notification_settings", {})

    result = dict(_DEFAULT_NOTIFICATION_SETTINGS)
    if isinstance(saved, dict):
        result.update(saved)
    return result


_DEFAULT_THEME_SETTINGS = {"appearance_mode": "Light", "accent_color": "Pastel Purple"}


def save_theme_settings(settings: dict, user_id: int | None = None):
    """Saves theme preference settings to the database (per-user) and session file."""
    data = _read_session_data()
    data["theme_settings"] = settings
    _write_session_data(data)

    if user_id:
        try:
            from database.db_manager import DatabaseManager

            db = DatabaseManager()
            db.save_theme_preferences(user_id, settings)
        except Exception:
            pass


def get_theme_settings(user_id: int | None = None) -> dict:
    """Returns theme settings with defaults for any missing keys.
    Loads from database first (per-user persistent), falls back to session file."""
    saved = {}

    if user_id:
        try:
            from database.db_manager import DatabaseManager

            db = DatabaseManager()
            db_prefs = db.get_theme_preferences(user_id)
            if db_prefs:
                saved = db_prefs
        except Exception:
            pass

    if not saved:
        data = _read_session_data()
        saved = data.get("theme_settings", {})

    result = dict(_DEFAULT_THEME_SETTINGS)
    if isinstance(saved, dict):
        result.update(saved)
    return result
