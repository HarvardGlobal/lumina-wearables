from datetime import date
import json

import httpx
import pytest

from app.models import CanonicalWearableSample
from app.promop import PROVENANCE_SOURCE, PromopClient, PromopExportError, PromopSettings


def sample(metric_key: str, value: float, unit: str) -> CanonicalWearableSample:
    return CanonicalWearableSample(
        observed_on=date(2026, 8, 17),
        metric_key=metric_key,
        value=value,
        unit=unit,
        source_provider="garmin",
        source_device="Forerunner",
        source_device_type="watch",
        source_metric=f"recovery.{metric_key}",
    )


def test_exports_approved_daily_samples_using_promop_lookup_and_measurements_api():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.headers["Authorization"] == "Bearer service-token"
        if request.url.path == "/api/v1/concepts/lookup/":
            assert set(request.url.params.get_list("lookup")) == {"LOINC:40443-4", "LOINC:80404-7"}
            assert request.url.params["include_versions"] == "1"
            return httpx.Response(
                200,
                json={
                    "LOINC": {"40443-4": 3027018, "80404-7": 9000001},
                    "_vocabulary_versions": {"LOINC": "2026-08-01"},
                },
            )
        assert request.url.path == "/api/v1/measurements/"
        assert request.headers["X-Provenance-Source"] == PROVENANCE_SOURCE
        assert json.loads(request.content) == [
            {
                "person": 42,
                "measurement_concept": 3027018,
                "measurement_date": "2026-08-17",
                "measurement_type_concept": 32865,
                "value_as_number": 54.0,
                "measurement_source_value": "40443-4",
                "unit_source_value": "/min",
            },
            {
                "person": 42,
                "measurement_concept": 9000001,
                "measurement_date": "2026-08-17",
                "measurement_type_concept": 32865,
                "value_as_number": 42.5,
                "measurement_source_value": "80404-7",
                "unit_source_value": "ms",
            },
        ]
        return httpx.Response(201, json={"created": 2, "updated": 0, "ids": [11, 12]})

    with PromopClient(
        PromopSettings("https://promop.example", "service-token"), transport=httpx.MockTransport(handler)
    ) as client:
        receipt = client.export_daily_samples(
            person_id=42,
            samples=[sample("resting_hr", 54.0, "/min"), sample("hrv_sdnn", 42.5, "ms")],
        )

    assert [request.url.path for request in requests] == [
        "/api/v1/concepts/lookup/",
        "/api/v1/measurements/",
    ]
    assert receipt["vocabulary_versions"] == {"LOINC": "2026-08-01"}
    assert receipt["tables"] == {"measurements": {"created": 2, "updated": 0, "ids": [11, 12]}}


def test_refuses_export_when_promop_has_no_approved_concept():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"LOINC": {}, "_vocabulary_versions": {"LOINC": "2026-08-01"}})

    with PromopClient(
        PromopSettings("https://promop.example", "service-token"), transport=httpx.MockTransport(handler)
    ) as client, pytest.raises(PromopExportError, match="LOINC:40443-4"):
        client.export_daily_samples(person_id=42, samples=[sample("resting_hr", 54.0, "/min")])


def test_refuses_an_out_of_range_wearable_value_before_writing():
    with PromopClient(PromopSettings("https://promop.example", "service-token")) as client, pytest.raises(
        PromopExportError, match="outside PRomop's approved wearable range"
    ):
        client.export_daily_samples(person_id=42, samples=[sample("spo2", 101.0, "%")])


def test_full_promop_wearable_registry_matches_the_existing_promop_contract():
    from app.promop import PROMOP_METRIC_MAPPINGS

    assert {key: (value.vocabulary_id, value.concept_code, value.table, value.unit) for key, value in PROMOP_METRIC_MAPPINGS.items()} == {
        "steps": ("LOINC", "55423-8", "observations", "/d"), "active_minutes": ("LOINC", "55411-3", "observations", "min"),
        "resting_hr": ("LOINC", "40443-4", "measurements", "/min"), "hrv_sdnn": ("LOINC", "80404-7", "measurements", "ms"),
        "hrv_rmssd": ("HK-Wearable", "HK-WEAR-HRV-RMSSD", "measurements", "ms"), "spo2": ("LOINC", "59408-5", "measurements", "%"),
        "respiratory_rate": ("LOINC", "9279-1", "measurements", "/min"), "sleep_duration": ("LOINC", "93832-4", "observations", "h"),
        "vo2_max": ("LOINC", "94122-9", "measurements", "mL/kg/min"), "distance": ("LOINC", "41953-1", "measurements", "km"),
        "walking_speed": ("LOINC", "41957-2", "measurements", "km/hr"), "walking_step_length": ("HK-Wearable", "HK-WEAR-STEP-LENGTH", "measurements", "cm"),
        "walking_double_support_pct": ("HK-Wearable", "HK-WEAR-DBL-SUPPORT", "measurements", "%"), "walking_hr_avg": ("HK-Wearable", "HK-WEAR-WALK-HR", "measurements", "/min"),
        "flights_climbed": ("LOINC", "100304-5", "observations", "{flights}"), "active_energy": ("LOINC", "93819-1", "measurements", "kcal"),
        "basal_energy": ("HK-Wearable", "HK-WEAR-BASAL-ENERGY", "measurements", "kcal"), "body_mass": ("LOINC", "29463-7", "measurements", "kg"),
    }
