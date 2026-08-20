from datetime import date
import secrets
from uuid import UUID

import httpx
from fastapi import FastAPI, Header, HTTPException, Path, Query

from app.normalization import normalize_recovery_summaries
from app.open_wearables import OpenWearablesClient
from app.promop import PromopClient, PromopExportError, PromopSettings
from app.settings import (
    OpenWearablesConfigurationError,
    OpenWearablesSettings,
    WearablesExportConfigurationError,
    WearablesExportSettings,
)

app = FastAPI(title="LUMINA Wearables", version="1.1.4")


def approved_daily_samples(user_id: UUID, start_date: date, end_date: date):
    settings = OpenWearablesSettings.from_environment()
    with OpenWearablesClient(settings) as client:
        return normalize_recovery_summaries(client.get_recovery_summaries(user_id, start_date, end_date))


def require_export_token(authorization: str | None = Header(default=None)) -> WearablesExportSettings:
    settings = WearablesExportSettings.from_environment()
    supplied = authorization.removeprefix("Bearer ") if authorization else ""
    if not authorization or not authorization.startswith("Bearer ") or not secrets.compare_digest(supplied, settings.export_token):
        raise HTTPException(status_code=401, detail="Invalid Wearables export credential")
    return settings


@app.get("/health")
def health():
    return {"status": "healthy", "service": "lumina-wearables"}


@app.get("/api/v1/open-wearables/users/{user_id}/daily-recovery")
def daily_recovery(
    user_id: UUID,
    start_date: date = Query(...),
    end_date: date = Query(...),
):
    """Return the first approved canonical HR/HRV pilot metrics.

    This endpoint is intentionally read-only. It does not write to PRomop or
    Archive: each destination needs its own approved, authenticated ingestion
    contract. See docs/promop-integration.md.
    """
    if end_date < start_date:
        raise HTTPException(status_code=422, detail="end_date must not precede start_date")

    try:
        samples = approved_daily_samples(user_id, start_date, end_date)
    except OpenWearablesConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except httpx.HTTPError as error:
        raise HTTPException(status_code=502, detail="Open Wearables request failed") from error

    return {
        "data": [sample.model_dump(mode="json") for sample in samples],
        "source": "open-wearables",
        "write_status": "preview-only",
    }


@app.post("/api/v1/promop/persons/{person_id}/open-wearables/users/{user_id}/daily-recovery/export")
def export_daily_recovery_to_promop(
    user_id: UUID,
    person_id: int = Path(gt=0),
    start_date: date = Query(...),
    end_date: date = Query(...),
    authorization: str | None = Header(default=None),
):
    """Export approved daily samples through PRomop's existing OMOP APIs.

    The caller supplies the explicitly authorised PRomop person ID. Open
    Wearables identities are acquisition identifiers and are never resolved to
    a PRomop person by this service.
    """
    if end_date < start_date:
        raise HTTPException(status_code=422, detail="end_date must not precede start_date")
    try:
        export_settings = require_export_token(authorization)
        samples = approved_daily_samples(user_id, start_date, end_date)
        with PromopClient(
            PromopSettings(
                export_settings.promop_base_url,
                export_settings.promop_service_token,
                export_settings.timeout_seconds,
            )
        ) as client:
            receipt = client.export_daily_samples(person_id=person_id, samples=samples)
    except (OpenWearablesConfigurationError, WearablesExportConfigurationError) as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except (httpx.HTTPError, PromopExportError) as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    return {
        "person_id": person_id,
        "exported_samples": len(samples),
        "source": "open-wearables",
        "receipt": receipt,
    }
