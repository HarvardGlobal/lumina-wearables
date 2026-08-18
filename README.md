# LUMINA Wearables

LUMINA Wearables is a small, independently deployable boundary between
[Open Wearables](https://github.com/the-momentum/open-wearables) and health-data
platforms. It is designed to be useful to PRomop adopters who do **not** run
the wider LUMINA Core stack.

Current release: `1.1.0`.

## First pilot: daily resting HR and HRV-SDNN

The pilot reads Open Wearables' daily recovery summaries and returns only two
semantically exact, daily records:

| LUMINA key | Open Wearables field | Unit | Why it is included |
| --- | --- | --- | --- |
| `resting_hr` | `resting_heart_rate_bpm` | `/min` | Provider-supplied daily resting heart rate |
| `hrv_sdnn` | `avg_hrv_sdnn_ms` | `ms` | Provider-supplied daily HRV explicitly labelled SDNN |

No calculation, imputation, unit conversion, or silent substitution is made.
In particular, raw continuous heart rate is not a daily resting-HR measure,
and HRV-RMSSD is not SDNN. They remain out of scope until their aggregation
and vocabulary rules are separately approved.

The full human lookup table is [docs/metric-cheat-sheet.md](docs/metric-cheat-sheet.md).
It is documentation only; no service reads it at runtime.

## Run it by itself

First deploy and configure Open Wearables according to its upstream guidance.
This service expects an API base URL that includes `/api/v1` and an Open
Wearables API key. Do not commit either value.

```bash
docker build -t lumina-wearables .
docker run --rm -p 8300:8300 \
  -e OPEN_WEARABLES_BASE_URL=https://open-wearables.example/api/v1 \
  -e OPEN_WEARABLES_API_KEY=replace-with-secret \
  lumina-wearables

curl http://localhost:8300/health
```

To preview one user's daily canonical samples, call:

```bash
curl 'http://localhost:8300/api/v1/open-wearables/users/<open-wearables-user-uuid>/daily-recovery?start_date=2026-08-01&end_date=2026-08-17'
```

The endpoint is deliberately read-only and returns `"write_status":
"preview-only"`. It neither writes an OMOP row nor stores data in Archive.
It must be protected by authenticated network access before a real deployment;
the development service itself does not provide user authentication.

Run the tests with:

```bash
python -m pytest -q
```

## PRomop and LUMINA Core paths

PRomop's current wearable endpoint accepts native Garmin FIT and Apple Health
ZIP uploads. It does not expose a documented authenticated endpoint that
accepts canonical daily samples from this service. Consequently, this release
does **not** fake a PRomop write by accessing its database or converting data
into a different provider's file format.

The next approved integration step is a PRomop-owned, authenticated import
contract for the two canonical daily records. Its required fields, identity
binding, idempotency, provenance, and OMOP mapping decisions are documented in
[docs/promop-integration.md](docs/promop-integration.md). Once PRomop supplies
that contract, this service can add a tested exporter without requiring
LUMINA Core.

For a full LUMINA deployment, original Open Wearables responses can later be
preserved in Archive before selected daily metrics are promoted to PRomop.
That Archive path is also intentionally deferred: it needs an approved raw
payload/provenance and retention contract, not an implicit copy of data.

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
