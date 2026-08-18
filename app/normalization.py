"""Loss-aware normalization for the deliberately small HR/HRV pilot."""

from app.models import CanonicalWearableSample, RecoverySummary

# At the pinned Open Wearables revision, the daily recovery endpoint exposes a
# WHOOP RMSSD value through the field named ``avg_hrv_sdnn_ms``. Until upstream
# corrects that contract, only providers whose field is proven SDNN may emit it.
SDNN_RECOVERY_PROVIDERS = frozenset({"apple", "garmin"})


def normalize_recovery_summaries(
    summaries: list[RecoverySummary],
) -> list[CanonicalWearableSample]:
    """Map only semantically exact daily Open Wearables recovery fields.

    Raw continuous heart rate, RMSSD, and provider scores are intentionally
    excluded. They need their own aggregation or vocabulary decisions.
    """
    samples: list[CanonicalWearableSample] = []
    for summary in summaries:
        common = {
            "observed_on": summary.date,
            "source_provider": summary.source.provider,
            "source_device": summary.source.device,
            "source_device_type": summary.source.device_type,
        }
        if summary.resting_heart_rate_bpm is not None:
            samples.append(
                CanonicalWearableSample(
                    **common,
                    metric_key="resting_hr",
                    value=float(summary.resting_heart_rate_bpm),
                    unit="/min",
                    source_metric="recovery.resting_heart_rate_bpm",
                )
            )
        if (
            summary.avg_hrv_sdnn_ms is not None
            and summary.source.provider.casefold() in SDNN_RECOVERY_PROVIDERS
        ):
            samples.append(
                CanonicalWearableSample(
                    **common,
                    metric_key="hrv_sdnn",
                    value=summary.avg_hrv_sdnn_ms,
                    unit="ms",
                    source_metric="recovery.avg_hrv_sdnn_ms",
                )
            )
    return samples
