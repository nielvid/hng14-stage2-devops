import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

with patch("redis.Redis") as mock_redis_cls:
    mock_redis = MagicMock()
    mock_redis_cls.return_value = mock_redis
    from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_mock():
    mock_redis.reset_mock()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_job_returns_job_id():
    response = client.post("/jobs")
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert len(data["job_id"]) == 36  # UUID format


def test_create_job_pushes_to_redis():
    response = client.post("/jobs")
    job_id = response.json()["job_id"]
    mock_redis.lpush.assert_called_once_with("job", job_id)
    mock_redis.hset.assert_called_once_with(f"job:{job_id}", "status", "queued")


def test_get_job_found():
    mock_redis.hget.return_value = b"completed"
    response = client.get("/jobs/test-id-123")
    assert response.status_code == 200
    assert response.json() == {"job_id": "test-id-123", "status": "completed"}


def test_get_job_not_found():
    mock_redis.hget.return_value = None
    response = client.get("/jobs/nonexistent")
    assert response.status_code == 200
    assert response.json() == {"error": "not found"}
