"""Client for PRomop's existing concept lookup and OMOP write APIs."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.models import CanonicalWearableSample


class PromopExportError(RuntimeError):
    """Raised when PRomop cannot resolve or persist an approved wearable row."""


@dataclass(frozen=True)
class PromopSettings:
    base_url: str
    service_token: str
    timeout_seconds: float = 30.0


@dataclass(frozen=True)
class PromopMetricMapping:
    metric_key: str
    vocabulary_id: str
    concept_code: str
    table: str
    unit: str


# This is an allow-list of PRomop's existing wearable concept registry. LUMINA
# never accepts arbitrary codes or numeric concept IDs from an API caller.
PROMOP_METRIC_MAPPINGS = {
    "resting_hr": PromopMetricMapping("resting_hr", "LOINC", "40443-4", "measurements", "/min"),
    "hrv_sdnn": PromopMetricMapping("hrv_sdnn", "LOINC", "80404-7", "measurements", "ms"),
}

WEARABLE_TYPE_CONCEPT_ID = 32865
PROVENANCE_SOURCE = "lumina-wearables/open-wearables"


def mapping_for(sample: CanonicalWearableSample) -> PromopMetricMapping:
    mapping = PROMOP_METRIC_MAPPINGS.get(sample.metric_key)
    if mapping is None or mapping.unit != sample.unit:
        raise PromopExportError(f"No approved PRomop mapping exists for {sample.metric_key!r}")
    return mapping


class PromopClient:
    def __init__(self, settings: PromopSettings, transport: httpx.BaseTransport | None = None):
        if not settings.base_url or not settings.service_token:
            raise PromopExportError("PRomop base URL and service token must be configured")
        self._client = httpx.Client(
            base_url=settings.base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {settings.service_token}"},
            timeout=settings.timeout_seconds,
            transport=transport,
        )

    def __enter__(self) -> "PromopClient":
        return self

    def __exit__(self, *_: object) -> None:
        self._client.close()

    def resolve_concepts(self, mappings: list[PromopMetricMapping]) -> tuple[dict[tuple[str, str], int], dict[str, str | None]]:
        requested = {(item.vocabulary_id, item.concept_code) for item in mappings}
        params: list[tuple[str, str]] = [("lookup", f"{vocabulary}:{code}") for vocabulary, code in sorted(requested)]
        params.append(("include_versions", "1"))
        try:
            response = self._client.get("/api/v1/concepts/lookup/", params=params)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise PromopExportError("PRomop concept lookup could not be completed") from error

        resolved: dict[tuple[str, str], int] = {}
        for mapping in mappings:
            concept_id = payload.get(mapping.vocabulary_id, {}).get(mapping.concept_code)
            if not isinstance(concept_id, int) or concept_id < 1:
                raise PromopExportError(
                    f"PRomop has no configured concept for {mapping.vocabulary_id}:{mapping.concept_code}"
                )
            resolved[(mapping.vocabulary_id, mapping.concept_code)] = concept_id
        versions = payload.get("_vocabulary_versions", {})
        if not isinstance(versions, dict):
            versions = {}
        return resolved, {item.vocabulary_id: versions.get(item.vocabulary_id) for item in mappings}

    def export_daily_samples(self, *, person_id: int, samples: list[CanonicalWearableSample]) -> dict[str, object]:
        if person_id < 1:
            raise PromopExportError("PRomop person ID must be positive")
        mappings = [mapping_for(sample) for sample in samples]
        concepts, vocabulary_versions = self.resolve_concepts(mappings)
        rows: dict[str, list[dict[str, object]]] = {"measurements": [], "observations": []}
        for sample, mapping in zip(samples, mappings):
            concept_id = concepts[(mapping.vocabulary_id, mapping.concept_code)]
            if mapping.table == "measurements":
                rows["measurements"].append(
                    {
                        "person": person_id,
                        "measurement_concept": concept_id,
                        "measurement_date": sample.observed_on.isoformat(),
                        "measurement_type_concept": WEARABLE_TYPE_CONCEPT_ID,
                        "value_as_number": sample.value,
                        "measurement_source_value": mapping.concept_code,
                        "unit_source_value": sample.unit,
                    }
                )
            elif mapping.table == "observations":
                rows["observations"].append(
                    {
                        "person": person_id,
                        "observation_concept": concept_id,
                        "observation_date": sample.observed_on.isoformat(),
                        "observation_type_concept": WEARABLE_TYPE_CONCEPT_ID,
                        "value_as_number": sample.value,
                        "observation_source_value": mapping.concept_code,
                        "unit_source_value": sample.unit,
                    }
                )
            else:  # pragma: no cover - mappings are static and covered by tests
                raise PromopExportError(f"Unsupported PRomop target table {mapping.table!r}")

        results: dict[str, object] = {"vocabulary_versions": vocabulary_versions, "tables": {}}
        headers = {"X-Provenance-Source": PROVENANCE_SOURCE}
        for table, payload in rows.items():
            if not payload:
                continue
            try:
                response = self._client.post(f"/api/v1/{table}/", json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
            except (httpx.HTTPError, ValueError) as error:
                raise PromopExportError(f"PRomop {table} write could not be completed") from error
            if not isinstance(result, dict) or not isinstance(result.get("ids"), list):
                raise PromopExportError(f"PRomop {table} returned an invalid write receipt")
            results["tables"][table] = result
        return results
