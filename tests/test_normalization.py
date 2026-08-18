from datetime import date

from app.models import RecoverySummary, SourceMetadata
from app.normalization import normalize_recovery_summaries


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
