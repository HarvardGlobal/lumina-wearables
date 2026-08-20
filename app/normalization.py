"""Loss-aware normalization for the deliberately small HR/HRV pilot."""

from app.models import ActivitySummary, CanonicalWearableSample, RecoverySummary, SleepSummary

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


def normalize_daily_summaries(
    activity_summaries: list[ActivitySummary],
    sleep_summaries: list[SleepSummary],
    recovery_summaries: list[RecoverySummary],
) -> list[CanonicalWearableSample]:
    """Emit only PRomop metrics with an exact, dated Open Wearables summary field.

    The PRomop registry is broader than the currently exposed Open Wearables
    summary contract. Metrics such as VO2 max, basal energy, and body mass are
    deliberately not inferred from unrelated fields or undated latest values.
    """
    samples: list[CanonicalWearableSample] = []

    def common(summary: ActivitySummary | SleepSummary | RecoverySummary) -> dict[str, object]:
        return {
            "observed_on": summary.date,
            "source_provider": summary.source.provider,
            "source_device": summary.source.device,
            "source_device_type": summary.source.device_type,
        }

    for summary in activity_summaries:
        fields = (
            ("steps", summary.steps, "/d", "activity.steps"),
            ("active_minutes", summary.active_minutes, "min", "activity.active_minutes"),
            ("flights_climbed", summary.floors_climbed, "{flights}", "activity.floors_climbed"),
            ("active_energy", summary.active_calories_kcal, "kcal", "activity.active_calories_kcal"),
        )
        for metric_key, value, unit, source_metric in fields:
            if value is not None:
                samples.append(CanonicalWearableSample(**common(summary), metric_key=metric_key, value=float(value), unit=unit, source_metric=source_metric))

    recovery_spo2_dates: set[date] = set()
    for summary in recovery_summaries:
        samples.extend(normalize_recovery_summaries([summary]))
        if summary.avg_spo2_percent is not None:
            recovery_spo2_dates.add(summary.date)
            samples.append(CanonicalWearableSample(**common(summary), metric_key="spo2", value=summary.avg_spo2_percent, unit="%", source_metric="recovery.avg_spo2_percent"))

    for summary in sleep_summaries:
        if summary.duration_minutes is not None:
            samples.append(CanonicalWearableSample(**common(summary), metric_key="sleep_duration", value=summary.duration_minutes / 60, unit="h", source_metric="sleep.duration_minutes"))
        if summary.avg_respiratory_rate is not None:
            samples.append(CanonicalWearableSample(**common(summary), metric_key="respiratory_rate", value=summary.avg_respiratory_rate, unit="/min", source_metric="sleep.avg_respiratory_rate"))
        if summary.avg_spo2_percent is not None and summary.date not in recovery_spo2_dates:
            samples.append(CanonicalWearableSample(**common(summary), metric_key="spo2", value=summary.avg_spo2_percent, unit="%", source_metric="sleep.avg_spo2_percent"))
    return samples
