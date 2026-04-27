"""``/api/predictions`` and ``/api/predictions/kerala`` endpoints.

The ``GET /api/predictions`` and ``GET /api/predictions/meta`` routes serve the
*active* prediction scenario (controlled by ``ACTIVE_PREDICTION_SCENARIO``) so
the dashboard always reflects the configured scenario. Per-scenario access
remains available at ``GET /api/predictions/kerala?scenario=...``.
"""
from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from schemas import ErrorResponse, KeralaScenarioResponse, PredictionRow, PredictionsMeta
from services import (
    ACTIVE_PREDICTION_SCENARIO,
    API_VERSION,
    NO_STORE_HEADERS,
    PREDICTION_LEVELS,
    SCENARIO_KEYS,
    ScenarioFileMissing,
    ScenarioSeatValidationError,
    build_kerala_scenario,
    build_kerala_summary,
    build_predictions_meta,
    file_sha256,
    iso_mtime_utc,
    list_scenarios,
    load_active_predictions,
)

router = APIRouter(prefix="/predictions", tags=["predictions"])


def _scenario_response_headers(
    source_file_name: str,
    source_file_path,
    fallback_in_use: bool,
    active_scenario: str,
) -> dict[str, str]:
    headers = dict(NO_STORE_HEADERS)
    headers["X-API-Version"] = API_VERSION
    headers["X-Predictions-Source"] = source_file_name
    headers["X-Predictions-Active-Scenario"] = active_scenario
    modified = iso_mtime_utc(source_file_path)
    if modified:
        headers["X-Predictions-Last-Modified-Utc"] = modified
    sha = file_sha256(source_file_path)
    if sha:
        headers["X-Predictions-SHA256"] = sha
    headers["X-Predictions-Fallback"] = "1" if fallback_in_use else "0"
    return headers


@router.get(
    "",
    response_model=list[PredictionRow],
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Per-constituency win predictions for the active scenario",
    description=(
        "Returns the active Kerala 2026 prediction scenario as 140 "
        "PredictionRow objects. The active scenario is controlled by the "
        "ACTIVE_PREDICTION_SCENARIO env variable (default: votevibe)."
    ),
)
def get_predictions() -> JSONResponse:
    try:
        rows, source_file, fallback_in_use, active_scenario = load_active_predictions()
    except (FileNotFoundError, ScenarioFileMissing) as exc:
        return JSONResponse(
            status_code=404,
            content={"error": str(exc)},
            headers=NO_STORE_HEADERS,
        )
    except ScenarioSeatValidationError as exc:
        return JSONResponse(
            status_code=500,
            content={"error": f"Active scenario validation failed: {exc}"},
            headers=NO_STORE_HEADERS,
        )
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"error": f"Unexpected server error: {exc}"},
            headers=NO_STORE_HEADERS,
        )

    headers = _scenario_response_headers(
        source_file.name, source_file, fallback_in_use, active_scenario
    )
    return JSONResponse(content=rows, headers=headers)


@router.get(
    "/meta",
    response_model=PredictionsMeta,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Active-scenario predictions metadata (hash, mtime, seat counts)",
)
def predictions_meta() -> JSONResponse:
    try:
        rows, source_file, fallback_in_use, _ = load_active_predictions()
        return JSONResponse(
            content=build_predictions_meta(rows, source_file, fallback_in_use),
            headers=NO_STORE_HEADERS,
        )
    except (FileNotFoundError, ScenarioFileMissing) as exc:
        return JSONResponse(
            status_code=404,
            content={"error": str(exc)},
            headers=NO_STORE_HEADERS,
        )
    except ScenarioSeatValidationError as exc:
        return JSONResponse(
            status_code=500,
            content={"error": f"Active scenario validation failed: {exc}"},
            headers=NO_STORE_HEADERS,
        )
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"error": f"Unexpected server error: {exc}"},
            headers=NO_STORE_HEADERS,
        )


@router.get(
    "/kerala",
    response_model=KeralaScenarioResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Kerala 2026 prediction for a given scenario and prediction level",
    description=(
        "Returns the requested scenario projection (base_model or votevibe) "
        "across all 140 Kerala assembly seats. Predictions only — counting "
        "is on 2026-05-04."
    ),
)
def kerala_scenario(
    scenario: str = Query(
        ACTIVE_PREDICTION_SCENARIO,
        description="Prediction scenario",
        enum=list(SCENARIO_KEYS),
    ),
    level: str = Query(
        "live_intelligence_score",
        description="Prediction level",
        enum=list(PREDICTION_LEVELS),
    ),
) -> JSONResponse:
    try:
        payload = build_kerala_scenario(scenario, level)
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={"error": str(exc)},
            headers=NO_STORE_HEADERS,
        )
    except ScenarioFileMissing as exc:
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
    headers["X-Predictions-Scenario"] = scenario
    headers["X-Predictions-Level"] = level
    headers["X-Predictions-Active-Scenario"] = ACTIVE_PREDICTION_SCENARIO
    return JSONResponse(content=payload, headers=headers)


@router.get(
    "/kerala/summary",
    summary="Compact seat-count summary for a Kerala 2026 scenario",
    description=(
        "Returns the user-facing summary payload (scenario, scenario_key, "
        "result_status, counting_date, seats, total_seats). The OTHERS key is "
        "omitted from `seats` when its count is zero."
    ),
)
def kerala_summary(
    scenario: str = Query(
        ACTIVE_PREDICTION_SCENARIO,
        description="Prediction scenario",
        enum=list(SCENARIO_KEYS),
    ),
) -> JSONResponse:
    try:
        payload = build_kerala_summary(scenario)
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={"error": str(exc)},
            headers=NO_STORE_HEADERS,
        )
    except ScenarioFileMissing as exc:
        return JSONResponse(
            status_code=404,
            content={"error": str(exc)},
            headers=NO_STORE_HEADERS,
        )
    except ScenarioSeatValidationError as exc:
        return JSONResponse(
            status_code=500,
            content={"error": f"Scenario validation failed: {exc}"},
            headers=NO_STORE_HEADERS,
        )
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"error": f"Unexpected server error: {exc}"},
            headers=NO_STORE_HEADERS,
        )

    return JSONResponse(content=payload, headers=NO_STORE_HEADERS)


@router.get(
    "/kerala/scenarios",
    summary="List the available Kerala 2026 prediction scenarios",
)
def kerala_scenarios() -> JSONResponse:
    return JSONResponse(
        content={
            "scenarios": list_scenarios(),
            "prediction_levels": list(PREDICTION_LEVELS),
            "active_scenario": ACTIVE_PREDICTION_SCENARIO,
            "result_status": "Prediction, not final result",
            "counting_date": "2026-05-04",
        },
        headers=NO_STORE_HEADERS,
    )
