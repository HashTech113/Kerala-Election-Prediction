"""``GET /api/health`` — reports API status plus the current predictions meta."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from schemas import HealthResponse
from services import (
    API_VERSION,
    NO_STORE_HEADERS,
    build_predictions_meta,
    load_predictions,
)

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    responses={500: {"model": HealthResponse}},
    summary="Liveness + predictions contract check",
)
def health() -> JSONResponse:
    try:
        rows, source_file, fallback_in_use = load_predictions()
        payload = {
            "status": "ok",
            "api_version": API_VERSION,
            "meta": build_predictions_meta(rows, source_file, fallback_in_use),
        }
        return JSONResponse(content=payload, headers=NO_STORE_HEADERS)
    except FileNotFoundError as exc:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(exc)},
            headers=NO_STORE_HEADERS,
        )
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": f"Unexpected server error: {exc}"},
            headers=NO_STORE_HEADERS,
        )
