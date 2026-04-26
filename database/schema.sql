-- database/schema.sql

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    encrypted_password TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    login_duration INTEGER DEFAULT 0,  -- In minutes
    is_system_password BOOLEAN DEFAULT 0,
    system_password_expires_at TIMESTAMP,
    recovery_email TEXT,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    is_disabled BOOLEAN DEFAULT 0,
    recent_login_duration INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    code TEXT,
    description TEXT,
    category TEXT DEFAULT 'Major',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    name TEXT,
    description TEXT NOT NULL,
    deadline TEXT,
    status TEXT DEFAULT 'pending',
    priority TEXT DEFAULT 'Medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);

-- Note: Admin login can be pre-configured by inserting it directly.
-- INSERT OR IGNORE INTO users (username, encrypted_password, is_admin) VALUES ('admin', 'admin_encrypted_pw', 1);
