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
for this export path. The single table below is the complete device-to-OMOP
sequence for every registry metric.

| LUMINA key | Four-device connection and device field | Open Wearables normalisation and summary field | LOINC/HK-Wearable → PRomop table | Unit | Status / safety rule |
| --- | --- | --- | --- | --- | --- |
| `steps` | Apple Health SDK `APPLE_STEP_COUNT`; Garmin daily `steps`; WHOOP no verified daily field; Fitbit unavailable | `steps` → ActivitySummary.`steps` | LOINC `55423-8` → Observation | `/d` | Automatic only when the dated summary field exists. |
| `active_minutes` | Apple Health SDK move/exercise time; Garmin `activeTimeInSeconds`; WHOOP/ Fitbit unverified | activity-duration normalisation → ActivitySummary.`active_minutes` | LOINC `55411-3` → Observation | `min` | Automatic only after Open Wearables emits the daily summary. |
| `resting_hr` | Apple Health `HKQuantityTypeIdentifierRestingHeartRate`; Garmin `restingHeartRateInBeatsPerMinute`; WHOOP `score.resting_heart_rate`; Fitbit unavailable | `resting_heart_rate` → RecoverySummary.`resting_heart_rate_bpm` | LOINC `40443-4` → Measurement | `/min` | Never substitute raw or average HR. |
| `hrv_sdnn` | Apple Health `HKQuantityTypeIdentifierHeartRateVariabilitySDNN`; Garmin Health Snapshot `sdrr_hrv`; WHOOP RMSSD; Fitbit unavailable | `heart_rate_variability_sdnn` → RecoverySummary.`avg_hrv_sdnn_ms` | LOINC `80404-7` → Measurement | `ms` | Automatic for Apple/Garmin only; WHOOP RMSSD is blocked. |
| `hrv_rmssd` | WHOOP `score.hrv_rmssd_milli`; Apple/Garmin/ Fitbit no verified daily route | `heart_rate_variability_rmssd` but no verified daily summary | HK-Wearable `HK-WEAR-HRV-RMSSD` → Measurement | `ms` | Registry only; never substitute for SDNN. |
| `spo2` | Apple Health `HKQuantityTypeIdentifierOxygenSaturation`; Garmin `averageSpo2`/sleep oxygen; WHOOP/Fitbit unverified | `oxygen_saturation` → RecoverySummary.`avg_spo2_percent`, sleep fallback | LOINC `59408-5` → Measurement | `%` | Recovery takes precedence when both exist. |
| `respiratory_rate` | Apple Health `HKQuantityTypeIdentifierRespiratoryRate`; Garmin sleep respiration; WHOOP/Fitbit unverified | `respiratory_rate` → SleepSummary.`avg_respiratory_rate` | LOINC `9279-1` → Measurement | `/min` | Automatic only when the dated sleep summary exists. |
| `sleep_duration` | Apple Health sleep records; Garmin sleep summary; WHOOP sleep data; Fitbit unavailable | sleep-session normalisation → SleepSummary.`duration_minutes` | LOINC `93832-4` → Observation | `h` | Lossless minutes-to-hours conversion only. |
| `vo2_max` | Apple/Android SDK can ingest VO₂ max; Garmin/WHOOP/Fitbit no verified daily route | `vo2_max`; no dated summary endpoint field | LOINC `94122-9` → Measurement | `mL/kg/min` | Registry only; not inferred from scores. |
| `distance` | Apple Health walking/running distance; Garmin `distanceInMeters`; WHOOP workout distance; Fitbit unavailable | `distance_walking_running`; generic ActivitySummary distance is not accepted | LOINC `41953-1` → Measurement | `km` | Registry only until walking context reaches a dated summary. |
| `walking_speed` | Apple Health walking speed; Garmin/WHOOP/Fitbit no verified daily route | walking-speed series; no dated summary field | LOINC `41957-2` → Measurement | `km/hr` | Registry only; requires walking context. |
| `walking_step_length` | Apple Health walking step length; Garmin/WHOOP/Fitbit no verified daily route | gait series; no dated summary field | HK-Wearable `HK-WEAR-STEP-LENGTH` → Measurement | `cm` | Registry only; requires gait context. |
| `walking_double_support_pct` | Apple Health double-support percentage; Garmin/WHOOP/Fitbit no verified daily route | gait series; no dated summary field | HK-Wearable `HK-WEAR-DBL-SUPPORT` → Measurement | `%` | Registry only; requires gait context. |
| `walking_hr_avg` | Apple Health walking HR average; Garmin/WHOOP/Fitbit no verified daily route | walking-HR series; no dated summary field | HK-Wearable `HK-WEAR-WALK-HR` → Measurement | `/min` | Registry only; requires walking context. |
| `flights_climbed` | Apple Health `HKQuantityTypeIdentifierFlightsClimbed`; Garmin `floorsClimbed`; WHOOP/Fitbit unverified | `flights_climbed` → ActivitySummary.`floors_climbed` | LOINC `100304-5` → Observation | `{flights}` | Automatic when the dated summary field exists. |
| `active_energy` | Apple Health `HKQuantityTypeIdentifierActiveEnergyBurned`; Garmin `activeKilocalories`; WHOOP/Fitbit unverified | `energy` → ActivitySummary.`active_calories_kcal` | LOINC `93819-1` → Measurement | `kcal` | Automatic when the dated summary field exists. |
| `basal_energy` | Apple Health `HKQuantityTypeIdentifierBasalEnergyBurned`; Garmin `bmrKilocalories`; WHOOP/Fitbit unverified | `basal_energy`; no separate dated summary field | HK-Wearable `HK-WEAR-BASAL-ENERGY` → Measurement | `kcal` | Registry only; never derive from total calories. |
| `body_mass` | Apple Health `HKQuantityTypeIdentifierBodyMass`; Garmin body composition; WHOOP/Fitbit unverified | `weight` → BodySummary latest weight, without measurement date | LOINC `29463-7` → Measurement | `kg` | Registry only; never assign today's date to an undated value. |
| `heart_rate` | Apple/Garmin/WHOOP time series; Fitbit unsupported here | Open Wearables `heart_rate` time series | No PRomop daily target | `bpm` | Archive candidate; high-frequency data is not daily resting HR. |

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
