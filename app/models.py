"""Typed boundaries for approved Open Wearables daily summaries."""

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
    avg_spo2_percent: float | None = None


class ActivitySummary(BaseModel):
    date: date
    source: SourceMetadata
    steps: int | None = None
    floors_climbed: int | None = None
    active_calories_kcal: float | None = None
    active_minutes: int | None = None


class SleepSummary(BaseModel):
    date: date
    source: SourceMetadata
    duration_minutes: int | None = None
    avg_respiratory_rate: float | None = None
    avg_spo2_percent: float | None = None


class Pagination(BaseModel):
    next_cursor: str | None = None
    has_more: bool = False


class RecoverySummaryPage(BaseModel):
    data: list[RecoverySummary]
    pagination: Pagination | None = None


class ActivitySummaryPage(BaseModel):
    data: list[ActivitySummary]
    pagination: Pagination | None = None


class SleepSummaryPage(BaseModel):
    data: list[SleepSummary]
    pagination: Pagination | None = None


MetricKey = Literal[
    "steps", "active_minutes", "resting_hr", "hrv_sdnn", "hrv_rmssd", "spo2", "respiratory_rate",
    "sleep_duration", "vo2_max", "distance", "walking_speed", "walking_step_length",
    "walking_double_support_pct", "walking_hr_avg", "flights_climbed", "active_energy", "basal_energy",
    "body_mass",
]
MetricUnit = Literal["/d", "min", "/min", "ms", "%", "h", "mL/kg/min", "km", "km/hr", "cm", "{flights}", "kcal", "kg"]


class CanonicalWearableSample(BaseModel):
    """A transparent, daily LUMINA representation; not an OMOP write model."""

    observed_on: date
    metric_key: MetricKey
    value: float
    unit: MetricUnit
    source_provider: str
    source_device: str | None = None
    source_device_type: str | None = None
    source_metric: str
    temporal_resolution: Literal["daily"] = "daily"
