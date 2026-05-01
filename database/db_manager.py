import sqlite3
import os
import datetime
from utils.security import hash_password, verify_password, encrypt_data, decrypt_data

import sys

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
    def __init__(self):
        self._conn = None  # Persistent shared connection
        self.init_db()

    def get_connection(self):
        """Returns a persistent shared connection, creating it once on first call."""
        if self._conn is None:
            self._conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        return self._conn

    def init_db(self):
        """Initializes the database schema if it doesn't exist."""
        if not os.path.exists(DB_PATH):
            with self.get_connection() as conn:
                with open(SCHEMA_PATH, 'r') as f:
                    conn.executescript(f.read())
            
            # Insert default admin user if not exists
            self.create_user('admin', 'admin123!', is_admin=True) # Exclamation to pass constraints natively if run manually later
            
        # Ensure schema migrations for existing DB
        with self.get_connection() as conn:
            try:
                conn.execute("ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0")
                conn.execute("ALTER TABLE users ADD COLUMN locked_until TIMESTAMP")
            except sqlite3.OperationalError:
                pass # Columns already exist
                
            try:
                conn.execute("ALTER TABLE users ADD COLUMN is_disabled BOOLEAN DEFAULT 0")
            except sqlite3.OperationalError:
                pass
                
            try:
                conn.execute("ALTER TABLE users ADD COLUMN recent_login_duration INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass
                
            try:
                conn.execute("ALTER TABLE tasks ADD COLUMN completed_at TIMESTAMP")
            except sqlite3.OperationalError:
                pass

            # Performance Indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_subjects_user ON subjects(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_subject ON tasks(subject_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)")

    def create_user(self, username, password, recovery_email=None, is_system_password=False, is_admin=False):
        """Creates a new user and hashes their password."""
        hashed_pw = hash_password(password)
        expires_at = None
        
        if is_system_password:
            expires_at = datetime.datetime.now() + datetime.timedelta(days=14)
            
        enc_email = encrypt_data(recovery_email) if recovery_email else None
            
        try:
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with self.get_connection() as conn:
                conn.execute(
                    '''INSERT INTO users 
                       (username, encrypted_password, is_admin, is_system_password, system_password_expires_at, recovery_email, created_at, is_disabled) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, 0)''',
                    (username, hashed_pw, is_admin, is_system_password, expires_at, enc_email, now_str)
                )
            return True
        except sqlite3.IntegrityError:
            return False # Username exists

    def get_user(self, username):
        """Fetches user details by username."""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username = ?", (username,))
            return dict(cur.fetchone()) if cur.fetchone() else None
            
    def get_user_by_username(self, username):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cur.fetchone()
            return dict(row) if row else None

    def authenticate_user(self, username, password):
        """Returns (user_dict, error_msg)."""
        user = self.get_user_by_username(username)
        if not user:
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
                return None, f"Account locked due to too many failed attempts.\nPlease try again in {mins} minute(s)."
        
        # Verify password using bcrypt hash
        if verify_password(password, user['encrypted_password']):
            # Success, reset attempts
            with self.get_connection() as conn:
                conn.execute("UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE id = ?", (user['id'],))
            self.update_last_login(user['id'])
            user_dict = dict(user)
            user_dict['failed_login_attempts'] = 0
            user_dict['locked_until'] = None
            return user_dict, ""
        else:
            # Failed
            attempts = user.get('failed_login_attempts', 0) + 1
            locked_until_str = None
            
            if attempts >= 5:
                locked_until_dt = now + datetime.timedelta(minutes=30)
                locked_until_str = locked_until_dt.strftime("%Y-%m-%d %H:%M:%S")
                msg = "5 failed attempts. Account locked for 30 minutes."
            elif attempts == 3:
                locked_until_dt = now + datetime.timedelta(minutes=15)
                locked_until_str = locked_until_dt.strftime("%Y-%m-%d %H:%M:%S")
                msg = "3 failed attempts. Account locked for 15 minutes."
            else:
                msg = "Invalid username or password."
                
            with self.get_connection() as conn:
                conn.execute("UPDATE users SET failed_login_attempts = ?, locked_until = ? WHERE id = ?", (attempts, locked_until_str, user['id']))
                
            return None, msg

    def update_last_login(self, user_id):
        with self.get_connection() as conn:
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute("UPDATE users SET last_login = ? WHERE id = ?", (now_str, user_id))

    def update_login_duration(self, user_id, duration_minutes):
        with self.get_connection() as conn:
            conn.execute("UPDATE users SET login_duration = login_duration + ?, recent_login_duration = ? WHERE id = ?", (duration_minutes, duration_minutes, user_id))

    def disable_user(self, user_id):
        with self.get_connection() as conn:
            conn.execute("UPDATE users SET is_disabled = 1 WHERE id = ?", (user_id,))

    def enable_user(self, user_id):
        with self.get_connection() as conn:
            conn.execute("UPDATE users SET is_disabled = 0 WHERE id = ?", (user_id,))

    def delete_user(self, user_id):
        with self.get_connection() as conn:
            # Delete tasks for this user's subjects
            conn.execute("DELETE FROM tasks WHERE subject_id IN (SELECT id FROM subjects WHERE user_id = ?)", (user_id,))
            # Delete subjects
            conn.execute("DELETE FROM subjects WHERE user_id = ?", (user_id,))
            # Delete user
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))

    def get_all_users_for_admin(self):
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

    def change_password(self, username, current_password, new_password, is_system=False):
        """Changes the user's password securely by verifying the current one first per OAuth best practices."""
        user = self.get_user_by_username(username)
        if not user or not verify_password(current_password, user['encrypted_password']):
            return False, "Invalid current password."
            
        hashed_pw = hash_password(new_password)
        expires_at = (datetime.datetime.now() + datetime.timedelta(days=14)) if is_system else None
        
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE users SET encrypted_password = ?, is_system_password = ?, system_password_expires_at = ? WHERE username = ?",
                (hashed_pw, is_system, expires_at, username)
            )
        return True, "Password updated successfully."
        
    def admin_reset_password(self, username, new_password, is_system=False):
        """Forces a password update unconditionally (used specifically after secure OTP validation flows)."""
        hashed_pw = hash_password(new_password)
        expires_at = (datetime.datetime.now() + datetime.timedelta(days=14)) if is_system else None
        
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE users SET encrypted_password = ?, is_system_password = ?, system_password_expires_at = ? WHERE username = ?",
                (hashed_pw, is_system, expires_at, username)
            )
        return True

    def recover_password(self, username, recovery_email):
        # Decode and check email 
        user = self.get_user_by_username(username)
        if user and user['recovery_email']:
            dec_email = decrypt_data(user['recovery_email'])
            if dec_email == recovery_email:
                return True
        return False

    # --- Subjects and Tasks CRUD ---
    def get_subjects(self, user_id):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM subjects WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            return [dict(row) for row in cur.fetchall()]

    def add_subject(self, user_id, name, code='', description='', category='Major'):
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO subjects (user_id, name, code, description, category, created_at) VALUES (?, ?, ?, ?, ?, ?)", 
                (user_id, name, code, description, category, now_str)
            )

    def update_subject(self, subject_id, name, code, description, category):
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE subjects SET name = ?, code = ?, description = ?, category = ? WHERE id = ?",
                (name, code, description, category, subject_id)
            )
            
    def delete_subject(self, subject_id):
        with self.get_connection() as conn:
            # AC007 Task 3: Remove subject and associated tasks from database.
            conn.execute("DELETE FROM tasks WHERE subject_id = ?", (subject_id,))
            conn.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))

    def get_tasks(self, subject_id):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM tasks WHERE subject_id = ? ORDER BY created_at DESC", (subject_id,))
            return [dict(row) for row in cur.fetchall()]

    def add_task(self, subject_id, name, description, deadline='', status='pending', priority='Medium'):
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.get_connection() as conn:
            conn.execute("INSERT INTO tasks (subject_id, name, description, deadline, status, priority, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                         (subject_id, name, description, deadline, status, priority, now_str))
                         
    def delete_task(self, task_id):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            
    def update_task_status(self, task_id, status):
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") if status == 'completed' else None
        with self.get_connection() as conn:
            conn.execute("UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?", (status, now_str, task_id))

    def update_task(self, task_id, name, description, deadline, priority):
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE tasks SET name = ?, description = ?, deadline = ?, priority = ? WHERE id = ?",
                (name, description, deadline, priority, task_id)
            )

    def get_completed_tasks(self, user_id, limit=None):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            query = """
                SELECT t.*, s.name as subject_name 
                FROM tasks t 
                JOIN subjects s ON t.subject_id = s.id 
                WHERE s.user_id = ? AND t.status = 'completed' 
                ORDER BY IFNULL(t.completed_at, t.created_at) DESC
            """
            if limit:
                query += f" LIMIT {int(limit)}"
            cur.execute(query, (user_id,))
            return [dict(row) for row in cur.fetchall()]

    def get_completed_tasks_by_subject(self, user_id):
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

    def get_pending_tasks_by_priority(self, user_id, priority, limit=None):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            query = """
                SELECT t.*, s.name as subject_name 
                FROM tasks t 
                JOIN subjects s ON t.subject_id = s.id 
                WHERE s.user_id = ? AND t.status = 'pending' AND t.priority = ?
                ORDER BY t.created_at DESC
            """
            if limit:
                query += f" LIMIT {int(limit)}"
            cur.execute(query, (user_id, priority))
            return [dict(row) for row in cur.fetchall()]
            
    def get_all_pending_tasks(self, user_id):
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
    def get_dashboard_metrics(self, user_id):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            # Get subjects with task counts
            cur.execute("""
                SELECT s.id, s.name, s.category,
                       (SELECT COUNT(*) FROM tasks t WHERE t.subject_id = s.id) as task_count,
                       (SELECT COUNT(*) FROM tasks t WHERE t.subject_id = s.id AND t.status = 'pending') as pending_task_count
                FROM subjects s
                WHERE s.user_id = ?
                ORDER BY s.created_at DESC
            """, (user_id,))
            subjects = [dict(row) for row in cur.fetchall()]
            
            # Get high priority task count
            cur.execute("""
                SELECT COUNT(*) as high_priority_count 
                FROM tasks t 
                JOIN subjects s ON t.subject_id = s.id 
                WHERE s.user_id = ? AND t.status = 'pending' AND t.priority = 'High'
            """, (user_id,))
            hp_row = cur.fetchone()
            high_priority_count = hp_row['high_priority_count'] if hp_row else 0
            
            # Totals
            total_subjects = len(subjects)
            total_pending_tasks = sum(s['pending_task_count'] for s in subjects)
            
            return {
                "total_subjects": total_subjects,
                "total_pending_tasks": total_pending_tasks,
                "high_priority_count": high_priority_count,
                "subjects": subjects
            }
