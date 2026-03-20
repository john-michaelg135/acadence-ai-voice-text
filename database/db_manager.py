import sqlite3
import os
import datetime
from utils.security import encrypt_data, decrypt_data, verify_password

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
            self.create_user('admin', 'admin123', is_admin=True)

    def create_user(self, username, password, recovery_email=None, is_system_password=False, is_admin=False):
        """Creates a new user and encrypts their password."""
        encrypted_pw = encrypt_data(password)
        expires_at = None
        
        if is_system_password:
            expires_at = datetime.datetime.now() + datetime.timedelta(days=14)
            
        try:
            with self.get_connection() as conn:
                conn.execute(
                    '''INSERT INTO users 
                       (username, encrypted_password, is_admin, is_system_password, system_password_expires_at, recovery_email) 
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (username, encrypted_pw, is_admin, is_system_password, expires_at, recovery_email)
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
        
        # Verify password
        if verify_password(password, user['encrypted_password']):
            # Update last login
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

    def update_password(self, username, new_password, is_system=False):
        encrypted_pw = encrypt_data(new_password)
        expires_at = (datetime.datetime.now() + datetime.timedelta(days=14)) if is_system else None
        
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE users SET encrypted_password = ?, is_system_password = ?, system_password_expires_at = ? WHERE username = ?",
                (encrypted_pw, is_system, expires_at, username)
            )

    def recover_password(self, username, recovery_email):
        # basic check
        user = self.get_user_by_username(username)
        if user and user['recovery_email'] == recovery_email:
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
