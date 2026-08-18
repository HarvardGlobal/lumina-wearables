# Contributing to LUMINA Wearables

Thank you for helping improve LUMINA Wearables. Please open an issue before
starting a substantial change so maintainers can agree the data semantics,
privacy impact, and scope.

## Development and checks

Use Python 3.12 or later. Create an isolated environment, install the pinned
dependencies, and run the tests:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q
docker build -t lumina-wearables .
```

Keep changes focused, document changed public behaviour, and add tests for
normal and failure paths. Never add credentials, production configuration,
identifiers, payloads, or any patient data to the repository, issues, pull
requests, fixtures, logs, or screenshots.

## Wearable data changes

Each mapping must preserve the provider's original metric meaning, units,
aggregation period, device/provider provenance, and mapping-version context.
Do not equate similarly named measures (for example, RMSSD and SDNN) without an
explicit, clinically reviewed conversion and validation. Update
`docs/metric-cheat-sheet.md` for human-facing mapping changes; application code
must continue to own runtime behavior.

## Pull requests

Explain the change, its data-semantics and privacy impact, and how it was
tested. Changes that can affect clinical interpretation, identity linkage,
security controls, or downstream OMOP mapping require maintainer review before
merge.

By submitting a contribution, you agree to license it under the
[Apache License 2.0](LICENSE).
