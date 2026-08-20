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
    "steps": PromopMetricMapping("steps", "LOINC", "55423-8", "observations", "/d"),
    "active_minutes": PromopMetricMapping("active_minutes", "LOINC", "55411-3", "observations", "min"),
    "resting_hr": PromopMetricMapping("resting_hr", "LOINC", "40443-4", "measurements", "/min"),
    "hrv_sdnn": PromopMetricMapping("hrv_sdnn", "LOINC", "80404-7", "measurements", "ms"),
    "hrv_rmssd": PromopMetricMapping("hrv_rmssd", "HK-Wearable", "HK-WEAR-HRV-RMSSD", "measurements", "ms"),
    "spo2": PromopMetricMapping("spo2", "LOINC", "59408-5", "measurements", "%"),
    "respiratory_rate": PromopMetricMapping("respiratory_rate", "LOINC", "9279-1", "measurements", "/min"),
    "sleep_duration": PromopMetricMapping("sleep_duration", "LOINC", "93832-4", "observations", "h"),
    "vo2_max": PromopMetricMapping("vo2_max", "LOINC", "94122-9", "measurements", "mL/kg/min"),
    "distance": PromopMetricMapping("distance", "LOINC", "41953-1", "measurements", "km"),
    "walking_speed": PromopMetricMapping("walking_speed", "LOINC", "41957-2", "measurements", "km/hr"),
    "walking_step_length": PromopMetricMapping("walking_step_length", "HK-Wearable", "HK-WEAR-STEP-LENGTH", "measurements", "cm"),
    "walking_double_support_pct": PromopMetricMapping("walking_double_support_pct", "HK-Wearable", "HK-WEAR-DBL-SUPPORT", "measurements", "%"),
    "walking_hr_avg": PromopMetricMapping("walking_hr_avg", "HK-Wearable", "HK-WEAR-WALK-HR", "measurements", "/min"),
    "flights_climbed": PromopMetricMapping("flights_climbed", "LOINC", "100304-5", "observations", "{flights}"),
    "active_energy": PromopMetricMapping("active_energy", "LOINC", "93819-1", "measurements", "kcal"),
    "basal_energy": PromopMetricMapping("basal_energy", "HK-Wearable", "HK-WEAR-BASAL-ENERGY", "measurements", "kcal"),
    "body_mass": PromopMetricMapping("body_mass", "LOINC", "29463-7", "measurements", "kg"),
}

WEARABLE_TYPE_CONCEPT_ID = 32865
PROVENANCE_SOURCE = "lumina-wearables/open-wearables"

# Mirrors PRomop's wearable artifact policy. Values outside these bounds fail
# closed before a generic OMOP write, rather than relying on a native-upload
# parser that this service does not use.
ARTIFACT_BOUNDS = {
    "spo2": (70.0, 100.0), "resting_hr": (20.0, 300.0), "hrv_sdnn": (1.0, 300.0),
    "hrv_rmssd": (1.0, 300.0), "respiratory_rate": (4.0, 60.0), "steps": (0.0, 100_000.0),
    "active_minutes": (0.0, 1440.0), "sleep_duration": (0.0, 24.0), "vo2_max": (10.0, 100.0),
    "distance": (0.0, 100.0), "walking_speed": (0.5, 15.0), "walking_step_length": (20.0, 200.0),
    "walking_double_support_pct": (5.0, 80.0), "walking_hr_avg": (30.0, 220.0),
    "flights_climbed": (0.0, 200.0), "active_energy": (0.0, 10_000.0),
    "basal_energy": (500.0, 5000.0), "body_mass": (20.0, 300.0),
}


def mapping_for(sample: CanonicalWearableSample) -> PromopMetricMapping:
    mapping = PROMOP_METRIC_MAPPINGS.get(sample.metric_key)
    if mapping is None or mapping.unit != sample.unit:
        raise PromopExportError(f"No approved PRomop mapping exists for {sample.metric_key!r}")
    bounds = ARTIFACT_BOUNDS.get(sample.metric_key)
    if bounds and not bounds[0] <= sample.value <= bounds[1]:
        raise PromopExportError(f"{sample.metric_key!r} is outside PRomop's approved wearable range")
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
