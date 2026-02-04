# backend/tests/test_main.py

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    """
    Tests the root endpoint to ensure the API is running.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "traverse-backend"}
