from datetime import date
from uuid import UUID

import httpx
from fastapi import FastAPI, HTTPException, Query

from app.normalization import normalize_recovery_summaries
from app.open_wearables import OpenWearablesClient
from app.settings import OpenWearablesConfigurationError, OpenWearablesSettings

app = FastAPI(title="LUMINA Wearables", version="1.1.2")


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
        settings = OpenWearablesSettings.from_environment()
        with OpenWearablesClient(settings) as client:
            summaries = client.get_recovery_summaries(user_id, start_date, end_date)
    except OpenWearablesConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except httpx.HTTPError as error:
        raise HTTPException(status_code=502, detail="Open Wearables request failed") from error

    return {
        "data": [sample.model_dump(mode="json") for sample in normalize_recovery_summaries(summaries)],
        "source": "open-wearables",
        "write_status": "preview-only",
    }
