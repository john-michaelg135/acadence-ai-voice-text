import sqlite3
import os
import datetime
import threading
import sys
from typing import Dict, List, Optional, Tuple
from utils.security import hash_password, verify_password, encrypt_data, decrypt_data, generate_system_password
from utils.logger import logger

if getattr(sys, 'frozen', False):
    # Running as compiled executable
    application_path = os.path.dirname(sys.executable)
    bundle_dir = getattr(sys, '_MEIPASS', application_path)
else:
    # Running as a script
    application_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bundle_dir = application_path

db_dir = os.path.join(application_path, 'database')
if not os.path.exists(db_dir):
    os.makedirs(db_dir)

DB_PATH = os.path.join(db_dir, 'acadence.db')
SCHEMA_PATH = os.path.join(bundle_dir, 'database', 'schema.sql')

class DatabaseManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseManager, cls).__new__(cls)
                    cls._instance._conn = None
                    cls._instance._db_lock = threading.RLock()
                    cls._instance.init_db()
        return cls._instance

    def get_connection(self) -> sqlite3.Connection:
        """Returns a persistent shared connection with thread safety enabled."""
        if self._conn is None:
            # check_same_thread=True re-enables thread safety checks
            self._conn = sqlite3.connect(DB_PATH, check_same_thread=True, timeout=30.0)
        return self._conn

    def init_db(self):
        """Initializes the database schema if it doesn't exist."""
        if not os.path.exists(DB_PATH):
            try:
                with self._db_lock:
                    with self.get_connection() as conn:
                        with open(SCHEMA_PATH, 'r') as f:
                            conn.executescript(f.read())
                
                # Generate secure random admin password
                admin_password = generate_system_password(16)
                self.create_user('admin', admin_password, is_admin=True, is_system_password=True)
                
                # Save credentials to secure file
                admin_creds_file = os.path.join(db_dir, '.admin_credentials')
                with open(admin_creds_file, 'w') as f:
                    f.write(f"ADMIN_USERNAME=admin\nADMIN_PASSWORD={admin_password}\nGENERATED_AT={datetime.datetime.now()}\n")
                
                # Set file permissions to owner-only (Unix-like systems)
                try:
                    os.chmod(admin_creds_file, 0o600)
                except Exception:
                    pass  # Windows doesn't support chmod the same way
                
                logger.info(f"Database initialized. Admin credentials saved to {admin_creds_file}")
            except Exception as e:
                logger.error(f"Database initialization failed: {e}", exc_info=True)
                raise
            
        # Ensure schema migrations for existing DB
        with self._db_lock:
            try:
                with self.get_connection() as conn:
                    migrations = [
                        ("ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0", "failed_login_attempts"),
                        ("ALTER TABLE users ADD COLUMN locked_until TIMESTAMP", "locked_until"),
                        ("ALTER TABLE users ADD COLUMN is_disabled BOOLEAN DEFAULT 0", "is_disabled"),
                        ("ALTER TABLE users ADD COLUMN recent_login_duration INTEGER DEFAULT 0", "recent_login_duration"),
                        ("ALTER TABLE users ADD COLUMN has_seen_walkthrough BOOLEAN DEFAULT 0", "has_seen_walkthrough"),
                        ("ALTER TABLE tasks ADD COLUMN completed_at TIMESTAMP", "completed_at"),
                    ]
                    
                    for migration_sql, description in migrations:
                        try:
                            conn.execute(migration_sql)
                        except sqlite3.OperationalError as e:
                            if "already exists" in str(e):
                                logger.debug(f"Migration already applied: {description}")
                            else:
                                logger.warning(f"Migration skipped for {description}: {e}")
                    
                    # Performance Indexes
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_subjects_user ON subjects(user_id)")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_subject ON tasks(subject_id)")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)")
            except Exception as e:
                logger.error(f"Database migration failed: {e}", exc_info=True)
                raise

    def create_user(self, username: str, password: str, recovery_email: Optional[str] = None, is_system_password: bool = False, is_admin: bool = False) -> bool:
        """Creates a new user and hashes their password."""
        hashed_pw = hash_password(password)
        expires_at = None
        
        if is_system_password:
            expires_at = datetime.datetime.now() + datetime.timedelta(days=14)
            
        enc_email = encrypt_data(recovery_email) if recovery_email else None
            
        try:
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with self._db_lock:
                with self.get_connection() as conn:
                    conn.execute(
                        '''INSERT INTO users 
                           (username, encrypted_password, is_admin, is_system_password, system_password_expires_at, recovery_email, created_at, is_disabled) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, 0)''',
                        (username, hashed_pw, is_admin, is_system_password, expires_at, enc_email, now_str)
                    )
            logger.info(f"User created: {username}")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Failed to create user {username}: username already exists")
            return False  # Username exists
        except Exception as e:
            logger.error(f"Error creating user {username}: {e}", exc_info=True)
            raise

    def get_user(self, username: str) -> Optional[Dict]:
        """Fetches user details by username."""
        with self._db_lock:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("SELECT * FROM users WHERE username = ?", (username,))
                row = cur.fetchone()  # Call fetchone() ONCE
                return dict(row) if row else None
            
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Fetches user details by username (alternative method with same implementation)."""
        with self._db_lock:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("SELECT * FROM users WHERE username = ?", (username,))
                row = cur.fetchone()  # Call fetchone() ONCE
                return dict(row) if row else None

    # Precomputed dummy hash for timing-attack prevention (computed once at class load)
    _DUMMY_HASH = hash_password("dummy_password_that_will_not_match")

    def authenticate_user(self, username: str, password: str) -> Tuple[Optional[Dict], str]:
        """Returns (user_dict, error_msg). Uses constant-time comparison to prevent timing attacks."""
        with self._db_lock:
            user = self.get_user_by_username(username)
            
            # Always verify password to prevent timing-based user enumeration
            if user:
                pwd_match = verify_password(password, user['encrypted_password'])
            else:
                # Verify against dummy hash to maintain constant time
                verify_password(password, self._DUMMY_HASH)
                return None, "Invalid username or password."
                
            if user.get('is_disabled'):
                return None, "Your account has been disabled by an administrator."
                
            now = datetime.datetime.now()
            
            # Check if locked
            if user.get('locked_until'):
                locked_until = datetime.datetime.strptime(user['locked_until'], "%Y-%m-%d %H:%M:%S")
                if now < locked_until:
                    diff = locked_until - now
                    mins = int(diff.total_seconds() / 60) + 1
                    logger.warning(f"Login attempt for locked account: {username}")
                    return None, f"Account locked due to too many failed attempts.\nPlease try again in {mins} minute(s)."
            
            # Verify password using bcrypt hash
            if pwd_match:
                # Success, reset attempts
                with self.get_connection() as conn:
                    conn.execute("UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE id = ?", (user['id'],))
                self.update_last_login(user['id'])
                user_dict = dict(user)
                user_dict['failed_login_attempts'] = 0
                user_dict['locked_until'] = None
                logger.info(f"User authenticated: {username}")
                return user_dict, ""
            else:
                # Failed
                attempts = user.get('failed_login_attempts', 0) + 1
                locked_until_str = None
                
                if attempts >= 5:
                    locked_until_dt = now + datetime.timedelta(minutes=30)
                    locked_until_str = locked_until_dt.strftime("%Y-%m-%d %H:%M:%S")
                    msg = "5 failed attempts. Account locked for 30 minutes."
                    logger.warning(f"Account locked (5 attempts): {username}")
                elif attempts == 3:
                    locked_until_dt = now + datetime.timedelta(minutes=15)
                    locked_until_str = locked_until_dt.strftime("%Y-%m-%d %H:%M:%S")
                    msg = "3 failed attempts. Account locked for 15 minutes."
                    logger.warning(f"Account will lock soon (3 attempts): {username}")
                else:
                    msg = "Invalid username or password."
                    
                with self.get_connection() as conn:
                    conn.execute("UPDATE users SET failed_login_attempts = ?, locked_until = ? WHERE id = ?", (attempts, locked_until_str, user['id']))
                    
                return None, msg

    def update_last_login(self, user_id: int) -> None:
        with self._db_lock:
            with self.get_connection() as conn:
                now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn.execute("UPDATE users SET last_login = ? WHERE id = ?", (now_str, user_id))

    def update_login_duration(self, user_id: int, duration_minutes: int) -> None:
        with self._db_lock:
            with self.get_connection() as conn:
                conn.execute("UPDATE users SET login_duration = login_duration + ?, recent_login_duration = ? WHERE id = ?", (duration_minutes, duration_minutes, user_id))

    def mark_walkthrough_seen(self, user_id: int) -> None:
        with self._db_lock:
            with self.get_connection() as conn:
                conn.execute("UPDATE users SET has_seen_walkthrough = 1 WHERE id = ?", (user_id,))

    def disable_user(self, user_id: int) -> None:
        with self._db_lock:
            with self.get_connection() as conn:
                conn.execute("UPDATE users SET is_disabled = 1 WHERE id = ?", (user_id,))
                logger.info(f"User disabled: {user_id}")

    def enable_user(self, user_id: int) -> None:
        with self._db_lock:
            with self.get_connection() as conn:
                conn.execute("UPDATE users SET is_disabled = 0 WHERE id = ?", (user_id,))
                logger.info(f"User enabled: {user_id}")

    def delete_user(self, user_id: int) -> None:
        with self._db_lock:
            with self.get_connection() as conn:
                # Delete tasks for this user's subjects
                conn.execute("DELETE FROM tasks WHERE subject_id IN (SELECT id FROM subjects WHERE user_id = ?)", (user_id,))
                # Delete subjects
                conn.execute("DELETE FROM subjects WHERE user_id = ?", (user_id,))
                # Delete user
                conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
                logger.info(f"User deleted: {user_id}")

    def get_all_users_for_admin(self) -> List[Dict]:
        with self._db_lock:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute('''
                    SELECT u.id, u.username, u.created_at, u.last_login, u.login_duration, u.recent_login_duration, u.is_disabled,
                           (SELECT COUNT(*) FROM subjects s WHERE s.user_id = u.id) as total_subjects,
                           (SELECT COUNT(*) FROM tasks t JOIN subjects s ON t.subject_id = s.id WHERE s.user_id = u.id) as total_tasks
                    FROM users u
                    WHERE u.is_admin = 0
                ''')
                return [dict(row) for row in cur.fetchall()]

    def change_password(self, username: str, current_password: str, new_password: str, is_system: bool = False) -> Tuple[bool, str]:
        """Changes the user's password securely by verifying the current one first per OAuth best practices."""
        with self._db_lock:
            user = self.get_user_by_username(username)
            if not user or not verify_password(current_password, user['encrypted_password']):
                logger.warning(f"Password change failed for {username}: invalid current password")
                return False, "Invalid current password."
                
            hashed_pw = hash_password(new_password)
            expires_at = (datetime.datetime.now() + datetime.timedelta(days=14)) if is_system else None
            
            with self.get_connection() as conn:
                conn.execute(
                    "UPDATE users SET encrypted_password = ?, is_system_password = ?, system_password_expires_at = ? WHERE username = ?",
                    (hashed_pw, is_system, expires_at, username)
                )
            logger.info(f"Password changed for user: {username}")
            return True, "Password updated successfully."
        
    def admin_reset_password(self, username: str, new_password: str, is_system: bool = False) -> bool:
        """Forces a password update unconditionally (used specifically after secure OTP validation flows)."""
        with self._db_lock:
            hashed_pw = hash_password(new_password)
            expires_at = (datetime.datetime.now() + datetime.timedelta(days=14)) if is_system else None
            
            with self.get_connection() as conn:
                conn.execute(
                    "UPDATE users SET encrypted_password = ?, is_system_password = ?, system_password_expires_at = ? WHERE username = ?",
                    (hashed_pw, is_system, expires_at, username)
                )
            logger.info(f"Password reset by admin for: {username}")
            return True

    def recover_password(self, username: str, recovery_email: str) -> bool:
        # Decode and check email 
        with self._db_lock:
            user = self.get_user_by_username(username)
            if user and user['recovery_email']:
                dec_email = decrypt_data(user['recovery_email'])
                if dec_email == recovery_email:
                    return True
            return False

    # --- Subjects and Tasks CRUD ---
    def get_subjects(self, user_id: int) -> List[Dict]:
        with self._db_lock:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("SELECT * FROM subjects WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
                return [dict(row) for row in cur.fetchall()]

    def add_subject(self, user_id: int, name: str, code: str = '', description: str = '', category: str = 'Major') -> None:
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._db_lock:
            with self.get_connection() as conn:
                conn.execute(
                    "INSERT INTO subjects (user_id, name, code, description, category, created_at) VALUES (?, ?, ?, ?, ?, ?)", 
                    (user_id, name, code, description, category, now_str)
                )

    def update_subject(self, subject_id: int, name: str, code: str, description: str, category: str) -> None:
        with self._db_lock:
            with self.get_connection() as conn:
                conn.execute(
                    "UPDATE subjects SET name = ?, code = ?, description = ?, category = ? WHERE id = ?",
                    (name, code, description, category, subject_id)
                )
            
    def delete_subject(self, subject_id: int) -> None:
        with self._db_lock:
            with self.get_connection() as conn:
                # Delete associated tasks from database
                conn.execute("DELETE FROM tasks WHERE subject_id = ?", (subject_id,))
                # Delete subject
                conn.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))

    def get_tasks(self, subject_id: int) -> List[Dict]:
        with self._db_lock:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("SELECT * FROM tasks WHERE subject_id = ? ORDER BY created_at DESC", (subject_id,))
                return [dict(row) for row in cur.fetchall()]

    def add_task(self, subject_id: int, name: str, description: str, deadline: str = '', status: str = 'pending', priority: str = 'Medium') -> None:
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._db_lock:
            with self.get_connection() as conn:
                conn.execute("INSERT INTO tasks (subject_id, name, description, deadline, status, priority, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                             (subject_id, name, description, deadline, status, priority, now_str))
                         
    def delete_task(self, task_id: int) -> None:
        with self._db_lock:
            with self.get_connection() as conn:
                conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            
    def update_task_status(self, task_id: int, status: str) -> None:
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") if status == 'completed' else None
        with self._db_lock:
            with self.get_connection() as conn:
                conn.execute("UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?", (status, now_str, task_id))

    def update_task(self, task_id: int, name: str, description: str, deadline: str, priority: str) -> None:
        with self._db_lock:
            with self.get_connection() as conn:
                conn.execute(
                    "UPDATE tasks SET name = ?, description = ?, deadline = ?, priority = ? WHERE id = ?",
                    (name, description, deadline, priority, task_id)
                )

    def get_completed_tasks(self, user_id: int, limit: Optional[int] = None) -> List[Dict]:
        with self._db_lock:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                
                if limit is not None:
                    limit = max(1, int(limit))  # Validate and ensure positive
                    query = """
                        SELECT t.*, s.name as subject_name 
                        FROM tasks t 
                        JOIN subjects s ON t.subject_id = s.id 
                        WHERE s.user_id = ? AND t.status = 'completed' 
                        ORDER BY IFNULL(t.completed_at, t.created_at) DESC
                        LIMIT ?
                    """
                    cur.execute(query, (user_id, limit))
                else:
                    query = """
                        SELECT t.*, s.name as subject_name 
                        FROM tasks t 
                        JOIN subjects s ON t.subject_id = s.id 
                        WHERE s.user_id = ? AND t.status = 'completed' 
                        ORDER BY IFNULL(t.completed_at, t.created_at) DESC
                    """
                    cur.execute(query, (user_id,))
                
                return [dict(row) for row in cur.fetchall()]

    def get_completed_tasks_by_subject(self, user_id: int) -> List[Dict]:
        with self._db_lock:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("""
                    SELECT s.name, COUNT(t.id) as count 
                    FROM subjects s 
                    LEFT JOIN tasks t ON s.id = t.subject_id AND t.status='completed' 
                    WHERE s.user_id = ? 
                    GROUP BY s.id
                """, (user_id,))
                return [dict(row) for row in cur.fetchall()]

    def get_pending_tasks_by_priority(self, user_id: int, priority: str, limit: Optional[int] = None) -> List[Dict]:
        with self._db_lock:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                
                if limit is not None:
                    limit = max(1, int(limit))  # Validate and ensure positive
                    query = """
                        SELECT t.*, s.name as subject_name 
                        FROM tasks t 
                        JOIN subjects s ON t.subject_id = s.id 
                        WHERE s.user_id = ? AND t.status = 'pending' AND t.priority = ?
                        ORDER BY t.created_at DESC
                        LIMIT ?
                    """
                    cur.execute(query, (user_id, priority, limit))
                else:
                    query = """
                        SELECT t.*, s.name as subject_name 
                        FROM tasks t 
                        JOIN subjects s ON t.subject_id = s.id 
                        WHERE s.user_id = ? AND t.status = 'pending' AND t.priority = ?
                        ORDER BY t.created_at DESC
                    """
                    cur.execute(query, (user_id, priority))
                
                return [dict(row) for row in cur.fetchall()]
            
    def get_all_pending_tasks(self, user_id: int) -> List[Dict]:
        with self._db_lock:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                query = """
                    SELECT t.*, s.name as subject_name 
                    FROM tasks t 
                    JOIN subjects s ON t.subject_id = s.id 
                    WHERE s.user_id = ? AND t.status = 'pending'
                    ORDER BY CASE t.priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END, t.created_at DESC
                """
                cur.execute(query, (user_id,))
                return [dict(row) for row in cur.fetchall()]

    # --- Dashboard Metrics ---
    def get_dashboard_metrics(self, user_id: int) -> Dict:
        """Efficiently retrieves all dashboard metrics in a single optimized query."""
        with self._db_lock:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                
                # Single query with aggregates — avoids multiple DB round trips
                cur.execute("""
                    SELECT s.id, s.name, s.category,
                           COUNT(DISTINCT t.id) as task_count,
                           SUM(CASE WHEN t.status = 'pending' THEN 1 ELSE 0 END) as pending_task_count,
                           SUM(CASE WHEN t.status = 'pending' AND t.priority = 'High' THEN 1 ELSE 0 END) as high_priority_count
                    FROM subjects s
                    LEFT JOIN tasks t ON s.id = t.subject_id
                    WHERE s.user_id = ?
                    GROUP BY s.id
                    ORDER BY s.created_at DESC
                """, (user_id,))
                subjects = [dict(row) for row in cur.fetchall()]
                
                # Compute totals from the single result set
                total_subjects = len(subjects)
                total_pending_tasks = sum(s['pending_task_count'] or 0 for s in subjects)
                high_priority_count = sum(s['high_priority_count'] or 0 for s in subjects)
                
                return {
                    "total_subjects": total_subjects,
                    "total_pending_tasks": total_pending_tasks,
                    "high_priority_count": high_priority_count,
                    "subjects": subjects
                }
