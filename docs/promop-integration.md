# PRomop integration contract: proposed next step

## Current, safe boundary

LUMINA Wearables `1.1.3` produces read-only previews of two exact daily metrics
from Open Wearables: `resting_hr` and `hrv_sdnn`. It has no PRomop database
credentials and does not write to PRomop.

That is intentional. Current PRomop wearable ingestion accepts provider-native
Garmin FIT and Apple Health ZIP uploads. A generic service-to-service endpoint
for canonical daily records has not been agreed or implemented.

## Required PRomop-owned API before writes are enabled

PRomop should define and own an authenticated endpoint with, at minimum:

1. A PRomop person ID resolved under service authentication; never infer it
   from an Open Wearables UUID.
2. An explicit mapping version and approved metric key (`resting_hr` or
   `hrv_sdnn`), value, UCUM unit, and day-level temporal resolution.
3. Source provider, device metadata, source metric name, collection date, and
   a content/idempotency key.
4. An all-or-nothing validation response that returns created or reused OMOP
   measurement identifiers and a durable receipt.
5. Authorisation, audit events, rate/size limits, and a policy for correction,
   deletion, retention, and replay.

The expected initial OMOP decisions should be reviewed by the PRomop maintainers:

| Canonical key | Intended standard concept | Domain | Unit |
| --- | --- | --- | --- |
| `resting_hr` | LOINC `40443-4` | Measurement | `/min` |
| `hrv_sdnn` | LOINC `80404-7` | Measurement | `ms` |

## Future Archive route

For full LUMINA installations, first persist the original Open Wearables
response and request metadata in Archive, then link any derived daily export to
that immutable record. The Archive contract must decide encrypted raw format,
source identity, consent/legal basis, retention, deletion, idempotency, and
lineage before it is enabled. It is not part of this pilot.
