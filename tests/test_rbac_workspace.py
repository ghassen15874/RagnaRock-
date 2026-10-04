import pytest
from fastapi.testclient import TestClient
import sqlite3
import os

from api.app import app
from api.services.auth_service import auth_service
from core.session_db import SessionDatabase
from api.services.framework_service import FrameworkService

@pytest.fixture(scope="module")
def client():
    # Setup fresh auth DB for tests
    auth_db_path = "test_auth_rbac.db"
    auth_service.db.db_path = auth_db_path
    if os.path.exists(auth_db_path):
        os.remove(auth_db_path)
    
    # Setup fresh session DB for tests
    session_db_path = "test_session_rbac.db"
    if os.path.exists(session_db_path):
        os.remove(session_db_path)
        
    FrameworkService.get_db = lambda: SessionDatabase(session_db_path)
    
    # Create test users
    auth_service.db.init_database()
    auth_service.create_user("admin_test", "pass123", "Administrator", ["*"])
    auth_service.create_user("analyst_test", "pass123", "Analyst", ["project_a"])
    auth_service.create_user("viewer_test", "pass123", "Viewer", ["project_b"])
    
    # Create test workspaces
    FrameworkService.get_db().add_workspace("project_a")
    FrameworkService.get_db().add_workspace("project_b")
    
    # Add dummy data
    FrameworkService.get_db().add_host("project_a", "192.168.1.1", status="up")
    FrameworkService.get_db().add_host("project_b", "10.0.0.1", status="up")
    
    with TestClient(app) as client:
        yield client
        
    if os.path.exists(auth_db_path):
        os.remove(auth_db_path)
    if os.path.exists(session_db_path):
        os.remove(session_db_path)

def get_token(client, username, password):
    resp = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    return resp.json()["data"]["access_token"]

def test_idor_prevention_on_hosts(client):
    analyst_token = get_token(client, "analyst_test", "pass123")
    headers = {"Authorization": f"Bearer {analyst_token}"}
    
    # Can access project_a
    resp = client.get("/api/v1/hosts?workspace=project_a", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]["items"]) >= 1
    
    # Cannot access project_b
    resp = client.get("/api/v1/hosts?workspace=project_b", headers=headers)
    assert resp.status_code == 403
    assert "Permission denied" in resp.json()["detail"] or "Not authorized" in resp.json()["detail"]

def test_rbac_roles(client):
    viewer_token = get_token(client, "viewer_test", "pass123")
    headers = {"Authorization": f"Bearer {viewer_token}"}
    
    # Viewer can read
    resp = client.get("/api/v1/hosts?workspace=project_b", headers=headers)
    assert resp.status_code == 200
    
    # Viewer cannot delete workspace
    resp = client.delete("/api/v1/workspaces/project_b", headers=headers)
    assert resp.status_code == 403

def test_default_workspace_protection(client):
    admin_token = get_token(client, "admin_test", "pass123")
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    resp = client.delete("/api/v1/workspaces/default", headers=headers)
    assert resp.status_code == 400
    assert "Cannot delete default workspace" in resp.json()["detail"]

def test_workspace_isolation_in_reports(client):
    analyst_token = get_token(client, "analyst_test", "pass123")
    headers = {"Authorization": f"Bearer {analyst_token}"}
    
    # Try to generate report for project_b (unauthorized)
    resp = client.get("/api/v1/reports/generate?workspace=project_b&format=json", headers=headers)
    assert resp.status_code == 403
