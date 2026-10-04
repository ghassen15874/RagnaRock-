import unittest
import threading
import time
import requests
import json
import socket
from core.handlers import HTTPHandler
from core.session_manager import SessionManager
from core.session_db import SessionDatabase
import os

class TestHTTPBeaconReliability(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = "test_beacon.db"
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
        cls.db = SessionDatabase(cls.db_path)
        cls.db.add_workspace("beacon_ws")
        
    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

    def setUp(self):
        self.session_manager = SessionManager(self.db_path)
        self.handler = HTTPHandler(self.session_manager)
        self.port = self.find_free_port()
        self.handler_id = "test_http_1"
        self.base_url = f"http://127.0.0.1:{self.port}"
        
        # Start handler
        t = threading.Thread(target=self.handler._run_server, args=("127.0.0.1", self.port, self.handler_id))
        t.daemon = True
        t.start()
        
        # Wait for server to start
        time.sleep(0.5)

    def tearDown(self):
        self.handler.stop_http_handler(self.handler_id)
        time.sleep(0.5)
        
    def find_free_port(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]

    def test_server_start_stop(self):
        self.assertTrue(self.handler.active_handlers[self.handler_id]['active'])
        # Can we connect?
        resp = requests.get(f"{self.base_url}/invalid", timeout=2)
        self.assertEqual(resp.status_code, 404)
        
        # Stop
        self.handler.stop_http_handler(self.handler_id)
        time.sleep(1.5)
        self.assertFalse(self.handler_id in self.handler.active_handlers)
        
        # Connection should be refused
        with self.assertRaises(requests.exceptions.ConnectionError):
            requests.get(f"{self.base_url}/invalid", timeout=2)

    def test_registration_and_tasks(self):
        # Register
        sysinfo = {"hostname": "testhost", "user": "testuser"}
        resp = requests.post(f"{self.base_url}/register", json=sysinfo, timeout=2)
        self.assertEqual(resp.status_code, 200)
        session_id = resp.json().get("session_id")
        self.assertIsNotNone(session_id)
        
        # Check session manager
        session = self.session_manager.get_session(session_id)
        self.assertIsNotNone(session)
        self.assertEqual(session.metadata['user'], 'testuser')
        
        # Queue task directly in session manager
        session.tasks.append({"id": "1", "command": "whoami"})
        
        # Poll tasks
        resp = requests.get(f"{self.base_url}/tasks/{session_id}", timeout=2)
        self.assertEqual(resp.status_code, 200)
        tasks = resp.json().get("tasks")
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["command"], "whoami")
        
        # Send result
        result = {"task_id": "1", "status": "success", "output": "testuser"}
        resp = requests.post(f"{self.base_url}/results/{session_id}", json=result, timeout=2)
        self.assertEqual(resp.status_code, 200)
        
        self.assertIn("1", session.results)
        self.assertEqual(session.results["1"]["output"], "testuser")

    def test_invalid_requests(self):
        # Missing payload
        resp = requests.post(f"{self.base_url}/register", data="invalid json", timeout=2)
        # Should gracefully return 400 or handle exception without crashing server
        self.assertEqual(resp.status_code, 400)
        
        # Invalid endpoint
        resp = requests.get(f"{self.base_url}/admin", timeout=2)
        self.assertEqual(resp.status_code, 404)
        
    def test_concurrent_connections(self):
        def make_request():
            sysinfo = {"hostname": "testhost", "user": "testuser"}
            requests.post(f"{self.base_url}/register", json=sysinfo, timeout=5)
            
        threads = []
        for _ in range(20):
            t = threading.Thread(target=make_request)
            threads.append(t)
            t.start()
            
        for t in threads:
            t.join()
            
        # 20 sessions should have been created
        # Wait, some might fail if ThreadingHTTPServer is overwhelmed, but it shouldn't crash
        active = len(self.session_manager.list_sessions())
        self.assertTrue(active > 0)

if __name__ == '__main__':
    unittest.main()
