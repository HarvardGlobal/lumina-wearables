"""Small client for the stable Open Wearables daily recovery API."""

from datetime import date
from uuid import UUID

import httpx

from app.models import (
    ActivitySummary,
    ActivitySummaryPage,
    RecoverySummary,
    RecoverySummaryPage,
    SleepSummary,
    SleepSummaryPage,
)
from app.settings import OpenWearablesSettings


class OpenWearablesClient:
    """API-key client. It never logs credentials or patient identifiers."""

    def __init__(self, settings: OpenWearablesSettings, transport: httpx.BaseTransport | None = None):
        self._client = httpx.Client(
            base_url=settings.base_url,
            headers={"X-Open-Wearables-API-Key": settings.api_key},
            timeout=settings.timeout_seconds,
            transport=transport,
        )

    def __enter__(self) -> "OpenWearablesClient":
        return self

    def __exit__(self, *_: object) -> None:
        self._client.close()

    def get_recovery_summaries(
        self, user_id: UUID, start_date: date, end_date: date
    ) -> list[RecoverySummary]:
        return self._get_summaries(user_id, start_date, end_date, "recovery", RecoverySummaryPage)

    def get_activity_summaries(self, user_id: UUID, start_date: date, end_date: date) -> list[ActivitySummary]:
        return self._get_summaries(user_id, start_date, end_date, "activity", ActivitySummaryPage)

    def get_sleep_summaries(self, user_id: UUID, start_date: date, end_date: date) -> list[SleepSummary]:
        return self._get_summaries(user_id, start_date, end_date, "sleep", SleepSummaryPage)

    def _get_summaries(self, user_id: UUID, start_date: date, end_date: date, kind: str, page_type):
        params: dict[str, str | int] = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "limit": 100,
        }
        summaries = []
        while True:
            response = self._client.get(f"/users/{user_id}/summaries/{kind}", params=params)
            response.raise_for_status()
            page = page_type.model_validate(response.json())
            summaries.extend(page.data)
            if not page.pagination or not page.pagination.has_more or not page.pagination.next_cursor:
                return summaries
            params["cursor"] = page.pagination.next_cursor
