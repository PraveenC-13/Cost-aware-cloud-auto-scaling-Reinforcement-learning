from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model_loaded" in data


def test_decide_endpoint_valid_input():
    payload = {
        "cpu": 85.0,
        "memory": 60.0,
        "predicted_cpu_next_15min": 90.0,
        "instance_count": 4,
        "current_hourly_cost": 0.20,
    }
    response = client.post("/decide", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Validate response schema keys
    assert "action" in data
    assert "action_name" in data
    assert "confidence" in data
    assert "reasoning" in data

    # Action must be 0, 1, or 2
    assert data["action"] in [0, 1, 2]
    assert data["action_name"] in ["hold", "scale_up", "scale_down"]
    assert 0.0 <= data["confidence"] <= 1.0
    assert isinstance(data["reasoning"], str)


def test_decide_endpoint_invalid_input_validation():
    # Out-of-bounds CPU (> 100)
    payload = {
        "cpu": 150.0,
        "memory": 60.0,
        "predicted_cpu_next_15min": 90.0,
        "instance_count": 4,
        "current_hourly_cost": 0.20,
    }
    response = client.post("/decide", json=payload)
    assert response.status_code == 422  # Unprocessable Entity (Pydantic validation error)


def test_decide_endpoint_low_utilization():
    payload = {
        "cpu": 15.0,
        "memory": 20.0,
        "predicted_cpu_next_15min": 10.0,
        "instance_count": 5,
        "current_hourly_cost": 0.25,
    }
    response = client.post("/decide", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["action"] in [0, 1, 2]
