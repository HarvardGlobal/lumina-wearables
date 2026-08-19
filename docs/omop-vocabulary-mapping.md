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
   locally loaded OMOP vocabulary and writes the OMOP record.

## Athena is a vocabulary-release source, not a runtime hop

Athena is the OHDSI vocabulary catalogue and release-distribution mechanism.
It is not a live API that transforms a LOINC code into an OMOP record during
ingestion. PRomop must load a specific Athena vocabulary release into its own
OMOP `concept` tables. At write time it resolves, for example,
`(LOINC, 40443-4)` to the active local OMOP concept and uses that row's numeric
`concept_id` and domain.

The vocabulary release identifier must be retained with the mapping version.
If a vocabulary update changes a concept's status, domain, or relationship,
the mapping must be re-reviewed and a new derived export created; previously
preserved source data must not be rewritten.

## Initial approved mapping candidates

| LUMINA canonical key | Meaning | LOINC code | Expected OMOP domain | UCUM unit | Status |
| --- | --- | --- | --- | --- | --- |
| `resting_hr` | Provider-supplied daily resting heart rate | `40443-4` | Measurement | `/min` | Candidate for the first authenticated import |
| `hrv_sdnn` | Provider-supplied daily HRV explicitly measured as SDNN | `80404-7` | Measurement | `ms` | Candidate for the first authenticated import |
| `hrv_rmssd` | HRV measured as RMSSD | No approved standard LOINC mapping in this project | To be decided | `ms` | Deferred; never substitute for SDNN |

The codes are a controlled mapping decision, not a value transformation. A
daily value is accepted only when its source field truly has the stated
meaning and temporal resolution. A raw or average heart-rate sample is not
daily resting heart rate; RMSSD is not SDNN.

## Write-time acceptance rules

Before PRomop writes an OMOP row, its authenticated import contract must:

1. Require an explicitly authorised PRomop person ID; never derive identity
   from a provider user ID or device ID.
2. Accept only an approved LUMINA canonical key, mapping version, value, UCUM
   unit, day-level date, provider/device provenance, and idempotency key.
3. Resolve the declared LOINC code using both `vocabulary_id = LOINC` and
   `concept_code`, then reject inactive, non-standard, missing, or
   wrong-domain concepts.
4. Record the resolved OMOP `concept_id`, vocabulary-release identifier,
   source code/value/unit, and all source provenance in the resulting OMOP
   row and promotion receipt.
5. Return an all-or-nothing receipt containing created or reused OMOP IDs.

## Archive relationship

For a full LUMINA deployment, Archive preserves the original Open Wearables
response before any derived metric is promoted. The derived record must link to
the raw object, Open Wearables version, LUMINA mapping version, Athena
vocabulary release, device/provider context, and PRomop receipt. The current
Wearables API remains preview-only until these authenticated Archive and PRomop
contracts are implemented and tested.
