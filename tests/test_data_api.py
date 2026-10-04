import unittest
from fastapi.testclient import TestClient
from api.app import app
from api.services.auth_service import auth_service
from api.services.data_service import DataService
from core.logger import LoggerFactory

class TestDataAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        LoggerFactory.setup()
        
        # Reset DB and users for clean tests
        with __import__('sqlite3').connect(auth_service.db.db_path) as conn:
            conn.execute("DELETE FROM users")
            conn.execute("DELETE FROM login_attempts")
            conn.execute("DELETE FROM revoked_tokens")
            
        auth_service._ensure_admin_exists()
        
        # Insert fake data into sessions DB
        with __import__('sqlite3').connect(DataService.get_db_path()) as conn:
            conn.execute("DELETE FROM hosts")
            conn.execute("DELETE FROM services")
            conn.execute("DELETE FROM workspaces WHERE name='test_ws'")
            
            conn.execute("INSERT INTO workspaces (name, description, created_at) VALUES (?, ?, ?)",
                         ('test_ws', 'Test', '2023-01-01T00:00:00'))
            
            # 5 hosts in workspace 'test_ws'
            for i in range(1, 6):
                conn.execute(
                    "INSERT INTO hosts (id, workspace, ip_address, os_name, status) VALUES (?, ?, ?, ?, ?)",
                    (i, 'test_ws', f'192.168.1.{i}', 'Linux', 'up' if i % 2 == 0 else 'down')
                )
                
            # 3 services for host 1
            for p in [22, 80, 443]:
                conn.execute(
                    "INSERT INTO services (host_id, port, protocol, name, state) VALUES (?, ?, ?, ?, ?)",
                    (1, p, 'tcp', 'ssh' if p==22 else 'http', 'open')
                )
            conn.commit()
            
        # Give admin access to test_ws
        auth_service.create_user("analyst", "pass123", "Analyst", ["test_ws"])
        
        # Login
        resp = self.client.post("/api/v1/auth/login", json={"username": "analyst", "password": "pass123"})
        token = resp.json()["data"]["access_token"]
        self.headers = {"Authorization": f"Bearer {token}"}

    def test_list_hosts_pagination_and_sorting(self):
        # Default fetch
        resp = self.client.get("/api/v1/hosts?workspace=test_ws", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["total"], 5)
        self.assertEqual(len(data["items"]), 5)
        
        # Pagination
        resp = self.client.get("/api/v1/hosts?workspace=test_ws&limit=2&offset=0", headers=self.headers)
        data = resp.json()["data"]
        self.assertEqual(len(data["items"]), 2)
        
        # Sorting
        resp = self.client.get("/api/v1/hosts?workspace=test_ws&sort_by=id&sort_desc=true", headers=self.headers)
        items = resp.json()["data"]["items"]
        self.assertEqual(items[0]["id"], 5)
        
        # Filtering
        resp = self.client.get("/api/v1/hosts?workspace=test_ws&status=up", headers=self.headers)
        items = resp.json()["data"]["items"]
        self.assertEqual(len(items), 2) # hosts 2 and 4

    def test_get_host_details(self):
        resp = self.client.get("/api/v1/hosts/1?workspace=test_ws", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["data"]["ip"], "192.168.1.1")
        
        # Non-existent
        resp = self.client.get("/api/v1/hosts/999?workspace=test_ws", headers=self.headers)
        self.assertEqual(resp.status_code, 404)

    def test_list_services_pagination_and_sorting(self):
        # Default fetch
        resp = self.client.get("/api/v1/services/host/1?workspace=test_ws", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["total"], 3)
        
        # Sorting
        resp = self.client.get("/api/v1/services/host/1?workspace=test_ws&sort_by=port&sort_desc=true", headers=self.headers)
        items = resp.json()["data"]["items"]
        self.assertEqual(items[0]["port"], 443)

    def test_get_service_details(self):
        # We don't know the exact service ID because of autoincrement, let's fetch it first
        resp = self.client.get("/api/v1/services/host/1?workspace=test_ws", headers=self.headers)
        svc_id = resp.json()["data"]["items"][0]["id"]
        
        resp = self.client.get(f"/api/v1/services/{svc_id}?workspace=test_ws", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["data"]["id"], svc_id)
        
    def test_reports_api(self):
        # Available formats
        resp = self.client.get("/api/v1/reports/available", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("json", resp.json()["data"])
        
        # Generate JSON
        resp = self.client.get("/api/v1/reports/generate?workspace=test_ws&format=json", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["content-type"], "application/json")
        
if __name__ == '__main__':
    unittest.main()
