#!/usr/bin/env python3
"""
Tests for HTTPHandler Protocol & Architecture
"""

import unittest
import requests
import json
import time
import socket
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

class TestHTTPHandler(unittest.TestCase):
    def setUp(self):
        # Use an in-memory db or a temp file db for SessionManager
        import tempfile
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        
        from core.session_db import SessionDatabase
        self._orig_init = SessionDatabase.__init__
        tmp_path = self.tmp.name
        def patched_init(self_db, db_path="sessions.db"):
            self._orig_init(self_db, db_path=tmp_path)
        SessionDatabase.__init__ = patched_init
        
        from core.session_manager import SessionManager
        from core.handlers import HTTPHandler
        
        self.sm = SessionManager()
        self.handler = HTTPHandler(self.sm)
        self.port = get_free_port()
        self.host = '127.0.0.1'
        self.base_url = f"http://{self.host}:{self.port}"
        
        self.handler_id = "test_http_1"
        self.handler.start_http_handler(self.host, self.port, self.handler_id, self.sm)
        
        # Give the thread a moment to start the server
        time.sleep(0.5)

    def tearDown(self):
        self.handler.stop_http_handler(self.handler_id)
        
        from core.session_db import SessionDatabase
        SessionDatabase.__init__ = self._orig_init
        for ext in ('', '-wal', '-shm'):
            try:
                os.unlink(self.tmp.name + ext)
            except FileNotFoundError:
                pass

    def test_client_registration(self):
        """Test beacon registration endpoint"""
        sysinfo = {
            "hostname": "test-pc",
            "user": "test-user",
            "pid": 1234,
            "profile": "default"
        }
        resp = requests.post(f"{self.base_url}/register", json=sysinfo)
        self.assertEqual(resp.status_code, 200)
        
        data = resp.json()
        self.assertIn('session_id', data)
        session_id = data['session_id']
        
        # Check if session is tracked by session manager
        session = self.sm.get_session(session_id)
        self.assertIsNotNone(session)
        self.assertEqual(session.metadata['user'], 'test-user')
        self.assertTrue(hasattr(session, 'tasks'))
        self.assertTrue(hasattr(session, 'results'))

    def test_task_polling(self):
        """Test beacon polling for tasks"""
        # Register a beacon first
        resp = requests.post(f"{self.base_url}/register", json={"user": "test"})
        session_id = resp.json()['session_id']
        
        # Add a task manually to the session
        session = self.sm.get_session(session_id)
        task = {"id": "t1", "command": "whoami"}
        session.tasks.append(task)
        
        # Poll for tasks
        resp = requests.get(f"{self.base_url}/tasks/{session_id}")
        self.assertEqual(resp.status_code, 200)
        
        data = resp.json()
        self.assertIn('tasks', data)
        self.assertEqual(len(data['tasks']), 1)
        self.assertEqual(data['tasks'][0]['command'], "whoami")
        
        # Ensure task was popped
        self.assertEqual(len(session.tasks), 0)

    def test_result_submission(self):
        """Test beacon submitting results"""
        # Register a beacon first
        resp = requests.post(f"{self.base_url}/register", json={"user": "test"})
        session_id = resp.json()['session_id']
        
        # Submit result
        result_data = {
            "task_id": "t1",
            "status": "success",
            "output": "root"
        }
        resp = requests.post(f"{self.base_url}/results/{session_id}", json=result_data)
        self.assertEqual(resp.status_code, 200)
        
        # Check if result is saved in session
        session = self.sm.get_session(session_id)
        self.assertIn("t1", session.results)
        self.assertEqual(session.results["t1"]["output"], "root")

    def test_invalid_endpoints(self):
        """Test error handling for invalid paths"""
        resp = requests.get(f"{self.base_url}/nonexistent")
        self.assertEqual(resp.status_code, 404)
        
        resp = requests.post(f"{self.base_url}/nonexistent", json={})
        self.assertEqual(resp.status_code, 400)

if __name__ == '__main__':
    unittest.main()
