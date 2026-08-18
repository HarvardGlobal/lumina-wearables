# Wearable metric cheat sheet

**Purpose:** a human-maintained lookup aid for data stewards, analysts, and
reviewers. This file is not loaded by LUMINA Wearables or any other software.
The authoritative runnable behaviour is covered by code and tests; changes to
this guide require the same semantic review as a mapping change.

**Pilot mapping version:** `0.1.0`  
**Scope:** Open Wearables daily recovery endpoint only.

| LUMINA key | Meaning and temporal resolution | Open Wearables source | Unit | PRomop status | OMOP concept in current PRomop | Rules / exclusions |
| --- | --- | --- | --- | --- | --- | --- |
| `resting_hr` | Provider-supplied daily resting heart rate | `RecoverySummary.resting_heart_rate_bpm` | `/min` | Proposed machine-to-machine import; native uploads already map it | LOINC `40443-4`, Measurement | Do not substitute raw `heart_rate` or a daily average. Preserve provider/device provenance. |
| `hrv_sdnn` | Provider-supplied daily average HRV explicitly measured as SDNN | `RecoverySummary.avg_hrv_sdnn_ms` | `ms` | Proposed machine-to-machine import; native uploads already map it | LOINC `80404-7`, Measurement | Never map RMSSD to SDNN. No imputation or aggregation beyond the source summary. |
| `hrv_rmssd` | HRV measured as RMSSD | Open Wearables time series `heart_rate_variability_rmssd` | `ms` | Deferred | Current PRomop uses local `HK-Wearable:HK-WEAR-HRV-RMSSD` | Requires an approved daily aggregation rule and explicit provenance. Not emitted by this pilot. |
| `heart_rate` | Timestamped or interval heart rate | Open Wearables time series `heart_rate` | `bpm` | Deferred / Archive candidate | None for raw samples | High-frequency source data is not promoted directly to OMOP measurements. Preserve original samples only after the Archive contract is approved. |

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
