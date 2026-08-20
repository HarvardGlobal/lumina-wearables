# Wearable metric cheat sheet

**Purpose:** a human-maintained lookup aid for data stewards, analysts, and
reviewers. This file is not loaded by LUMINA Wearables or any other software.
The authoritative runnable behaviour is covered by code and tests; changes to
this guide require the same semantic review as a mapping change.

**Pilot mapping version:** `0.1.1`

**Pinned Open Wearables source:** `0.7.0` at commit
`cb3ad1fd1141138179d27f7e787a1d0049a071c9`

**Scope:** initial read-only LUMINA flow. No data is yet written to PRomop or
Archive by this service.

## Standardisation path

```text
Device/provider -> Open Wearables -> LUMINA semantic validation -> LOINC code
-> local OMOP concept from a pinned Athena vocabulary release -> PRomop/OMOP
```

Athena supplies the OMOP vocabulary release loaded into PRomop; it is not a
live translation step. PRomop resolves the approved `(vocabulary_id,
concept_code)` pair to its local numeric OMOP `concept_id` before a write. See
[omop-vocabulary-mapping.md](omop-vocabulary-mapping.md) for the required
release, validation, and provenance rules.

| LUMINA key | Meaning and temporal resolution | Open Wearables source | Unit | PRomop status | OMOP concept in current PRomop | Rules / exclusions |
| --- | --- | --- | --- | --- | --- | --- |
| `resting_hr` | Provider-supplied daily resting heart rate | `RecoverySummary.resting_heart_rate_bpm` | `/min` | Exporter allow-list; writes through PRomop's generic Measurement API | LOINC `40443-4`, Measurement | Do not substitute raw `heart_rate` or a daily average. Preserve provider/device provenance. |
| `hrv_sdnn` | Provider-supplied daily average HRV explicitly measured as SDNN | `RecoverySummary.avg_hrv_sdnn_ms` | `ms` | Exporter allow-list; writes through PRomop's generic Measurement API | LOINC `80404-7`, Measurement | Never map RMSSD to SDNN. No imputation or aggregation beyond the source summary. |
| `hrv_rmssd` | HRV measured as RMSSD | Open Wearables time series `heart_rate_variability_rmssd` | `ms` | Deferred | Current PRomop uses local `HK-Wearable:HK-WEAR-HRV-RMSSD` | Requires an approved daily aggregation rule and explicit provenance. Not emitted by this pilot. |
| `heart_rate` | Timestamped or interval heart rate | Open Wearables time series `heart_rate` | `bpm` | Deferred / Archive candidate | None for raw samples | High-frequency source data is not promoted directly to OMOP measurements. Preserve original samples only after the Archive contract is approved. |

## Device-to-LUMINA flow

This is the operational lookup table: it records the source variable name,
Open Wearables' normalized name, and the LUMINA treatment. “Ready” means it is
safe for the current pilot and, for the two approved metrics, eligible for an
explicit protected PRomop export—not that every provider supplies every metric.

| Device / provider | Connection into Open Wearables | Source device or provider variable | Open Wearables normalized variable | LUMINA name and current treatment | Status |
| --- | --- | --- | --- | --- | --- |
| Apple Health | iOS HealthKit SDK push | `HKQuantityTypeIdentifierRestingHeartRate` | `resting_heart_rate` → recovery `resting_heart_rate_bpm` | `resting_hr`, daily, `/min` | Ready |
| Apple Health | iOS HealthKit SDK push | `HKQuantityTypeIdentifierHeartRateVariabilitySDNN` | `heart_rate_variability_sdnn` → recovery `avg_hrv_sdnn_ms` | `hrv_sdnn`, daily, `ms` | Ready |
| Apple Health | iOS HealthKit SDK push | `HKQuantityTypeIdentifierHeartRate` | `heart_rate` | Raw heart rate; retained only in a future Archive path | Deferred |
| Garmin | OAuth 2.0 + webhook | `restingHeartRateInBeatsPerMinute` from wellness dailies | `resting_heart_rate` → recovery `resting_heart_rate_bpm` | `resting_hr`, daily, `/min` | Ready |
| Garmin | OAuth 2.0 + webhook | Health Snapshot `summaries[].summaryType = sdrr_hrv`, `avgValue` | `heart_rate_variability_sdnn` → recovery `avg_hrv_sdnn_ms` | `hrv_sdnn`, daily, `ms` | Ready |
| Garmin | OAuth 2.0 + webhook | `timeOffsetHeartRateSamples` / activity `heartRate` | `heart_rate` | Raw heart rate; future Archive-only path | Deferred |
| WHOOP | OAuth 2.0 + webhook/poll | `score.resting_heart_rate` | `resting_heart_rate` | `resting_hr`, daily, `/min` | Ready |
| WHOOP | OAuth 2.0 + webhook/poll | `score.hrv_rmssd_milli` | `heart_rate_variability_rmssd` | `hrv_rmssd`, `ms`; no approved daily aggregation/export yet | Deferred |
| Fitbit | OAuth 2.0 + PKCE polling | Workout `activities[].averageHeartRate` | Workout `heart_rate_avg` only | Not a daily resting-HR or HRV source | Not ready |
| Google Health Connect (Android) | Android SDK push | `RESTING_HEART_RATE` | `resting_heart_rate` | `resting_hr`, daily, `/min` | Future addition; not wired in LUMINA yet |
| Google Health Connect (Android) | Android SDK push | `HEART_RATE_VARIABILITY` (RMSSD) | `heart_rate_variability_rmssd` | `hrv_rmssd`, `ms`; requires daily aggregation/export decision | Deferred |

### Provider availability decision

- **Apple Health and Garmin:** yes, begin with daily resting HR and SDNN as the
  first two statistics once their Open Wearables connections are configured.
- **WHOOP:** begin with daily resting HR. Its HRV is RMSSD—not SDNN—and remains
  distinct until the RMSSD promotion decision is approved.
- **Fitbit:** no, not for the initial daily HR/HRV pilot. At this pinned Open
  Wearables release it provides workouts only; Fitbit sleep, intraday heart
  rate, and HRV processing are not implemented.
- **Google devices:** distinguish Fitbit from Google Health Connect. Health
  Connect can provide resting HR and RMSSD, but it is a later Android SDK path,
  not a substitute for Fitbit support.

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
