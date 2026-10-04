import unittest
from fastapi.testclient import TestClient
from api.app import app
from api.services.auth_service import auth_service
from core.session_db import SessionDatabase
from core.history import HistoryAnalyzer

class TestHistoryAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        
        # Reset DB and users for clean tests
        with __import__('sqlite3').connect(auth_service.db.db_path) as conn:
            conn.execute("DELETE FROM users")
            
        auth_service._ensure_admin_exists()
        auth_service.create_user("analyst", "pass123", "Analyst", ["test_ws"])
        
        # Login
        resp = self.client.post("/api/v1/auth/login", json={"username": "analyst", "password": "pass123"})
        self.token = resp.json()["data"]["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Insert Workspace and data
        from api.services.framework_service import FrameworkService
        self.db = FrameworkService.get_db()
        
        with __import__('sqlite3').connect(self.db.db_path) as conn:
            conn.execute("DELETE FROM scan_services")
            conn.execute("DELETE FROM scan_hosts")
            conn.execute("DELETE FROM scans")
            conn.execute("DELETE FROM services")
            conn.execute("DELETE FROM hosts")
            conn.execute("DELETE FROM workspaces")
            
        self.db.add_workspace("test_ws")
        self.db.add_host("test_ws", "10.0.0.1", status="up")

    def test_snapshot_and_history(self):
        # 1. Take Snapshot
        resp = self.client.post("/api/v1/history/snapshot?workspace=test_ws&source=API_Test", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        scan_id_1 = resp.json()["data"]["scan_id"]
        
        # 2. Add Host and Take another Snapshot
        self.db.add_host("test_ws", "10.0.0.2", status="up")
        resp = self.client.post("/api/v1/history/snapshot?workspace=test_ws&source=API_Test_2", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        scan_id_2 = resp.json()["data"]["scan_id"]
        
        # 3. List History
        resp = self.client.get("/api/v1/history/scans?workspace=test_ws", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(len(data), 2)
        
        # 4. Compare
        resp = self.client.get(f"/api/v1/history/compare?workspace=test_ws&old_scan_id={scan_id_1}&new_scan_id={scan_id_2}", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        report = resp.json()["data"]
        self.assertEqual(report["old_scan_id"], scan_id_1)
        self.assertEqual(report["new_scan_id"], scan_id_2)
        self.assertIn("10.0.0.2", report["hosts"]["new"])

if __name__ == '__main__':
    unittest.main()
