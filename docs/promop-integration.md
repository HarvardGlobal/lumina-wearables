# PRomop integration contract

## Current, safe boundary

LUMINA Wearables implements PRomop's full 18-metric wearable registry and can
export verified, date-stamped Open Wearables daily summary fields. It uses PRomop's
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
4. Sends the resulting row list to `POST /api/v1/measurements/` or
   `POST /api/v1/observations/`, based on the PRomop-owned concept domain, with
   `measurement_type_concept`/`observation_type_concept=32865`, numeric value,
   date, source code, and unit.
5. Returns PRomop's write receipt to the caller. PRomop remains responsible for
   its row validation, idempotency/upsert semantics, audit handling, and
   PatientRecord refresh/aggregation.

The protected LUMINA route requires a separate
`LUMINA_WEARABLES_EXPORT_TOKEN`; this limits who may instruct the service to
perform an export. It must not be reused as the PRomop service token.

The complete controlled mapping list—including the local `HK-Wearable` codes,
correct Measurement/Observation table, expected units, Open Wearables source
availability, and deliberate exclusions—is maintained in
[omop-vocabulary-mapping.md](omop-vocabulary-mapping.md). The exporter rejects
an unknown mapping, incorrect unit, unavailable PRomop concept, or a value
outside PRomop's approved wearable artifact bounds.

The LOINC code is resolved by PRomop against its local OMOP vocabulary loaded
from a specific Athena release; LUMINA Wearables does not call Athena at
runtime or hard-code numeric concept IDs. A missing lookup result fails closed.
PRomop owns validation of active, standard, and domain-appropriate concepts.

## Future Archive route

For full LUMINA installations, first preserve the original Open Wearables
response and request metadata in Archive, then link any derived daily export to
that immutable record. The Archive contract must decide encrypted raw format,
source identity, consent/legal basis, retention, deletion, idempotency, and
lineage before it is enabled. It is not part of this pilot.
