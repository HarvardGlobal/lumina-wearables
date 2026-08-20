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
and **Google Health Connect → Android SDK push**. Fitbit is not the fourth
source in this matrix: it is a separate Google-owned provider whose pinned
Open Wearables adapter does not currently provide the required summary path.

## Preview metrics: four-device to PRomop matrix

This is the single complete 18-metric device-to-OMOP matrix. A dash means the
pinned Open Wearables source does not verify a safe device-specific path. “Map
only” means the PRomop mapping exists but the daily-summary route deliberately
does not emit it yet.

| LUMINA key | Apple Health variable | Garmin variable | WHOOP variable | Google Health Connect variable | Open Wearables field | LOINC/HK-Wearable | PRomop table | Current route |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `steps` | `HKQuantityTypeIdentifierStepCount` | daily `steps` | — | `STEP_COUNT` | ActivitySummary.`steps` | LOINC `55423-8` | Observation | Preview/export |
| `active_minutes` | `HKQuantityTypeIdentifierAppleExerciseTime` | daily `activeTimeInSeconds` | — | — | ActivitySummary.`active_minutes` | LOINC `55411-3` | Observation | Preview/export |
| `resting_hr` | `HKQuantityTypeIdentifierRestingHeartRate` | `restingHeartRateInBeatsPerMinute` | `score.resting_heart_rate` | `RESTING_HEART_RATE` | RecoverySummary.`resting_heart_rate_bpm` | LOINC `40443-4` | Measurement | Preview/export |
| `hrv_sdnn` | `HKQuantityTypeIdentifierHeartRateVariabilitySDNN` | Health Snapshot `sdrr_hrv` | — (RMSSD only) | — (RMSSD only) | RecoverySummary.`avg_hrv_sdnn_ms` | LOINC `80404-7` | Measurement | Preview/export for Apple/Garmin |
| `hrv_rmssd` | — | — (sleep HRV semantics not verified) | `score.hrv_rmssd_milli` | `HEART_RATE_VARIABILITY` | `heart_rate_variability_rmssd` | HK-Wearable `HK-WEAR-HRV-RMSSD` | Measurement | Map only |
| `spo2` | `HKQuantityTypeIdentifierOxygenSaturation` | `averageSpo2` / sleep oxygen | — | `OXYGEN_SATURATION` | RecoverySummary.`avg_spo2_percent`; SleepSummary fallback | LOINC `59408-5` | Measurement | Preview/export |
| `respiratory_rate` | `HKQuantityTypeIdentifierRespiratoryRate` | sleep `avgWakingRespirationValue` | — | `RESPIRATORY_RATE` | SleepSummary.`avg_respiratory_rate` | LOINC `9279-1` | Measurement | Preview/export |
| `sleep_duration` | HealthKit sleep records | sleep duration fields | sleep duration data | Health Connect sleep records | SleepSummary.`duration_minutes` | LOINC `93832-4` | Observation | Preview/export when summary is present |
| `vo2_max` | `HKQuantityTypeIdentifierVO2Max` | — | — | `VO2_MAX` | `vo2_max` series; no dated summary field | LOINC `94122-9` | Measurement | Map only |
| `distance` | `HKQuantityTypeIdentifierDistanceWalkingRunning` | `distanceInMeters` | workout `distance_meter` | `DISTANCE` | `distance_walking_running`; no safe dated walking summary | LOINC `41953-1` | Measurement | Map only |
| `walking_speed` | `HKQuantityTypeIdentifierWalkingSpeed` | — | — | — | walking-speed series; no dated summary field | LOINC `41957-2` | Measurement | Map only |
| `walking_step_length` | `HKQuantityTypeIdentifierWalkingStepLength` | — | — | — | gait series; no dated summary field | HK-Wearable `HK-WEAR-STEP-LENGTH` | Measurement | Map only |
| `walking_double_support_pct` | `HKQuantityTypeIdentifierWalkingDoubleSupportPercentage` | — | — | — | gait series; no dated summary field | HK-Wearable `HK-WEAR-DBL-SUPPORT` | Measurement | Map only |
| `walking_hr_avg` | `HKQuantityTypeIdentifierWalkingHeartRateAverage` | — | — | — | walking-HR series; no dated summary field | HK-Wearable `HK-WEAR-WALK-HR` | Measurement | Map only |
| `flights_climbed` | `HKQuantityTypeIdentifierFlightsClimbed` | daily `floorsClimbed` | — | `FLOORS_CLIMBED` | ActivitySummary.`floors_climbed` | LOINC `100304-5` | Observation | Preview/export |
| `active_energy` | `HKQuantityTypeIdentifierActiveEnergyBurned` | daily `activeKilocalories` | — | `ACTIVE_CALORIES_BURNED` | ActivitySummary.`active_calories_kcal` | LOINC `93819-1` | Measurement | Preview/export |
| `basal_energy` | `HKQuantityTypeIdentifierBasalEnergyBurned` | daily `bmrKilocalories` | — | `BASAL_METABOLIC_RATE` | `basal_energy`; no separate dated summary field | HK-Wearable `HK-WEAR-BASAL-ENERGY` | Measurement | Map only |
| `body_mass` | `HKQuantityTypeIdentifierBodyMass` | body-composition weight | — | `WEIGHT` | BodySummary latest `weight_kg`, without measurement date | LOINC `29463-7` | Measurement | Map only |

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
