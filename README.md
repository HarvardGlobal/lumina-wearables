# LUMINA Wearables

LUMINA Wearables is a small, independently deployable boundary between
[Open Wearables](https://github.com/the-momentum/open-wearables) and health-data
platforms. It is designed to be useful to PRomop adopters who do **not** run
the wider LUMINA Core stack.

## Project status and open source

This is research health-data infrastructure, not clinical decision support.
Deployers remain responsible for the privacy, security, governance, validation,
and regulatory controls required for their setting.

LUMINA Wearables is licensed under [Apache-2.0](LICENSE). Please read
[CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and the
[Code of Conduct](CODE_OF_CONDUCT.md) before participating.

Current release: `1.2.2`.

## Daily-summary export and full PRomop registry

The service implements PRomop's full current wearable registry (18 controlled
LOINC/HK-Wearable mappings). Its automatic Open Wearables route emits only the
source-equivalent, date-stamped fields currently exposed by activity, sleep,
and recovery summaries:

| LUMINA key | Open Wearables field | Unit | Why it is included |
| --- | --- | --- | --- |
| `resting_hr` | `resting_heart_rate_bpm` | `/min` | Provider-supplied daily resting heart rate |
| `hrv_sdnn` | `avg_hrv_sdnn_ms` | `ms` | Provider-supplied daily HRV explicitly labelled SDNN |
| `steps` | activity `steps` | `/d` | Provider-supplied daily step count |
| `active_minutes` | activity `active_minutes` | `min` | Provider-supplied daily activity duration |
| `flights_climbed` | activity `floors_climbed` | `{flights}` | Provider-supplied daily floors climbed |
| `active_energy` | activity `active_calories_kcal` | `kcal` | Provider-supplied daily active energy |
| `sleep_duration` | sleep `duration_minutes` | `h` | Main-sleep duration, converted from minutes |
| `respiratory_rate` | sleep `avg_respiratory_rate` | `/min` | Provider-supplied daily sleep respiratory rate |
| `spo2` | recovery/sleep `avg_spo2_percent` | `%` | Daily oxygen saturation; recovery takes precedence |

No calculation, imputation, or silent substitution is made. The sole unit
conversion is the lossless `duration_minutes ÷ 60` conversion required for
PRomop's approved sleep-duration unit of hours.
In particular, raw continuous heart rate is not a daily resting-HR measure,
and HRV-RMSSD is not SDNN. They remain out of scope until their aggregation
and vocabulary rules are separately approved.

The full human lookup table is [docs/metric-cheat-sheet.md](docs/metric-cheat-sheet.md).
It is documentation only; no service reads it at runtime.

The table includes the full source-device → Open Wearables → LUMINA flow for
Apple Health, Garmin, WHOOP, Fitbit, and Google Health Connect. It also states
which providers are ready for each pilot statistic and which are not.

The implemented standardisation route is **Open Wearables → LUMINA semantic
validation → LOINC code → PRomop's locally loaded Athena vocabulary concept →
PRomop Measurement**. Athena is a vocabulary-release source, not a live runtime
conversion service. The complete strategy and current controlled mapping
allow-list are in
[docs/omop-vocabulary-mapping.md](docs/omop-vocabulary-mapping.md).

## Run it by itself

First deploy and configure Open Wearables according to its upstream guidance.
This service expects an API base URL that includes `/api/v1` and an Open
Wearables API key. Do not commit either value.

```bash
docker build -t lumina-wearables .
docker run --rm -p 8300:8300 \
  -e OPEN_WEARABLES_BASE_URL=https://open-wearables.example/api/v1 \
  -e OPEN_WEARABLES_API_KEY=replace-with-secret \
  -e PROMOP_BASE_URL=https://promop.example.org \
  -e PROMOP_SERVICE_AUTH_TOKEN=replace-with-promop-service-secret \
  -e LUMINA_WEARABLES_EXPORT_TOKEN=replace-with-a-separate-secret \
  lumina-wearables

curl http://localhost:8300/health
```

To preview the full verified daily-summary set, call:

```bash
curl 'http://localhost:8300/api/v1/open-wearables/users/<open-wearables-user-uuid>/daily-summaries?start_date=2026-08-01&end_date=2026-08-17'
```

The preview endpoint is deliberately read-only and returns `"write_status":
"preview-only"`. It neither writes an OMOP row nor stores data in Archive.

## Export to PRomop

The protected export endpoint sends only approved daily samples to PRomop's
existing concept-lookup and generic Measurement/Observation APIs. It resolves LOINC codes
against the vocabulary loaded by that PRomop deployment at write time; it does
not hard-code Athena numeric concept IDs. The request must supply an explicit,
authorised PRomop person ID. An Open Wearables user UUID is never treated as a
clinical identity.

```bash
curl -X POST \
  'http://localhost:8300/api/v1/promop/persons/<promop-person-id>/open-wearables/users/<open-wearables-user-uuid>/daily-summaries/export?start_date=2026-08-01&end_date=2026-08-17' \
  -H 'Authorization: Bearer <LUMINA_WEARABLES_EXPORT_TOKEN>'
```

`LUMINA_WEARABLES_EXPORT_TOKEN` protects this service endpoint and must be
different from `PROMOP_SERVICE_AUTH_TOKEN`, which is used only from Wearables
to PRomop. The result includes the PRomop write receipt and vocabulary-version
metadata. PRomop applies its own idempotent write and PatientRecord refresh
behaviour. See [docs/promop-integration.md](docs/promop-integration.md) for the
exact boundary and fields.

Run the tests with:

```bash
python -m pytest -q
```

## PRomop and LUMINA Core paths

This service uses PRomop's existing authenticated generic APIs; it does not
access the PRomop database or convert records into a Garmin FIT/Apple Health
file. PRomop retains ownership of the OMOP schema, its Athena-loaded vocabulary
tables, local HK-Wearable concepts, and PatientRecord aggregation.

For a full LUMINA deployment, original Open Wearables responses will later be
preserved in Archive before selected daily metrics are promoted to PRomop.
That Archive path remains intentionally deferred: it needs an approved raw
payload/provenance and retention contract, not an implicit copy of data.
The required separation of raw source, device context, and mapping versions is
described in Core's `docs/architecture/wearable-data-lineage.md`.

## Versioning and Core orchestration

LUMINA Core pins this repository and Open Wearables by immutable commit SHA in
`config/components.yaml`. `make setup` from the Core repository materializes
those exact revisions in `.lumina/components`; it never follows a mutable
branch. Open Wearables remains a separately configured deployment because its
upstream application owns its own OAuth, admin, PostgreSQL, Redis, and worker
lifecycle. This preserves reproducible source/version selection without
silently starting an unconfigured identity system.

## Technical notes

- Open Wearables is the acquisition/normalization layer; this service retains
  the returned provider and device provenance.
- The response's `source_provider`, `source_device`, `source_device_type`, and
  source metric are carried with every returned record.
- Neither LUMINA Wearables nor the cheat sheet is a clinical decision-support
  tool. Treat wearable measurements as context subject to clinical governance.
