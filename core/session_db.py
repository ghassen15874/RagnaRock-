#!/usr/bin/env python3
"""
Session Database Management
"""

import json
import sqlite3
import os
from datetime import datetime

class SessionDatabase:
    def __init__(self, db_path="sessions.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with WAL mode for safe concurrent access (fixes B5)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA foreign_keys=ON')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE,
                    session_type TEXT,
                    target_info TEXT,
                    created_at TEXT,
                    last_seen TEXT,
                    active INTEGER,
                    metadata TEXT,
                    exported INTEGER DEFAULT 0,
                    workspace TEXT DEFAULT 'default'
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workspaces (
                    name TEXT PRIMARY KEY,
                    description TEXT,
                    created_at TEXT
                )
            ''')
            
            # Insert default workspace if it doesn't exist
            cursor.execute('INSERT OR IGNORE INTO workspaces (name, description, created_at) VALUES (?, ?, ?)', 
                           ('default', 'Default Workspace', datetime.now().isoformat()))
            


            cursor.execute('''
                CREATE TABLE IF NOT EXISTS persistence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    method TEXT,
                    configuration TEXT,
                    created_at TEXT,
                    active INTEGER DEFAULT 1,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS hosts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workspace TEXT,
                    ip_address TEXT,
                    mac_address TEXT,
                    os_name TEXT,
                    status TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    UNIQUE(workspace, ip_address)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    host_id INTEGER,
                    port INTEGER,
                    protocol TEXT,
                    name TEXT,
                    state TEXT,
                    info TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    UNIQUE(host_id, port, protocol),
                    FOREIGN KEY (host_id) REFERENCES hosts (id) ON DELETE CASCADE
                )
            ''')
            conn.commit()
            
            # Check if migration is needed (if hosts lacks Foreign Keys)
            cursor.execute("PRAGMA foreign_key_list(hosts)")
            fks = cursor.fetchall()
            if not any(fk[2] == 'workspaces' for fk in fks):
                self.migrate_to_v2(conn)
            
    def migrate_to_v2(self, conn):
        """Safely migrate legacy database to new schema with Foreign Keys and workspace isolation."""
        cursor = conn.cursor()
        print("[*] Migrating database to v2 schema...")
        
        # Turn off FKs during migration
        conn.execute('PRAGMA foreign_keys=OFF')
        conn.execute('BEGIN TRANSACTION')
        try:
            # Add missing workspace column to legacy sessions
            try:
                cursor.execute('ALTER TABLE sessions ADD COLUMN workspace TEXT DEFAULT "default"')
            except sqlite3.OperationalError:
                pass
                
            # Ensure all referenced workspaces exist in workspaces table
            cursor.execute('INSERT OR IGNORE INTO workspaces (name, description, created_at) SELECT DISTINCT workspace, "Migrated Workspace", datetime("now") FROM sessions WHERE workspace IS NOT NULL')
            cursor.execute('INSERT OR IGNORE INTO workspaces (name, description, created_at) SELECT DISTINCT workspace, "Migrated Workspace", datetime("now") FROM hosts WHERE workspace IS NOT NULL')
                
            # Copy data to temp tables and rename (to enforce FKs)
            # Sessions migration
            cursor.execute('DROP TABLE IF EXISTS sessions_new')
            cursor.execute('''
                CREATE TABLE sessions_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE,
                    session_type TEXT,
                    target_info TEXT,
                    created_at TEXT,
                    last_seen TEXT,
                    active INTEGER,
                    metadata TEXT,
                    exported INTEGER DEFAULT 0,
                    workspace TEXT DEFAULT 'default',
                    FOREIGN KEY (workspace) REFERENCES workspaces (name) ON DELETE CASCADE
                )
            ''')
            cursor.execute('INSERT INTO sessions_new SELECT * FROM sessions')
            cursor.execute('DROP TABLE sessions')
            cursor.execute('ALTER TABLE sessions_new RENAME TO sessions')

            # Hosts migration
            cursor.execute('DROP TABLE IF EXISTS hosts_new')
            # Fix schema of new table to include FKs
            cursor.execute('''
                CREATE TABLE hosts_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workspace TEXT,
                    ip_address TEXT,
                    mac_address TEXT,
                    os_name TEXT,
                    status TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    UNIQUE(workspace, ip_address),
                    FOREIGN KEY (workspace) REFERENCES workspaces (name) ON DELETE CASCADE
                )
            ''')
            cursor.execute('INSERT INTO hosts_new SELECT * FROM hosts')
            cursor.execute('DROP TABLE hosts')
            cursor.execute('ALTER TABLE hosts_new RENAME TO hosts')

            conn.commit()
            print("[+] Database migration to v2 completed successfully.")
        except Exception as e:
            conn.rollback()
            print(f"[-] Database migration failed: {e}")
            raise
        finally:
            conn.execute('PRAGMA foreign_keys=ON')
            
    def save_session(self, session):
        """Save session to database using context manager (fixes B6)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('PRAGMA journal_mode=WAL')
                conn.execute('''
                    INSERT OR REPLACE INTO sessions
                    (session_id, session_type, target_info, created_at, last_seen, active, metadata, workspace)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session.session_id,
                    session.session_type,
                    session.target_info,
                    session.created_at.isoformat(),
                    session.last_seen.isoformat(),
                    1 if session.active else 0,
                    json.dumps(session.metadata),
                    session.workspace
                ))
                conn.commit()
            return True
        except Exception as e:
            print(f"[-] Database error saving session: {e}")
            return False
    
    def load_sessions(self, workspace='default'):
        """Load sessions from database for a specific workspace."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('PRAGMA journal_mode=WAL')
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM sessions WHERE workspace = ?', (workspace,))
                rows = cursor.fetchall()

            sessions = []
            for row in rows:
                # row structure depends on columns:
                # id(0), session_id(1), session_type(2), target_info(3), created_at(4), last_seen(5), active(6), metadata(7), exported(8), workspace(9)
                session_data = {
                    'session_id': row[1],
                    'type': row[2],
                    'target': row[3],
                    'created_at': row[4],
                    'last_seen': row[5],
                    'active': bool(row[6]),
                    'metadata': json.loads(row[7]) if row[7] else {},
                    'workspace': row[9] if len(row) > 9 else 'default'
                }
                sessions.append(session_data)
            return sessions
        except Exception as e:
            print(f"[-] Failed to load sessions from database: {e}")
            return []
    
    def export_sessions(self, filename="sessions_export.json", workspace='default'):
        """Export sessions to JSON file"""
        try:
            sessions = self.load_sessions(workspace)
            export_data = {
                'export_time': datetime.now().isoformat(),
                'sessions': sessions
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            print(f"[+] Sessions exported to {filename}")
            return True
            
        except Exception as e:
            print(f"[-] Export failed: {e}")
            return False
    
    def import_sessions(self, filename):
        """Import sessions from JSON file with input validation (fixes S3)."""
        REQUIRED_FIELDS = {'session_id', 'type', 'target', 'created_at', 'last_seen', 'active'}
        try:
            with open(filename, 'r') as f:
                import_data = json.load(f)

            if not isinstance(import_data, dict):
                print("[-] Import file has unexpected format (expected JSON object)")
                return False

            sessions = import_data.get('sessions', [])
            if not isinstance(sessions, list):
                print("[-] Import file 'sessions' field is not a list")
                return False

            imported = 0
            skipped = 0
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('PRAGMA journal_mode=WAL')
                cursor = conn.cursor()
                for session_data in sessions:
                    if not isinstance(session_data, dict):
                        skipped += 1
                        continue
                    # Validate required fields
                    if not REQUIRED_FIELDS.issubset(session_data.keys()):
                        missing = REQUIRED_FIELDS - session_data.keys()
                        print(f"[!] Skipping session with missing fields: {missing}")
                        skipped += 1
                        continue
                    # Validate field types
                    if not isinstance(session_data['session_id'], str) or not session_data['session_id']:
                        print(f"[!] Skipping session with invalid session_id")
                        skipped += 1
                        continue
                    cursor.execute('''
                        INSERT OR REPLACE INTO sessions
                        (session_id, session_type, target_info, created_at, last_seen, active, metadata, exported, workspace)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        str(session_data['session_id'])[:128],
                        str(session_data.get('type', 'unknown'))[:64],
                        str(session_data.get('target', ''))[:256],
                        str(session_data['created_at'])[:32],
                        str(session_data['last_seen'])[:32],
                        1 if session_data['active'] else 0,
                        json.dumps(session_data.get('metadata', {})),
                        1,
                        session_data.get('workspace', 'default')
                    ))
                    imported += 1
                conn.commit()

            print(f"[+] Sessions imported from {filename}: {imported} imported, {skipped} skipped")
            return True

        except (json.JSONDecodeError, ValueError) as e:
            print(f"[-] Import file parse error: {e}")
            return False
        except Exception as e:
            print(f"[-] Import failed: {e}")
            return False
    
    def add_persistence(self, session_id, method, configuration):
        """Add persistence method for session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO persistence (session_id, method, configuration, created_at)
            VALUES (?, ?, ?, ?)
        ''', (session_id, method, json.dumps(configuration), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        print(f"[+] Persistence added for session {session_id}: {method}")
    
    def get_persistence_methods(self, session_id):
        """Get persistence methods for session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM persistence WHERE session_id = ? AND active = 1', (session_id,))
        rows = cursor.fetchall()
        
        methods = []
        for row in rows:
            methods.append({
                'method': row[2],
                'configuration': json.loads(row[3]),
                'created_at': row[4]
            })
        
        conn.close()
        conn.close()
        return methods

    def get_workspaces(self):
        """Get list of all workspaces"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT name FROM workspaces')
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"[-] Failed to get workspaces: {e}")
            return ['default']

    def add_workspace(self, name, description=""):
        """Add a new workspace"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO workspaces (name, description, created_at) VALUES (?, ?, ?)',
                               (name, description, datetime.now().isoformat()))
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            print(f"[-] Workspace '{name}' already exists")
            return False
        except Exception as e:
            print(f"[-] Failed to add workspace: {e}")
            return False

    def delete_workspace(self, name):
        """Delete a workspace and its associated sessions, hosts, and services"""
        if name == 'default':
            print("[-] Cannot delete default workspace")
            return False
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM workspaces WHERE name = ?', (name,))
                cursor.execute('DELETE FROM sessions WHERE workspace = ?', (name,))
                
                # Delete hosts in workspace (cascades to services because of ON DELETE CASCADE, if pragma foreign_keys=ON is set on the connection doing the delete)
                # Ensure foreign_keys pragma is enabled for this connection
                conn.execute('PRAGMA foreign_keys=ON')
                cursor.execute('DELETE FROM hosts WHERE workspace = ?', (name,))
                
                conn.commit()
            return True
        except Exception as e:
            print(f"[-] Failed to delete workspace: {e}")
            return False

    def add_host(self, workspace, ip_address, status='alive', os_name=None, mac_address=None):
        """Add or update a host"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                cursor.execute('''
                    INSERT INTO hosts (workspace, ip_address, status, os_name, mac_address, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(workspace, ip_address) DO UPDATE SET
                        status = excluded.status,
                        os_name = coalesce(excluded.os_name, hosts.os_name),
                        mac_address = coalesce(excluded.mac_address, hosts.mac_address),
                        updated_at = excluded.updated_at
                ''', (workspace, ip_address, status, os_name, mac_address, now, now))
                conn.commit()
                # Return the host id
                cursor.execute('SELECT id FROM hosts WHERE workspace = ? AND ip_address = ?', (workspace, ip_address))
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"[-] Failed to add/update host: {e}")
            return None

    def add_service(self, host_id, port, protocol='tcp', name=None, state='open', info=None):
        """Add or update a service on a host"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                cursor.execute('''
                    INSERT INTO services (host_id, port, protocol, name, state, info, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(host_id, port, protocol) DO UPDATE SET
                        name = coalesce(excluded.name, services.name),
                        state = excluded.state,
                        info = coalesce(excluded.info, services.info),
                        updated_at = excluded.updated_at
                ''', (host_id, port, protocol, name, state, info, now, now))
                conn.commit()
            return True
        except Exception as e:
            print(f"[-] Failed to add/update service: {e}")
            return False

    def get_hosts(self, workspace):
        """Get all hosts for a workspace"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM hosts WHERE workspace = ?', (workspace,))
                return cursor.fetchall()
        except Exception as e:
            print(f"[-] Failed to get hosts: {e}")
            return []
            
    def get_services(self, host_id):
        """Get all services for a host"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM services WHERE host_id = ?', (host_id,))
                return cursor.fetchall()
        except Exception as e:
            print(f"[-] Failed to get services: {e}")
            return []

    def deactivate_session(self, session_id):
        """Mark a session as inactive in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('PRAGMA journal_mode=WAL')
                conn.execute('UPDATE sessions SET active = 0 WHERE session_id = ?', (session_id,))
                conn.commit()
            return True
        except Exception as e:
            print(f"[-] Failed to deactivate session {session_id}: {e}")
            return False

    def deactivate_all_sessions(self):
        """Mark all sessions as inactive in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('PRAGMA journal_mode=WAL')
                conn.execute('UPDATE sessions SET active = 0')
                conn.commit()
            return True
        except Exception as e:
            print(f"[-] Failed to deactivate all sessions: {e}")
            return False

    def clean_database(self):
        """Remove inactive sessions from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count before cleanup
        cursor.execute('SELECT COUNT(*) FROM sessions WHERE active = 0')
        inactive_count = cursor.fetchone()[0]
        
        # Delete inactive sessions
        cursor.execute('DELETE FROM sessions WHERE active = 0')
        
        # Also clean up orphaned persistence entries
        cursor.execute('''
            DELETE FROM persistence 
            WHERE session_id NOT IN (SELECT session_id FROM sessions)
        ''')
        
        conn.commit()
        conn.close()
        
        print(f"[+] Database cleaned: removed {inactive_count} inactive sessions")
        return inactive_count

    def reset_database(self):
        """Reset entire database (DANGEROUS - use with caution)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count records before reset
        cursor.execute('SELECT COUNT(*) FROM sessions')
        session_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM persistence')
        persistence_count = cursor.fetchone()[0]
        
        # Reset tables
        cursor.execute('DELETE FROM sessions')
        cursor.execute('DELETE FROM persistence')
        
        # Reset autoincrement counters
        cursor.execute('DELETE FROM sqlite_sequence WHERE name IN ("sessions", "persistence")')
        
        conn.commit()
        conn.close()
        
        print(f"[+] Database reset: removed {session_count} sessions and {persistence_count} persistence entries")
        return session_count + persistence_count

    def get_database_stats(self):
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Session statistics
        cursor.execute('SELECT COUNT(*) FROM sessions')
        total_sessions = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM sessions WHERE active = 1')
        active_sessions = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM sessions WHERE active = 0')
        inactive_sessions = cursor.fetchone()[0]
        
        # Persistence statistics
        cursor.execute('SELECT COUNT(*) FROM persistence')
        total_persistence = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM persistence WHERE active = 1')
        active_persistence = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'inactive_sessions': inactive_sessions,
            'total_persistence': total_persistence,
            'active_persistence': active_persistence
        }