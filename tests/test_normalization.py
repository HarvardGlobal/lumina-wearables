from datetime import date

from app.models import ActivitySummary, RecoverySummary, SleepSummary, SourceMetadata
from app.normalization import normalize_daily_summaries, normalize_recovery_summaries


def test_normalizes_only_exact_daily_recovery_metrics():
    samples = normalize_recovery_summaries(
        [
            RecoverySummary(
                date=date(2026, 8, 17),
                source=SourceMetadata(provider="garmin", device="Forerunner", device_type="watch"),
                resting_heart_rate_bpm=54,
                avg_hrv_sdnn_ms=42.5,
            )
        ]
    )

    assert [sample.model_dump() for sample in samples] == [
        {
            "observed_on": date(2026, 8, 17),
            "metric_key": "resting_hr",
            "value": 54.0,
            "unit": "/min",
            "source_provider": "garmin",
            "source_device": "Forerunner",
            "source_device_type": "watch",
            "source_metric": "recovery.resting_heart_rate_bpm",
            "temporal_resolution": "daily",
        },
        {
            "observed_on": date(2026, 8, 17),
            "metric_key": "hrv_sdnn",
            "value": 42.5,
            "unit": "ms",
            "source_provider": "garmin",
            "source_device": "Forerunner",
            "source_device_type": "watch",
            "source_metric": "recovery.avg_hrv_sdnn_ms",
            "temporal_resolution": "daily",
        },
    ]


def test_omits_missing_values_without_substitution():
    samples = normalize_recovery_summaries(
        [
            RecoverySummary(
                date=date(2026, 8, 17),
                source=SourceMetadata(provider="apple"),
            )
        ]
    )

    assert samples == []


def test_does_not_mislabel_whoop_rmssd_as_sdnn():
    samples = normalize_recovery_summaries(
        [
            RecoverySummary(
                date=date(2026, 8, 17),
                source=SourceMetadata(provider="whoop"),
                resting_heart_rate_bpm=51,
                # The pinned Open Wearables recovery endpoint currently puts
                # WHOOP's source field hrv_rmssd_milli in this SDNN-labelled
                # response field. It must not be promoted as SDNN.
                avg_hrv_sdnn_ms=63.2,
            )
        ]
    )

    assert [sample.metric_key for sample in samples] == ["resting_hr"]


def test_normalizes_all_verified_activity_sleep_and_recovery_summary_fields():
    source = SourceMetadata(provider="garmin", device="Forerunner", device_type="watch")
    samples = normalize_daily_summaries(
        [ActivitySummary(date=date(2026, 8, 17), source=source, steps=8432, active_minutes=60, floors_climbed=12, active_calories_kcal=342.5)],
        [SleepSummary(date=date(2026, 8, 17), source=source, duration_minutes=450, avg_respiratory_rate=13.5, avg_spo2_percent=97.1)],
        [RecoverySummary(date=date(2026, 8, 17), source=source, resting_heart_rate_bpm=54, avg_hrv_sdnn_ms=42.5, avg_spo2_percent=97.4)],
    )

    assert [(sample.metric_key, sample.value, sample.unit) for sample in samples] == [
        ("steps", 8432.0, "/d"), ("active_minutes", 60.0, "min"), ("flights_climbed", 12.0, "{flights}"),
        ("active_energy", 342.5, "kcal"), ("resting_hr", 54.0, "/min"), ("hrv_sdnn", 42.5, "ms"),
        ("spo2", 97.4, "%"), ("sleep_duration", 7.5, "h"), ("respiratory_rate", 13.5, "/min"),
    ]
