import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health_check(client):
    """Test that the health check endpoint returns successfully"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_get_status(client):
    """Test that the status endpoint returns correctly"""
    response = client.get("/simulation/status")
    assert response.status_code == 200
    data = response.json()
    assert "running" in data
    assert "events_sent" in data
