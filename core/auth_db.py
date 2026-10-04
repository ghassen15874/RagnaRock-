import sqlite3
import os
import json
from datetime import datetime

class AuthDatabase:
    def __init__(self, db_path="auth.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA foreign_keys=ON')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    workspaces TEXT NOT NULL, -- JSON array of allowed workspaces or "*"
                    created_at TEXT NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS revoked_tokens (
                    jti TEXT PRIMARY KEY,
                    revoked_at TEXT NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS login_attempts (
                    ip TEXT,
                    username TEXT,
                    attempts INTEGER DEFAULT 0,
                    last_attempt TEXT,
                    PRIMARY KEY (ip, username)
                )
            ''')
            conn.commit()

    def add_user(self, username, password_hash, role="Viewer", workspaces=None):
        if workspaces is None:
            workspaces = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO users (username, password_hash, role, workspaces, created_at) VALUES (?, ?, ?, ?, ?)',
                    (username, password_hash, role, json.dumps(workspaces), datetime.now().isoformat())
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False

    def get_user(self, username):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, password_hash, role, workspaces FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'username': row[1],
                    'password_hash': row[2],
                    'role': row[3],
                    'workspaces': json.loads(row[4])
                }
            return None

    def update_user_workspaces(self, username, workspaces):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET workspaces = ? WHERE username = ?', (json.dumps(workspaces), username))
            conn.commit()
            return cursor.rowcount > 0

    def revoke_token(self, jti):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR IGNORE INTO revoked_tokens (jti, revoked_at) VALUES (?, ?)', (jti, datetime.now().isoformat()))
            conn.commit()

    def is_token_revoked(self, jti):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM revoked_tokens WHERE jti = ?', (jti,))
            return cursor.fetchone() is not None

    def record_login_attempt(self, ip, username, success=False):
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if success:
                cursor.execute('DELETE FROM login_attempts WHERE ip = ? AND username = ?', (ip, username))
            else:
                cursor.execute('''
                    INSERT INTO login_attempts (ip, username, attempts, last_attempt) 
                    VALUES (?, ?, 1, ?) 
                    ON CONFLICT(ip, username) 
                    DO UPDATE SET attempts = attempts + 1, last_attempt = ?
                ''', (ip, username, now, now))
            conn.commit()

    def get_login_attempts(self, ip, username):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT attempts, last_attempt FROM login_attempts WHERE ip = ? AND username = ?', (ip, username))
            row = cursor.fetchone()
            if row:
                return row[0], datetime.fromisoformat(row[1])
            return 0, None
