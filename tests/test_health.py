from datetime import date
from uuid import UUID

from fastapi.testclient import TestClient

import app.main as main
from app.models import CanonicalWearableSample
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


def test_export_uses_an_explicit_person_and_the_protected_promop_bridge(monkeypatch):
    monkeypatch.setenv("PROMOP_BASE_URL", "https://promop.example")
    monkeypatch.setenv("PROMOP_SERVICE_AUTH_TOKEN", "promop-token")
    monkeypatch.setenv("LUMINA_WEARABLES_EXPORT_TOKEN", "wearables-token")
    captured: dict[str, object] = {}

    def approved_samples(user_id: UUID, start_date: date, end_date: date):
        assert user_id == UUID("b9dc2fe8-9df1-4140-b6c2-7f989a4d7b53")
        assert (start_date, end_date) == (date(2026, 8, 1), date(2026, 8, 17))
        return [
            CanonicalWearableSample(
                observed_on=date(2026, 8, 17),
                metric_key="resting_hr",
                value=54,
                unit="/min",
                source_provider="apple",
                source_metric="recovery.resting_heart_rate_bpm",
            )
        ]

    class FakePromopClient:
        def __init__(self, settings):
            captured["settings"] = settings

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return None

        def export_daily_samples(self, *, person_id, samples):
            captured["person_id"] = person_id
            captured["samples"] = samples
            return {"tables": {"measurements": {"ids": [11]}}}

    monkeypatch.setattr(main, "approved_daily_samples", approved_samples)
    monkeypatch.setattr(main, "PromopClient", FakePromopClient)
    response = TestClient(app).post(
        "/api/v1/promop/persons/42/open-wearables/users/b9dc2fe8-9df1-4140-b6c2-7f989a4d7b53/daily-recovery/export",
        params={"start_date": "2026-08-01", "end_date": "2026-08-17"},
        headers={"Authorization": "Bearer wearables-token"},
    )

    assert response.status_code == 200
    assert response.json()["person_id"] == 42
    assert response.json()["exported_samples"] == 1
    assert captured["person_id"] == 42


def test_export_requires_the_lumina_wearables_export_token(monkeypatch):
    monkeypatch.setenv("PROMOP_BASE_URL", "https://promop.example")
    monkeypatch.setenv("PROMOP_SERVICE_AUTH_TOKEN", "promop-token")
    monkeypatch.setenv("LUMINA_WEARABLES_EXPORT_TOKEN", "wearables-token")

    response = TestClient(app).post(
        "/api/v1/promop/persons/42/open-wearables/users/b9dc2fe8-9df1-4140-b6c2-7f989a4d7b53/daily-recovery/export",
        params={"start_date": "2026-08-01", "end_date": "2026-08-17"},
    )

    assert response.status_code == 401


def test_daily_summaries_export_uses_the_all_summary_normalization_path(monkeypatch):
    monkeypatch.setenv("PROMOP_BASE_URL", "https://promop.example")
    monkeypatch.setenv("PROMOP_SERVICE_AUTH_TOKEN", "promop-token")
    monkeypatch.setenv("LUMINA_WEARABLES_EXPORT_TOKEN", "wearables-token")
    captured: dict[str, object] = {}

    def summary_samples(*_):
        return [CanonicalWearableSample(observed_on=date(2026, 8, 17), metric_key="steps", value=8432, unit="/d", source_provider="garmin", source_metric="activity.steps")]

    class FakePromopClient:
        def __init__(self, _settings):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return None

        def export_daily_samples(self, *, person_id, samples):
            captured["person_id"] = person_id
            captured["samples"] = samples
            return {"tables": {"observations": {"ids": [12]}}}

    monkeypatch.setattr(main, "approved_daily_summary_samples", summary_samples)
    monkeypatch.setattr(main, "PromopClient", FakePromopClient)
    response = TestClient(app).post(
        "/api/v1/promop/persons/42/open-wearables/users/b9dc2fe8-9df1-4140-b6c2-7f989a4d7b53/daily-summaries/export",
        params={"start_date": "2026-08-01", "end_date": "2026-08-17"},
        headers={"Authorization": "Bearer wearables-token"},
    )

    assert response.status_code == 200
    assert response.json()["exported_samples"] == 1
    assert captured["person_id"] == 42
