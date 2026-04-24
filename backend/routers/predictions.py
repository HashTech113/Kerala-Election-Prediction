"""``/api/predictions`` and ``/api/predictions/meta`` endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from schemas import ErrorResponse, PredictionRow, PredictionsMeta
from services import (
    API_VERSION,
    NO_STORE_HEADERS,
    build_predictions_meta,
    file_sha256,
    iso_mtime_utc,
    load_predictions,
)

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get(
    "",
    response_model=list[PredictionRow],
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Per-constituency win predictions",
)
def get_predictions() -> JSONResponse:
    try:
        rows, source_file, fallback_in_use = load_predictions()
    except FileNotFoundError as exc:
        return JSONResponse(
            status_code=404,
            content={"error": str(exc)},
            headers=NO_STORE_HEADERS,
        )
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"error": f"Unexpected server error: {exc}"},
            headers=NO_STORE_HEADERS,
        )

    headers = dict(NO_STORE_HEADERS)
    headers["X-API-Version"] = API_VERSION
    headers["X-Predictions-Source"] = source_file.name
    modified = iso_mtime_utc(source_file)
    if modified:
        headers["X-Predictions-Last-Modified-Utc"] = modified
    sha = file_sha256(source_file)
    if sha:
        headers["X-Predictions-SHA256"] = sha
    headers["X-Predictions-Fallback"] = "1" if fallback_in_use else "0"
    return JSONResponse(content=rows, headers=headers)


@router.get(
    "/meta",
    response_model=PredictionsMeta,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Predictions file metadata (hash, mtime, seat counts)",
)
def predictions_meta() -> JSONResponse:
    try:
        rows, source_file, fallback_in_use = load_predictions()
        return JSONResponse(
            content=build_predictions_meta(rows, source_file, fallback_in_use),
            headers=NO_STORE_HEADERS,
        )
    except FileNotFoundError as exc:
        return JSONResponse(
            status_code=404,
            content={"error": str(exc)},
            headers=NO_STORE_HEADERS,
        )
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"error": f"Unexpected server error: {exc}"},
            headers=NO_STORE_HEADERS,
        )
