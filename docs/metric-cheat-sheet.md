# Wearable metric cheat sheet

**Purpose:** a human-maintained lookup aid for data stewards, analysts, and
reviewers. This file is not loaded by LUMINA Wearables or any other software.
The authoritative runnable behaviour is covered by code and tests; changes to
this guide require the same semantic review as a mapping change.

**Mapping registry:** all 18 current PRomop wearable metrics; only
source-equivalent, date-stamped Open Wearables fields are emitted automatically.

**Pinned Open Wearables source:** `0.7.0` at commit
`cb3ad1fd1141138179d27f7e787a1d0049a071c9`

**Scope:** the protected exporter implements all 18 current PRomop wearable
metrics. It automatically emits only those with an exact, date-stamped Open
Wearables summary field; this service does not write to Archive yet.

## Standardisation path

```text
Device/provider -> Open Wearables -> LUMINA semantic validation -> LOINC code
-> local OMOP concept from a pinned Athena vocabulary release -> PRomop/OMOP
```

Athena supplies the OMOP vocabulary release loaded into PRomop; it is not a
live translation step. PRomop resolves the approved `(vocabulary_id,
concept_code)` pair to its local numeric OMOP `concept_id` before a write. The
export receipt returns the vocabulary-version metadata supplied by PRomop. See
[omop-vocabulary-mapping.md](omop-vocabulary-mapping.md) for the validation and
provenance rules.

The four device connections are: **Apple Health → iOS HealthKit SDK push**;
**Garmin → OAuth 2.0 plus webhook**; **WHOOP → OAuth 2.0 plus webhook/poll**;
and **Fitbit → OAuth 2.0 with PKCE polling**. The Fitbit connection exists
upstream, but the pinned release does not provide verified daily-summary fields
for this export path.

## Preview metrics: four-device to PRomop matrix

This is the single operational table for the fields that the current preview
and `daily-summaries/export` route can emit. A dash means that the pinned Open
Wearables source does not verify that device-specific path.

| LUMINA key | Apple Health variable | Garmin variable | WHOOP variable | Fitbit variable | Open Wearables field | LOINC/HK-Wearable | PRomop table |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `steps` | `HKQuantityTypeIdentifierStepCount` | daily `steps` | — | — | ActivitySummary.`steps` | LOINC `55423-8` | Observation |
| `active_minutes` | `HKQuantityTypeIdentifierAppleExerciseTime` | daily `activeTimeInSeconds` | — | — | ActivitySummary.`active_minutes` | LOINC `55411-3` | Observation |
| `resting_hr` | `HKQuantityTypeIdentifierRestingHeartRate` | `restingHeartRateInBeatsPerMinute` | `score.resting_heart_rate` | — | RecoverySummary.`resting_heart_rate_bpm` | LOINC `40443-4` | Measurement |
| `hrv_sdnn` | `HKQuantityTypeIdentifierHeartRateVariabilitySDNN` | Health Snapshot `sdrr_hrv` | — (RMSSD only) | — | RecoverySummary.`avg_hrv_sdnn_ms` | LOINC `80404-7` | Measurement |
| `spo2` | `HKQuantityTypeIdentifierOxygenSaturation` | daily `averageSpo2` / sleep oxygen | — | — | RecoverySummary.`avg_spo2_percent`; SleepSummary fallback | LOINC `59408-5` | Measurement |
| `respiratory_rate` | `HKQuantityTypeIdentifierRespiratoryRate` | sleep `avgWakingRespirationValue` | — | — | SleepSummary.`avg_respiratory_rate` | LOINC `9279-1` | Measurement |
| `sleep_duration` | HealthKit sleep records | sleep duration fields | sleep duration data | — | SleepSummary.`duration_minutes` | LOINC `93832-4` | Observation |
| `flights_climbed` | `HKQuantityTypeIdentifierFlightsClimbed` | daily `floorsClimbed` | — | — | ActivitySummary.`floors_climbed` | LOINC `100304-5` | Observation |
| `active_energy` | `HKQuantityTypeIdentifierActiveEnergyBurned` | daily `activeKilocalories` | — | — | ActivitySummary.`active_calories_kcal` | LOINC `93819-1` | Measurement |

The full 18-metric registry, including mappings which are deliberately not in
the preview because their pinned Open Wearables source is not semantically
exact or does not carry a valid date, is in
[omop-vocabulary-mapping.md](omop-vocabulary-mapping.md).

### Current upstream safety restriction

At the pinned Open Wearables revision, its daily recovery response puts
WHOOP's `hrv_rmssd_milli` into a field labelled `avg_hrv_sdnn_ms`. LUMINA
Wearables therefore returns WHOOP resting HR but rejects that field for SDNN.
This guard prevents a clinically meaningful metric swap while the upstream
response contract is corrected.

## Non-negotiable semantic rules

1. SDNN and RMSSD are distinct metrics. A missing SDNN is not replaced by RMSSD,
   and vice versa.
2. A provider's resting-heart-rate summary is distinct from raw or average
   heart rate.
3. A missing value is omitted—not inferred as zero or carried forward.
4. Retain source provider, source device, source metric name, and the fact that
   the record is daily.
5. Add a new metric only with its definition, source field, unit, temporal
   resolution, validation, PRomop concept decision, and Archive treatment
   reviewed together.
