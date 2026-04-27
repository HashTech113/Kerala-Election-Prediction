"""Pydantic response schemas used by the FastAPI routers.

These are published in the OpenAPI / Swagger docs so frontend consumers have
a typed contract. The actual payloads are produced by ``services.py`` as
plain dicts — Pydantic validation is advisory only (FastAPI's response_model
would otherwise coerce error responses, which we want to preserve verbatim
from the original server).
"""
from __future__ import annotations

from typing import Literal, Optional

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
    active_scenario: Optional[str] = None
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


# ---- Scenario predictions ------------------------------------------------

ScenarioName = Literal["base_model", "votevibe"]
PredictionLevel = Literal["long_term_trend", "recent_swing", "live_intelligence_score"]


class ScenarioConstituency(BaseModel):
    constituency: str
    district: str
    region_5way: Optional[str] = None
    winner: str = Field(..., description="Predicted winning alliance for this scenario")
    confidence: float = Field(..., description="Winner's vote share in this scenario (0-1)")
    LDF: float
    UDF: float
    NDA: float
    OTHERS: float
    base_model_winner: str
    changed_from_base: bool = Field(
        ..., description="True when this scenario flips the base-model winner"
    )
    scenario_source: Optional[str] = None
    scenario_notes: Optional[str] = Field(
        None, description="Reason the winner differs from the base model (if any)"
    )


class ScenarioVoteShare(BaseModel):
    LDF: float
    UDF: float
    NDA: float
    OTHERS: float


class ScenarioSeatValidation(BaseModel):
    expected: Optional[SeatCounts] = None
    actual: SeatCounts
    total: int
    ok: bool


class KeralaScenarioResponse(BaseModel):
    scenario: ScenarioName
    scenario_name: str
    prediction_level: PredictionLevel
    result_status: str = "Prediction, not final result"
    counting_date: str = "2026-05-04"
    seat_counts: SeatCounts
    vote_share_estimate: ScenarioVoteShare
    confidence_level: float
    constituencies: list[ScenarioConstituency]
    changed_seats: list[ScenarioConstituency]
    notes: str
    seat_validation: ScenarioSeatValidation
