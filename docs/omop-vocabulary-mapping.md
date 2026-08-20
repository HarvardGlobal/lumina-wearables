# Wearable vocabulary mapping strategy

## The approved conceptual flow

```text
Device / provider
  -> Open Wearables normalised field
  -> LUMINA canonical metric + semantic and provenance checks
  -> approved LOINC code
  -> local OMOP standard concept from a pinned Athena vocabulary release
  -> PRomop OMOP row
```

This sequence deliberately separates three different jobs:

1. **Open Wearables** obtains and normalises provider data. It does not decide
   that two clinically distinct measurements are interchangeable.
2. **LUMINA Wearables** validates metric meaning, unit, aggregation period,
   provider/device provenance, and mapping version. It assigns only an
   approved canonical metric key and LOINC code.
3. **PRomop** resolves the `(vocabulary_id, concept_code)` pair against its
   locally loaded OMOP vocabulary and writes the OMOP record. It also owns its
   local HK-Wearable concepts and PatientRecord aggregation.

## Athena is a vocabulary-release source, not a runtime hop

Athena is the OHDSI vocabulary catalogue and release-distribution mechanism.
It is not a live API that transforms a LOINC code into an OMOP record during
ingestion. PRomop must load a specific Athena vocabulary release into its own
OMOP `concept` tables. At write time it resolves, for example,
`(LOINC, 40443-4)` to the active local OMOP concept and uses that row's numeric
`concept_id` and domain.

The vocabulary-release metadata returned by PRomop's concept lookup must be
retained with the mapping version.
If a vocabulary update changes a concept's status, domain, or relationship,
the mapping must be re-reviewed and a new derived export created; previously
preserved source data must not be rewritten.

## Current controlled mapping allow-list

| LUMINA canonical key | Meaning | LOINC code | Expected OMOP domain | UCUM unit | Status |
| --- | --- | --- | --- | --- | --- |
| `steps` | Daily step count | `55423-8` | Observation | `/d` | Direct Open Wearables activity-summary export |
| `active_minutes` | Daily activity duration | `55411-3` | Observation | `min` | Direct Open Wearables activity-summary export |
| `resting_hr` | Daily resting heart rate | `40443-4` | Measurement | `/min` | Direct recovery-summary export |
| `hrv_sdnn` | Daily HRV explicitly measured as SDNN | `80404-7` | Measurement | `ms` | Direct for Apple/Garmin only; WHOOP RMSSD guard remains |
| `hrv_rmssd` | HRV measured as RMSSD | `HK-WEAR-HRV-RMSSD` | Measurement | `ms` | Export mapping implemented; no verified daily summary source in this pin |
| `spo2` | Daily oxygen saturation | `59408-5` | Measurement | `%` | Direct recovery summary, otherwise sleep summary |
| `respiratory_rate` | Daily respiratory rate | `9279-1` | Measurement | `/min` | Direct sleep-summary export |
| `sleep_duration` | Daily main-sleep duration | `93832-4` | Observation | `h` | Direct sleep-summary export; minutes converted to hours |
| `vo2_max` | VO₂ max | `94122-9` | Measurement | `mL/kg/min` | Export mapping implemented; no verified summary field in this pin |
| `distance` | Walking distance | `41953-1` | Measurement | `km` | Export mapping implemented; generic activity distance is not assumed walking |
| `walking_speed` | Walking speed | `41957-2` | Measurement | `km/hr` | Export mapping implemented; no verified summary field in this pin |
| `walking_step_length` | Walking step length | `HK-WEAR-STEP-LENGTH` | Measurement | `cm` | Export mapping implemented; no verified summary field in this pin |
| `walking_double_support_pct` | Walking double-support | `HK-WEAR-DBL-SUPPORT` | Measurement | `%` | Export mapping implemented; no verified summary field in this pin |
| `walking_hr_avg` | Walking mean HR | `HK-WEAR-WALK-HR` | Measurement | `/min` | Export mapping implemented; no verified summary field in this pin |
| `flights_climbed` | Daily floors/flights climbed | `100304-5` | Observation | `{flights}` | Direct Open Wearables activity-summary export |
| `active_energy` | Daily active energy | `93819-1` | Measurement | `kcal` | Direct Open Wearables activity-summary export |
| `basal_energy` | Daily basal energy | `HK-WEAR-BASAL-ENERGY` | Measurement | `kcal` | Export mapping implemented; total calories are not split into basal energy |
| `body_mass` | Body mass | `29463-7` | Measurement | `kg` | Export mapping implemented; current body summary lacks measurement date |

The codes are a controlled mapping decision, not a value transformation. A
daily value is accepted only when its source field truly has the stated
meaning and temporal resolution. A raw or average heart-rate sample is not
daily resting heart rate; RMSSD is not SDNN.

## Write-time acceptance rules

The implemented PRomop integration does the following before a row is written:

1. Require an explicitly authorised PRomop person ID; never derive identity
   from a provider user ID or device ID.
2. Accept only an approved LUMINA canonical key, expected unit, and daily date.
3. Resolve the declared LOINC code using both `vocabulary_id = LOINC` and
   `concept_code`; a missing mapping fails closed.
4. Send the resolved local `concept_id`, source code/value/unit, and
   `measurement_type_concept=32865` to PRomop, returning its receipt and the
   lookup's vocabulary-version metadata.
5. Leave concept status/domain enforcement, idempotency/upserts, auditing, and
   PatientRecord aggregation to PRomop's existing API implementation.

## Archive relationship

For a full LUMINA deployment, the future Archive-linked route will preserve the
original Open Wearables response before its derived metric is promoted. That
derived record must link to the raw object, Open Wearables version, LUMINA
mapping version, Athena vocabulary release, device/provider context, and
PRomop receipt. The separate protected PRomop export route is implemented and
tested; Archive preservation remains deferred until its dedicated authenticated
contract is implemented and tested.
