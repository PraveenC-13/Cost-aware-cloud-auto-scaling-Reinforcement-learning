from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.main import WINDOW_SIZE, app

client = TestClient(app)


def _sample_history(n=WINDOW_SIZE):
    start = datetime(2026, 8, 11, 10, 0, 0)
    return [
        {
            "timestamp": (start + timedelta(minutes=i)).isoformat() + "Z",
            "cpu": 40 + (i % 10),
            "memory": 55,
            "requests_per_sec": 120 + (i % 20),
        }
        for i in range(n)
    ]


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_predict_returns_schema_shape_in_stub_mode():
    # In stub mode (no trained model on disk), forecast is empty but the
    # response must still match PredictResponse's schema.
    resp = client.post("/predict", json={"history": _sample_history()})
    assert resp.status_code == 200
    body = resp.json()
    assert "forecast" in body
    assert "model_used" in body
    assert "confidence" in body


def test_predict_rejects_too_little_history():
    resp = client.post("/predict", json={"history": _sample_history(n=5)})
    assert resp.status_code == 422
