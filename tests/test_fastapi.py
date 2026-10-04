import unittest
from fastapi.testclient import TestClient
from api.app import app
from api.middleware.auth import API_TOKEN
from core.logger import LoggerFactory

class TestFastAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.headers = {"X-Api-Token": API_TOKEN}
        LoggerFactory.setup()

    def tearDown(self):
        LoggerFactory.reset()

    def test_health_check(self):
        response = self.client.get("/api/v1/health", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")

    def test_unauthorized(self):
        # Missing token
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 401)
        # Invalid token
        response = self.client.get("/api/v1/health", headers={"X-Api-Token": "invalid"})
        self.assertEqual(response.status_code, 401)

    def test_workspaces(self):
        # Create a workspace
        response = self.client.post("/api/v1/workspaces", json={"name": "api_test"}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        # Get workspaces
        response = self.client.get("/api/v1/workspaces", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("api_test", response.json()["data"])
        
        # Delete workspace
        response = self.client.delete("/api/v1/workspaces/api_test", headers=self.headers)
        self.assertEqual(response.status_code, 200)

    def test_get_hosts_invalid_workspace(self):
        response = self.client.get("/api/v1/hosts?workspace=invalid_workspace_name", headers=self.headers)
        self.assertEqual(response.status_code, 404)

    def test_validation_error(self):
        # Missing required 'name' field
        response = self.client.post("/api/v1/workspaces", json={"description": "Missing name"}, headers=self.headers)
        self.assertEqual(response.status_code, 422)

if __name__ == '__main__':
    unittest.main()
