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

| LUMINA key | Meaning and temporal resolution | Open Wearables source | Unit | PRomop status | OMOP concept in current PRomop | Rules / exclusions |
| --- | --- | --- | --- | --- | --- | --- |
| `steps` | Daily step count | ActivitySummary.`steps` | `/d` | Automatic export | LOINC `55423-8`, Observation | Exact daily summary field. |
| `active_minutes` | Daily activity duration | ActivitySummary.`active_minutes` | `min` | Automatic export | LOINC `55411-3`, Observation | Exact daily summary field. |
| `resting_hr` | Daily resting heart rate | RecoverySummary.`resting_heart_rate_bpm` | `/min` | Automatic export | LOINC `40443-4`, Measurement | Never substitute raw or average HR. |
| `hrv_sdnn` | Daily HRV explicitly labelled SDNN | RecoverySummary.`avg_hrv_sdnn_ms` | `ms` | Automatic export for Apple/Garmin | LOINC `80404-7`, Measurement | WHOOP RMSSD is blocked; never substitute RMSSD. |
| `hrv_rmssd` | Daily HRV measured as RMSSD | No verified daily summary field | `ms` | Registry/export mapping only | HK-Wearable `HK-WEAR-HRV-RMSSD`, Measurement | Await a verified daily RMSSD source contract. |
| `spo2` | Daily oxygen saturation | RecoverySummary.`avg_spo2_percent`; SleepSummary fallback | `%` | Automatic export | LOINC `59408-5`, Measurement | Recovery takes precedence when both exist. |
| `respiratory_rate` | Daily respiratory rate | SleepSummary.`avg_respiratory_rate` | `/min` | Automatic export | LOINC `9279-1`, Measurement | Exact sleep-summary field. |
| `sleep_duration` | Daily main-sleep duration | SleepSummary.`duration_minutes` | `h` | Automatic export | LOINC `93832-4`, Observation | Lossless minutes-to-hours conversion only. |
| `vo2_max` | VO₂ max | No verified summary field | `mL/kg/min` | Registry/export mapping only | LOINC `94122-9`, Measurement | Not inferred from activity or score data. |
| `distance` | Walking distance | Generic activity distance is not accepted | `km` | Registry/export mapping only | LOINC `41953-1`, Measurement | Do not label non-walking distance as walking. |
| `walking_speed` | Daily walking speed | No verified summary field | `km/hr` | Registry/export mapping only | LOINC `41957-2`, Measurement | Requires source-confirmed walking context. |
| `walking_step_length` | Walking step length | No verified summary field | `cm` | Registry/export mapping only | HK-Wearable `HK-WEAR-STEP-LENGTH`, Measurement | Requires source-confirmed gait context. |
| `walking_double_support_pct` | Walking double-support percentage | No verified summary field | `%` | Registry/export mapping only | HK-Wearable `HK-WEAR-DBL-SUPPORT`, Measurement | Requires source-confirmed gait context. |
| `walking_hr_avg` | Walking mean HR | No verified summary field | `/min` | Registry/export mapping only | HK-Wearable `HK-WEAR-WALK-HR`, Measurement | Requires source-confirmed walking context. |
| `flights_climbed` | Daily floors/flights climbed | ActivitySummary.`floors_climbed` | `{flights}` | Automatic export | LOINC `100304-5`, Observation | Upstream defines floors from elevation. |
| `active_energy` | Daily active energy | ActivitySummary.`active_calories_kcal` | `kcal` | Automatic export | LOINC `93819-1`, Measurement | Exact active-energy field. |
| `basal_energy` | Daily basal energy | No separate basal-energy field | `kcal` | Registry/export mapping only | HK-Wearable `HK-WEAR-BASAL-ENERGY`, Measurement | Never derive from total calories. |
| `body_mass` | Body mass | BodySummary latest weight lacks measurement date | `kg` | Registry/export mapping only | LOINC `29463-7`, Measurement | Never assign today's date to an undated value. |
| `heart_rate` | Timestamped/interval heart rate | Open Wearables time series `heart_rate` | `bpm` | Archive candidate, not registry export | None | High-frequency samples are not daily resting-HR Measurements. |

## Device-to-LUMINA flow

This is the operational lookup table: it records the source variable name,
Open Wearables' normalized name, and the LUMINA treatment. “Ready” means it is
safe for the current pilot and eligible for an explicit protected PRomop
export—not that every provider supplies every registry metric.

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

- **Apple Health and Garmin:** their configured Open Wearables activity, sleep,
  and recovery summaries can export the verified fields in the full table.
  SDNN remains restricted to these providers.
- **WHOOP:** its verified daily summary fields can export, but its HRV is
  RMSSD—not SDNN—and remains blocked until a verified daily RMSSD contract is
  available.
- **Fitbit:** no, not for the initial daily HR/HRV pilot. At this pinned Open
  Wearables release it provides workouts only; Fitbit sleep, intraday heart
  rate, and HRV processing are not implemented.
- **Google devices:** distinguish Fitbit from Google Health Connect. Health
  Connect may provide resting HR and RMSSD, but it remains a later Android SDK
  path and is not a substitute for Fitbit support.

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
