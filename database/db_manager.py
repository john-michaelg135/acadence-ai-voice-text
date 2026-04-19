import sqlite3
import os
import datetime
from utils.security import hash_password, verify_password, encrypt_data, decrypt_data

DB_PATH = os.path.join(os.path.dirname(__file__), 'acadence.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')

class DatabaseManager:
    def __init__(self):
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(DB_PATH)

    def init_db(self):
        """Initializes the database schema if it doesn't exist."""
        if not os.path.exists(DB_PATH):
            with self.get_connection() as conn:
                with open(SCHEMA_PATH, 'r') as f:
                    conn.executescript(f.read())
            
            # Insert default admin user if not exists
            self.create_user('admin', 'admin123!', is_admin=True) # Exclamation to pass constraints natively if run manually later

    def create_user(self, username, password, recovery_email=None, is_system_password=False, is_admin=False):
        """Creates a new user and hashes their password."""
        hashed_pw = hash_password(password)
        expires_at = None
        
        if is_system_password:
            expires_at = datetime.datetime.now() + datetime.timedelta(days=14)
            
        enc_email = encrypt_data(recovery_email) if recovery_email else None
            
        try:
            with self.get_connection() as conn:
                conn.execute(
                    '''INSERT INTO users 
                       (username, encrypted_password, is_admin, is_system_password, system_password_expires_at, recovery_email) 
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (username, hashed_pw, is_admin, is_system_password, expires_at, enc_email)
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
        """Returns user dict if valid, otherwise None."""
        user = self.get_user_by_username(username)
        if not user:
            return None
        
        # Verify password using bcrypt hash
        if verify_password(password, user['encrypted_password']):
            self.update_last_login(user['id'])
            return user
        return None

    def update_last_login(self, user_id):
        with self.get_connection() as conn:
            conn.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))

    def get_all_users_for_admin(self):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute('''
                SELECT u.id, u.username, u.created_at, u.last_login, u.login_duration,
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
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO subjects (user_id, name, code, description, category) VALUES (?, ?, ?, ?, ?)", 
                (user_id, name, code, description, category)
            )
            
    def delete_subject(self, subject_id):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))

    def get_tasks(self, subject_id):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM tasks WHERE subject_id = ? ORDER BY created_at DESC", (subject_id,))
            return [dict(row) for row in cur.fetchall()]

    def add_task(self, subject_id, name, description, deadline='', status='pending', priority='Medium'):
        with self.get_connection() as conn:
            conn.execute("INSERT INTO tasks (subject_id, name, description, deadline, status, priority) VALUES (?, ?, ?, ?, ?, ?)",
                         (subject_id, name, description, deadline, status, priority))
                         
    def delete_task(self, task_id):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            
    def update_task_status(self, task_id, status):
        with self.get_connection() as conn:
            conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))

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
