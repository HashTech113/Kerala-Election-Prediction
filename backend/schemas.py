"""Pydantic response schemas used by the FastAPI routers.

These are published in the OpenAPI / Swagger docs so frontend consumers have
a typed contract. The actual payloads are produced by ``services.py`` as
plain dicts — Pydantic validation is advisory only (FastAPI's response_model
would otherwise coerce error responses, which we want to preserve verbatim
from the original server).
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class SeatCounts(BaseModel):
    LDF: int = 0
    UDF: int = 0
    NDA: int = 0
    OTHERS: int = 0


class PredictionRow(BaseModel):
    constituency: str = Field(..., description="Assembly constituency name")
    district: str = Field(..., description="Kerala district")
    predicted: str = Field(..., description="Predicted winning alliance (LDF/UDF/NDA/OTHERS)")
    confidence: float = Field(..., description="Top-1 predicted-party probability (0.25-1.0)")
    LDF: float
    UDF: float
    NDA: float
    OTHERS: float


class PredictionsMeta(BaseModel):
    api_version: str
    source_file: str
    source_path: str
    source_last_modified_utc: Optional[str] = None
    source_sha256: Optional[str] = None
    fallback_in_use: bool
    allow_assembly_fallback: bool
    total_constituencies: int
    seat_counts: SeatCounts
    projected_winner: str


class HealthResponse(BaseModel):
    status: str = Field(..., description="'ok' on success, 'error' otherwise")
    api_version: Optional[str] = None
    meta: Optional[PredictionsMeta] = None
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    available_routes: Optional[list[str]] = None
