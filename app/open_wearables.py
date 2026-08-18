"""Small client for the stable Open Wearables daily recovery API."""

from datetime import date
from uuid import UUID

import httpx

from app.models import RecoverySummary, RecoverySummaryPage
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
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "limit": 100,
        }
        summaries: list[RecoverySummary] = []
        while True:
            response = self._client.get(f"/users/{user_id}/summaries/recovery", params=params)
            response.raise_for_status()
            page = RecoverySummaryPage.model_validate(response.json())
            summaries.extend(page.data)
            if not page.pagination or not page.pagination.has_more or not page.pagination.next_cursor:
                return summaries
            params["cursor"] = page.pagination.next_cursor
