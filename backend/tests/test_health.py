from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app

client = TestClient(app)
prefix = get_settings().api_v1_prefix


def test_health_ok():
    response = client.get(f"{prefix}/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "HummingID"
    assert body["version"] == "0.1.0"
