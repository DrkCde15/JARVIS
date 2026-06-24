import os
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["SECRET_KEY"] = "test-secret-key-for-testing"


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from api.server import app

    with TestClient(app) as c:
        yield c


class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestAuthEndpoints:
    def test_register(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={"username": "newuser", "password": "newpass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"

    def test_register_duplicate(self, client):
        client.post(
            "/api/v1/auth/register",
            json={"username": "dupuser", "password": "pass123"},
        )
        response = client.post(
            "/api/v1/auth/register",
            json={"username": "dupuser", "password": "pass123"},
        )
        assert response.status_code == 409

    def test_login(self, client):
        client.post(
            "/api/v1/auth/register",
            json={"username": "loginuser", "password": "pass123"},
        )
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "loginuser", "password": "pass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["username"] == "loginuser"

    def test_login_invalid(self, client):
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nobody", "password": "wrong"},
        )
        assert response.status_code == 401


class TestPermissionEndpoints:
    def test_list_roles_requires_auth(self, client):
        response = client.get("/api/v1/permissions/roles")
        assert response.status_code in (401, 403)

    def test_seed_data_requires_auth(self, client):
        response = client.post("/api/v1/permissions/seed")
        assert response.status_code in (401, 403)
