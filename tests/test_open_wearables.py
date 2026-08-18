from datetime import date
from uuid import UUID

import httpx

from app.open_wearables import OpenWearablesClient
from app.settings import OpenWearablesSettings


def test_recovery_client_uses_api_key_and_exact_endpoint():
    request_seen = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_seen
        request_seen = request
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "date": "2026-08-17",
                        "source": {"provider": "whoop", "device_name": "WHOOP"},
                        "resting_heart_rate_bpm": 51,
                        "avg_hrv_sdnn_ms": 63.2,
                    }
                ],
                "pagination": {},
                "metadata": {},
            },
        )

    settings = OpenWearablesSettings("https://wearables.example/api/v1", "test-key")
    with OpenWearablesClient(settings, transport=httpx.MockTransport(handler)) as client:
        summaries = client.get_recovery_summaries(
            UUID("b9dc2fe8-9df1-4140-b6c2-7f989a4d7b53"), date(2026, 8, 1), date(2026, 8, 17)
        )

    assert request_seen is not None
    assert request_seen.headers["X-Open-Wearables-API-Key"] == "test-key"
    assert request_seen.url.path == "/api/v1/users/b9dc2fe8-9df1-4140-b6c2-7f989a4d7b53/summaries/recovery"
    assert request_seen.url.params["start_date"] == "2026-08-01"
    assert len(summaries) == 1
    assert summaries[0].avg_hrv_sdnn_ms == 63.2


def test_recovery_client_follows_pagination_cursor():
    requested_cursors: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        cursor = request.url.params.get("cursor")
        requested_cursors.append(cursor)
        if cursor is None:
            return httpx.Response(
                200,
                json={
                    "data": [{"date": "2026-08-01", "source": {"provider": "garmin"}}],
                    "pagination": {"has_more": True, "next_cursor": "next-page"},
                },
            )
        return httpx.Response(
            200,
            json={
                "data": [{"date": "2026-08-02", "source": {"provider": "garmin"}}],
                "pagination": {"has_more": False},
            },
        )

    with OpenWearablesClient(
        OpenWearablesSettings("https://wearables.example/api/v1", "test-key"),
        transport=httpx.MockTransport(handler),
    ) as client:
        summaries = client.get_recovery_summaries(
            UUID("b9dc2fe8-9df1-4140-b6c2-7f989a4d7b53"), date(2026, 8, 1), date(2026, 8, 2)
        )

    assert requested_cursors == [None, "next-page"]
    assert [summary.date for summary in summaries] == [date(2026, 8, 1), date(2026, 8, 2)]
