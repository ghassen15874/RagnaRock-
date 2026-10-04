import unittest
from fastapi.testclient import TestClient
from api.app import app
from api.services.auth_service import auth_service
import time

class TestAPIAuth(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        
        # Reset DB and users for clean tests
        with __import__('sqlite3').connect(auth_service.db.db_path) as conn:
            conn.execute("DELETE FROM users")
            conn.execute("DELETE FROM login_attempts")
            conn.execute("DELETE FROM revoked_tokens")
            
        auth_service.db.init_database()
        
        # Ensure admin is created
        auth_service._ensure_admin_exists()
        
        # Create different role users
        auth_service.create_user("analyst_1", "pass123", "Analyst", ["ws1"])
        auth_service.create_user("viewer_1", "pass123", "Viewer", ["ws2"])

    def test_login_success_and_rate_limit(self):
        # Successful login
        resp = self.client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access_token", resp.json()["data"])
        
        # Failed logins to trigger rate limit
        for _ in range(5):
            self.client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrongpassword"})
            
        # 6th attempt should hit rate limit even with correct password
        resp = self.client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
        self.assertEqual(resp.status_code, 401)
        self.assertIn("Rate limit", resp.json()["detail"])

    def test_unauthorized_access(self):
        # Access without token
        resp = self.client.get("/api/v1/workspaces")
        self.assertEqual(resp.status_code, 401)
        
    def test_privilege_escalation(self):
        # Get viewer token
        resp = self.client.post("/api/v1/auth/login", json={"username": "viewer_1", "password": "pass123"})
        token = resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Viewer trying to access admin endpoint (create workspace)
        resp = self.client.post("/api/v1/workspaces", json={"name": "test_ws"}, headers=headers)
        self.assertEqual(resp.status_code, 403)
        self.assertIn("Not enough permissions", resp.json()["detail"])
        
    def test_workspace_isolation(self):
        # Analyst with access to ws1
        resp = self.client.post("/api/v1/auth/login", json={"username": "analyst_1", "password": "pass123"})
        token = resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Access allowed workspace
        resp = self.client.get("/api/v1/hosts?workspace=ws1", headers=headers)
        # It may return 404 if ws1 doesn't exist in main DB, but it shouldn't return 403
        self.assertNotEqual(resp.status_code, 403)
        
        # Access unauthorized workspace
        resp = self.client.get("/api/v1/hosts?workspace=ws2", headers=headers)
        self.assertEqual(resp.status_code, 403)
        
    def test_token_revocation(self):
        resp = self.client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
        token = resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Should work
        resp = self.client.get("/api/v1/workspaces", headers=headers)
        self.assertEqual(resp.status_code, 200)
        
        # Logout
        resp = self.client.post("/api/v1/auth/logout", headers=headers)
        self.assertEqual(resp.status_code, 200)
        
        # Should not work
        resp = self.client.get("/api/v1/workspaces", headers=headers)
        self.assertEqual(resp.status_code, 401)

if __name__ == '__main__':
    unittest.main()
