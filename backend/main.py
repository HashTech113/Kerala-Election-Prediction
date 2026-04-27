"""FastAPI entry point for the Kerala Election 2026 backend.

Run locally (from the ``backend`` directory):
    uvicorn main:app --host 0.0.0.0 --port 8001 --reload

Run from the project root:
    uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8001

Production (Railway) uses the same command with ``$PORT`` bound by the
platform — see ``Procfile`` / ``railway.json``.

Routes preserved from the legacy ``server.py``:
    GET /api/health
    GET /api/predictions
    GET /api/predictions/meta

Automatic OpenAPI docs are served at ``/docs`` (Swagger UI) and ``/redoc``.
"""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routers import health, predictions
from services import API_VERSION


def _parse_cors_origins(raw: str) -> list[str]:
    raw = (raw or "").strip()
    if not raw or raw == "*":
        return ["*"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


CORS_ORIGINS = _parse_cors_origins(os.getenv("CORS_ORIGINS", "*"))


app = FastAPI(
    title="Kerala Election 2026 API",
    description=(
        "Prediction and metadata endpoints backing the Kerala Assembly 2026 "
        "dashboard. Serves the model output in `predictions_2026.csv` with "
        "optional fallback to the seed assembly dataset."
    ),
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS — mirrors the legacy handler (Access-Control-Allow-Origin: *). Custom
# X-* headers set by the predictions endpoint must be listed in
# ``expose_headers`` so the browser exposes them to the React frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["Content-Type", "Cache-Control", "Pragma"],
    expose_headers=[
        "X-API-Version",
        "X-Predictions-Source",
        "X-Predictions-Last-Modified-Utc",
        "X-Predictions-SHA256",
        "X-Predictions-Fallback",
        "X-Predictions-Scenario",
        "X-Predictions-Level",
        "X-Predictions-Active-Scenario",
    ],
)


app.include_router(health.router, prefix="/api")
app.include_router(predictions.router, prefix="/api")


@app.get("/", include_in_schema=False)
def root() -> JSONResponse:
    return JSONResponse(
        {
            "service": "Kerala Election 2026 API",
            "api_version": API_VERSION,
            "routes": [
                "/api/health",
                "/api/predictions",
                "/api/predictions/meta",
                "/api/predictions/kerala",
                "/api/predictions/kerala/summary",
                "/api/predictions/kerala/scenarios",
                "/docs",
                "/redoc",
            ],
        }
    )


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run("main:app", host=host, port=port, reload=False)
