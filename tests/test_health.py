from fastapi.testclient import TestClient

from app.main import app


def test_health():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "lumina-wearables"}


def test_recovery_requires_open_wearables_configuration(monkeypatch):
    monkeypatch.delenv("OPEN_WEARABLES_BASE_URL", raising=False)
    monkeypatch.delenv("OPEN_WEARABLES_API_KEY", raising=False)

    response = TestClient(app).get(
        "/api/v1/open-wearables/users/b9dc2fe8-9df1-4140-b6c2-7f989a4d7b53/daily-recovery",
        params={"start_date": "2026-08-01", "end_date": "2026-08-17"},
    )

    assert response.status_code == 503
    assert "OPEN_WEARABLES_BASE_URL" in response.json()["detail"]


def test_recovery_rejects_inverted_date_range():
    response = TestClient(app).get(
        "/api/v1/open-wearables/users/b9dc2fe8-9df1-4140-b6c2-7f989a4d7b53/daily-recovery",
        params={"start_date": "2026-08-17", "end_date": "2026-08-01"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "end_date must not precede start_date"
