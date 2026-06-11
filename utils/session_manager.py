import os
import json

SESSION_FILE = "session.json"

_DEFAULT_NOTIFICATION_SETTINGS = {
    "enabled": True,
    "persistent": True,
    "group_notifications": False,
    "high_advance_days": 2,    # Notify 2 days before, 1 day before, due today, overdue
    "medium_advance_days": 1,  # Notify 1 day before, due today, overdue
    "low_advance_days": 0,     # Notify due today + overdue only
}

def _read_session_data():
    """Reads the full session JSON, returns empty dict on failure."""
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _write_session_data(data):
    """Writes the full session JSON."""
    try:
        with open(SESSION_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def save_session(username):
    data = _read_session_data()
    data["username"] = username
    _write_session_data(data)

def get_session():
    data = _read_session_data()
    return data.get("username")

def clear_session():
    data = _read_session_data()
    if "username" in data:
        del data["username"]
        _write_session_data(data)

def save_notification_settings(settings: dict, user_id: int = None):
    """Saves notification preference settings to the database (per-user) and session file."""
    # Always save to session file for the current session
    data = _read_session_data()
    data["notification_settings"] = settings
    _write_session_data(data)
    
    # Persist to database so settings survive logout/login
    if user_id:
        try:
            from database.db_manager import DatabaseManager
            db = DatabaseManager()
            db.save_notification_preferences(user_id, settings)
        except Exception:
            pass

def get_notification_settings(user_id: int = None) -> dict:
    """Returns notification settings with defaults for any missing keys.
    Loads from database first (per-user persistent), falls back to session file."""
    saved = {}
    
    # Try loading from database first (per-user persistent storage)
    if user_id:
        try:
            from database.db_manager import DatabaseManager
            db = DatabaseManager()
            db_prefs = db.get_notification_preferences(user_id)
            if db_prefs:
                saved = db_prefs
        except Exception:
            pass
    
    # Fallback to session file if database had nothing
    if not saved:
        data = _read_session_data()
        saved = data.get("notification_settings", {})
    
    # Merge with defaults so new keys are always present
    result = dict(_DEFAULT_NOTIFICATION_SETTINGS)
    result.update(saved)
    return result

_DEFAULT_THEME_SETTINGS = {
    "appearance_mode": "Light",
    "accent_color": "Pastel Purple"
}

def save_theme_settings(settings: dict, user_id: int = None):
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

def get_theme_settings(user_id: int = None) -> dict:
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
    result.update(saved)
    return result
