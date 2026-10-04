import unittest
import sqlite3
import os
import threading
from core.session_db import SessionDatabase

class TestDatabaseMigrationAndRecovery(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_migration.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            
    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            
    def test_migrate_to_v2_from_v1(self):
        # 1. Create a V1 database (legacy, without Foreign Keys on workspace)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE,
                    session_type TEXT,
                    target_info TEXT,
                    created_at TEXT,
                    last_seen TEXT,
                    active INTEGER,
                    metadata TEXT,
                    exported INTEGER DEFAULT 0
                    -- No workspace column!
                )
            ''')
            
            conn.execute('''
                CREATE TABLE hosts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workspace TEXT,
                    ip_address TEXT,
                    mac_address TEXT,
                    os_name TEXT,
                    status TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    UNIQUE(workspace, ip_address)
                    -- No foreign key!
                )
            ''')
            
            # Insert some data
            conn.execute("INSERT INTO sessions (session_id, session_type, target_info) VALUES ('sess1', 'ssh', '1.1.1.1')")
            conn.execute("INSERT INTO hosts (workspace, ip_address, status) VALUES ('legacy_ws', '2.2.2.2', 'up')")
            conn.commit()
            
        # 2. Trigger migration by initializing SessionDatabase
        db = SessionDatabase(self.db_path)
        
        # 3. Verify data preservation and schema update
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Verify workspace column was added and defaulted to 'default'
            cursor.execute("SELECT workspace FROM sessions WHERE session_id = 'sess1'")
            self.assertEqual(cursor.fetchone()[0], 'default')
            
            # Verify hosts data was preserved
            cursor.execute("SELECT ip_address FROM hosts WHERE workspace = 'legacy_ws'")
            self.assertEqual(cursor.fetchone()[0], '2.2.2.2')
            
            # Verify foreign keys are present
            cursor.execute("PRAGMA foreign_key_list(hosts)")
            fks = cursor.fetchall()
            self.assertTrue(any(fk[2] == 'workspaces' for fk in fks))

    def test_concurrent_writes_wal(self):
        db = SessionDatabase(self.db_path)
        db.add_workspace("concurrent_ws")
        
        def write_host(ip):
            db.add_host("concurrent_ws", ip, "up")
            
        threads = []
        for i in range(10):
            t = threading.Thread(target=write_host, args=(f"10.0.0.{i}",))
            threads.append(t)
            t.start()
            
        for t in threads:
            t.join()
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM hosts WHERE workspace = 'concurrent_ws'")
            self.assertEqual(cursor.fetchone()[0], 10)

if __name__ == '__main__':
    unittest.main()
