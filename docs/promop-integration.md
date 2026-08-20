# PRomop integration contract

## Current, safe boundary

LUMINA Wearables `1.1.4` previews and can explicitly export two exact daily
metrics from Open Wearables: `resting_hr` and `hrv_sdnn`. It uses PRomop's
existing service-token-protected concept lookup and generic OMOP write APIs.
It never accesses the PRomop database directly and does not use PRomop's
separate native Garmin FIT/Apple Health ZIP upload endpoint.

## Implemented PRomop-owned APIs

For each export, LUMINA Wearables:

1. Requires a caller-selected, positive PRomop `person_id`; it never derives a
   PRomop identity from an Open Wearables UUID or device ID.
2. Accepts only the service's static approved mapping allow-list, metric unit,
   and daily temporal resolution.
3. Calls `GET /api/v1/concepts/lookup/?lookup=LOINC:<code>&include_versions=1`
   using PRomop's service token. This resolves the code to that deployment's
   local concept ID and returns vocabulary-version metadata.
4. Sends the resulting row list to `POST /api/v1/measurements/` with PRomop's
   service token, `measurement_type_concept=32865`, numeric value, date,
   source LOINC code, and unit.
5. Returns PRomop's write receipt to the caller. PRomop remains responsible for
   its row validation, idempotency/upsert semantics, audit handling, and
   PatientRecord refresh/aggregation.

The protected LUMINA route requires a separate
`LUMINA_WEARABLES_EXPORT_TOKEN`; this limits who may instruct the service to
perform an export. It must not be reused as the PRomop service token.

| Canonical key | Standard code | PRomop target | Unit |
| --- | --- | --- | --- |
| `resting_hr` | LOINC `40443-4` | Measurement | `/min` |
| `hrv_sdnn` | LOINC `80404-7` | Measurement | `ms` |

The LOINC code is resolved by PRomop against its local OMOP vocabulary loaded
from a specific Athena release; LUMINA Wearables does not call Athena at
runtime or hard-code numeric concept IDs. A missing lookup result fails closed.
PRomop owns validation of active, standard, and domain-appropriate concepts.
The full strategy is in [omop-vocabulary-mapping.md](omop-vocabulary-mapping.md).

## Future Archive route

For full LUMINA installations, first preserve the original Open Wearables
response and request metadata in Archive, then link any derived daily export to
that immutable record. The Archive contract must decide encrypted raw format,
source identity, consent/legal basis, retention, deletion, idempotency, and
lineage before it is enabled. It is not part of this pilot.
