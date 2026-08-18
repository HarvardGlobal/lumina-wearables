"""Typed boundary models for the Open Wearables HR/HRV pilot."""

from datetime import date
from typing import Literal

from pydantic import BaseModel


class SourceMetadata(BaseModel):
    provider: str
    source: str | None = None
    device: str | None = None
    device_type: str | None = None
    device_name: str | None = None


class RecoverySummary(BaseModel):
    """Subset of Open Wearables' daily recovery response used by this pilot."""

    date: date
    source: SourceMetadata
    resting_heart_rate_bpm: int | None = None
    avg_hrv_sdnn_ms: float | None = None


class Pagination(BaseModel):
    next_cursor: str | None = None
    has_more: bool = False


class RecoverySummaryPage(BaseModel):
    data: list[RecoverySummary]
    pagination: Pagination | None = None


class CanonicalWearableSample(BaseModel):
    """A transparent, daily LUMINA representation; not an OMOP write model."""

    observed_on: date
    metric_key: Literal["resting_hr", "hrv_sdnn"]
    value: float
    unit: Literal["/min", "ms"]
    source_provider: str
    source_device: str | None = None
    source_device_type: str | None = None
    source_metric: str
    temporal_resolution: Literal["daily"] = "daily"
