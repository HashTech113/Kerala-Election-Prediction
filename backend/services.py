"""Data-loading and meta-building helpers shared by the FastAPI routers.

Two CSVs are read here, neither of which this module ever writes:

* ``predictions_2026.csv`` — trained model output, 140 rows, columns
  ``constituency, district, predicted, confidence, LDF, UDF, NDA, OTHERS``.
* ``kerala_prediction_scenarios_2026.csv`` — scenario overlay produced by
  ``build_scenarios.py``, 140 rows, columns ``base_model_winner``,
  ``base_model_<party>_pct``, ``votevibe_winner``, ``votevibe_<party>_pct``,
  plus ``region_5way``, ``scenario_source``, ``scenario_notes``.

The active dashboard scenario is selected via the ``ACTIVE_PREDICTION_SCENARIO``
env variable (default ``votevibe``). All ``/api/predictions*`` responses route
through ``load_active_predictions()`` so the dashboard always sees the active
scenario, while the per-scenario endpoint can still serve any scenario by name.
"""
from __future__ import annotations

import csv
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
PREDICTIONS_FILE = ROOT / "predictions_2026.csv"
SCENARIOS_FILE = ROOT / "kerala_prediction_scenarios_2026.csv"
ASSEMBLY_FALLBACK_FILE = ROOT / "data_files" / "kerala_assembly_2026.csv"
PARTIES = ("LDF", "UDF", "NDA", "OTHERS")
API_VERSION = "2026-04-12.1"

SCENARIO_KEYS = ("base_model", "votevibe")
PREDICTION_LEVELS = ("long_term_trend", "recent_swing", "live_intelligence_score")

SCENARIO_LABELS: dict[str, str] = {
    "base_model": "Base Model",
    "votevibe": "VoteVibe Scenario",
}

SCENARIO_NOTES: dict[str, str] = {
    "base_model": (
        "Trained constituency-level model output (predictions_2026.csv). "
        "No survey overlay applied."
    ),
    "votevibe": (
        "Adjusted toward the VoteVibe / CNN-News18 survey midpoint "
        "(LDF 68-74, UDF 64-70, NDA 1-3). Active dashboard scenario."
    ),
}

# Documented expected aggregate seat counts per scenario. Used by
# ``validate_scenario_seats``. Keep in sync with build_scenarios.py.
EXPECTED_SEAT_COUNTS: dict[str, dict[str, int]] = {
    "base_model": {"LDF": 69, "UDF": 60, "NDA": 7, "OTHERS": 4},
    "votevibe": {"LDF": 74, "UDF": 65, "NDA": 1, "OTHERS": 0},
}

NO_STORE_CACHE_HEADER = "no-store, no-cache, must-revalidate, max-age=0"
NO_STORE_HEADERS: dict[str, str] = {
    "Cache-Control": NO_STORE_CACHE_HEADER,
    "Pragma": "no-cache",
    "Expires": "0",
}


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_str(name: str, default: str) -> str:
    raw = os.getenv(name)
    if raw is None:
        return default
    raw = raw.strip()
    return raw or default


ALLOW_ASSEMBLY_FALLBACK = _env_flag("ALLOW_ASSEMBLY_FALLBACK", default=False)
ACTIVE_PREDICTION_SCENARIO = _env_str("ACTIVE_PREDICTION_SCENARIO", "votevibe")
if ACTIVE_PREDICTION_SCENARIO not in SCENARIO_KEYS:
    raise RuntimeError(
        f"ACTIVE_PREDICTION_SCENARIO={ACTIVE_PREDICTION_SCENARIO!r} is not a known "
        f"scenario. Expected one of {list(SCENARIO_KEYS)}."
    )


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ---- Base / fallback loaders --------------------------------------------

def _load_rows_from_predictions_file() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with PREDICTIONS_FILE.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            rows.append(
                {
                    "constituency": row.get("constituency", ""),
                    "district": row.get("district", ""),
                    "predicted": row.get("predicted", ""),
                    "confidence": _to_float(row.get("confidence", 0)),
                    "LDF": _to_float(row.get("LDF", 0)),
                    "UDF": _to_float(row.get("UDF", 0)),
                    "NDA": _to_float(row.get("NDA", 0)),
                    "OTHERS": _to_float(row.get("OTHERS", 0)),
                }
            )
    return rows


def _load_rows_from_assembly_fallback() -> list[dict[str, Any]]:
    if not ASSEMBLY_FALLBACK_FILE.exists():
        raise FileNotFoundError(
            f"Neither {PREDICTIONS_FILE.name} nor {ASSEMBLY_FALLBACK_FILE} was found. "
            "Run create_dataset.py and train.py before starting the server."
        )

    rows: list[dict[str, Any]] = []
    with ASSEMBLY_FALLBACK_FILE.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            shares = {
                "LDF": _to_float(row.get("proj_2026_ldf_pct", 0)),
                "UDF": _to_float(row.get("proj_2026_udf_pct", 0)),
                "NDA": _to_float(row.get("proj_2026_nda_pct", 0)),
                "OTHERS": _to_float(row.get("proj_2026_others_pct", 0)),
            }
            predicted = row.get("proj_2026_winner", "")
            if predicted not in shares:
                predicted = max(shares, key=shares.get)
            confidence = shares.get(predicted, 0.0)

            rows.append(
                {
                    "constituency": row.get("constituency", ""),
                    "district": row.get("district", ""),
                    "predicted": predicted,
                    "confidence": confidence,
                    "LDF": shares["LDF"],
                    "UDF": shares["UDF"],
                    "NDA": shares["NDA"],
                    "OTHERS": shares["OTHERS"],
                }
            )
    return rows


def iso_mtime_utc(path: Path) -> str | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    except FileNotFoundError:
        return None


def file_sha256(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as fp:
            for chunk in iter(lambda: fp.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except FileNotFoundError:
        return None


def load_predictions() -> tuple[list[dict[str, Any]], Path, bool]:
    """Return ``(rows, source_file, fallback_in_use)`` for the *base model* file.

    Always reads ``predictions_2026.csv`` (or the assembly fallback when
    explicitly enabled). Used by introspection endpoints that need the raw
    trained-model output. The dashboard does NOT call this directly — it
    calls ``load_active_predictions`` instead, which respects the active
    scenario flag.
    """
    if PREDICTIONS_FILE.exists():
        return _load_rows_from_predictions_file(), PREDICTIONS_FILE, False

    if ALLOW_ASSEMBLY_FALLBACK:
        return _load_rows_from_assembly_fallback(), ASSEMBLY_FALLBACK_FILE, True

    raise FileNotFoundError(
        f"{PREDICTIONS_FILE.name} not found. Generate and deploy it with "
        "`python backend/train.py`. To intentionally use heuristic fallback "
        "data, set ALLOW_ASSEMBLY_FALLBACK=1."
    )


def seat_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {party: 0 for party in PARTIES}
    for row in rows:
        predicted = row.get("predicted")
        if predicted in counts:
            counts[predicted] += 1
    return counts


def build_predictions_meta(
    rows: list[dict[str, Any]], source_file: Path, fallback_in_use: bool
) -> dict[str, Any]:
    counts = seat_counts(rows)
    projected_winner = "-"
    if rows:
        projected_winner = max(PARTIES, key=lambda party: counts[party])
    return {
        "api_version": API_VERSION,
        "source_file": source_file.name,
        "source_path": str(source_file),
        "source_last_modified_utc": iso_mtime_utc(source_file),
        "source_sha256": file_sha256(source_file),
        "fallback_in_use": fallback_in_use,
        "allow_assembly_fallback": ALLOW_ASSEMBLY_FALLBACK,
        "active_scenario": ACTIVE_PREDICTION_SCENARIO,
        "total_constituencies": len(rows),
        "seat_counts": counts,
        "projected_winner": projected_winner,
    }


# ---- Scenario loading -----------------------------------------------------

class ScenarioFileMissing(FileNotFoundError):
    """Raised when ``kerala_prediction_scenarios_2026.csv`` has not been built."""


def _load_scenario_rows() -> list[dict[str, Any]]:
    if not SCENARIOS_FILE.exists():
        raise ScenarioFileMissing(
            f"{SCENARIOS_FILE.name} not found. Run "
            "`python backend/build_scenarios.py` to generate it."
        )
    with SCENARIOS_FILE.open("r", encoding="utf-8", newline="") as fp:
        return list(csv.DictReader(fp))


def _scenario_winner_field(scenario: str) -> str:
    return {
        "base_model": "base_model_winner",
        "votevibe": "votevibe_winner",
    }[scenario]


def _scenario_share_field(scenario: str, party: str) -> str:
    party_key = party.lower()
    if scenario == "base_model":
        return f"base_model_{party_key}_pct"
    if scenario == "votevibe":
        return f"votevibe_{party_key}_pct"
    raise ValueError(f"Unknown scenario {scenario!r}")


def _scenario_to_prediction_row(
    raw: dict[str, Any], scenario: str
) -> dict[str, Any]:
    """Convert a scenarios-CSV row into the ``PredictionRow`` shape used by
    the existing ``/api/predictions`` consumers."""
    winner = raw[_scenario_winner_field(scenario)]
    shares = {p: _to_float(raw[_scenario_share_field(scenario, p)]) for p in PARTIES}
    confidence = shares.get(winner, 0.0)
    return {
        "constituency": raw.get("constituency", ""),
        "district": raw.get("district", ""),
        "predicted": winner,
        "confidence": confidence,
        "LDF": shares["LDF"],
        "UDF": shares["UDF"],
        "NDA": shares["NDA"],
        "OTHERS": shares["OTHERS"],
    }


def load_active_predictions() -> tuple[list[dict[str, Any]], Path, bool, str]:
    """Return rows for the *currently active* scenario.

    When ``ACTIVE_PREDICTION_SCENARIO`` is ``"base_model"`` this is the same
    rows ``load_predictions`` returns. For any other scenario, it reads from
    the scenarios CSV and re-projects each row to the ``PredictionRow`` shape.

    Returns ``(rows, source_file, fallback_in_use, active_scenario)``.
    """
    if ACTIVE_PREDICTION_SCENARIO == "base_model":
        rows, source_file, fb = load_predictions()
        return rows, source_file, fb, "base_model"

    raw_rows = _load_scenario_rows()
    rows = [_scenario_to_prediction_row(r, ACTIVE_PREDICTION_SCENARIO) for r in raw_rows]
    validate_scenario_seats(ACTIVE_PREDICTION_SCENARIO, rows)
    return rows, SCENARIOS_FILE, False, ACTIVE_PREDICTION_SCENARIO


# ---- Validation -----------------------------------------------------------

class ScenarioSeatValidationError(ValueError):
    """Raised when an active scenario does not match its expected aggregate."""


def validate_scenario_seats(
    scenario: str, rows: list[dict[str, Any]]
) -> dict[str, int]:
    """Assert seat counts equal documented expectations and total 140.

    Returns the seat-counts dict on success; raises on mismatch."""
    counts = seat_counts(rows)
    total = sum(counts.values())
    if total != 140:
        raise ScenarioSeatValidationError(
            f"{scenario}: total seats {total} != 140 (counts={counts})"
        )
    expected = EXPECTED_SEAT_COUNTS.get(scenario)
    if expected is not None and counts != expected:
        raise ScenarioSeatValidationError(
            f"{scenario}: seat counts {counts} != expected {expected}"
        )
    return counts


# ---- Per-scenario response payloads --------------------------------------

def _vote_share_estimate(
    rows: list[dict[str, Any]], scenario: str
) -> dict[str, float]:
    if not rows:
        return {p: 0.0 for p in PARTIES}
    totals = {p: 0.0 for p in PARTIES}
    for row in rows:
        for party in PARTIES:
            totals[party] += _to_float(row.get(_scenario_share_field(scenario, party)))
    n = float(len(rows))
    return {p: round(totals[p] / n, 4) for p in PARTIES}


def build_kerala_scenario(scenario: str, level: str) -> dict[str, Any]:
    if scenario not in SCENARIO_KEYS:
        raise ValueError(
            f"Unknown scenario {scenario!r}. Expected one of {list(SCENARIO_KEYS)}."
        )
    if level not in PREDICTION_LEVELS:
        raise ValueError(
            f"Unknown prediction level {level!r}. Expected one of "
            f"{list(PREDICTION_LEVELS)}."
        )

    rows = _load_scenario_rows()
    winner_field = _scenario_winner_field(scenario)

    constituencies: list[dict[str, Any]] = []
    seat_counts_map = {p: 0 for p in PARTIES}
    confidence_total = 0.0

    for row in rows:
        winner = row[winner_field]
        shares = {p: _to_float(row[_scenario_share_field(scenario, p)]) for p in PARTIES}
        confidence = shares.get(winner, 0.0)
        confidence_total += confidence
        if winner in seat_counts_map:
            seat_counts_map[winner] += 1

        constituencies.append(
            {
                "constituency": row["constituency"],
                "district": row["district"],
                "region_5way": row.get("region_5way", ""),
                "winner": winner,
                "confidence": round(confidence, 4),
                "LDF": shares["LDF"],
                "UDF": shares["UDF"],
                "NDA": shares["NDA"],
                "OTHERS": shares["OTHERS"],
                "base_model_winner": row["base_model_winner"],
                "changed_from_base": winner != row["base_model_winner"],
                "scenario_source": row.get("scenario_source"),
                "scenario_notes": (
                    row.get("scenario_notes")
                    if winner != row["base_model_winner"]
                    else None
                ),
            }
        )

    # Validate aggregate against documented expectations.
    expected = EXPECTED_SEAT_COUNTS.get(scenario)
    total = sum(seat_counts_map.values())
    seat_validation = {
        "expected": expected,
        "actual": seat_counts_map,
        "total": total,
        "ok": total == 140 and (expected is None or seat_counts_map == expected),
    }

    changed = [c for c in constituencies if c["changed_from_base"]]
    n = len(constituencies) or 1

    return {
        "scenario": scenario,
        "scenario_name": SCENARIO_LABELS[scenario],
        "prediction_level": level,
        "result_status": "Prediction, not final result",
        "counting_date": "2026-05-04",
        "seat_counts": seat_counts_map,
        "vote_share_estimate": _vote_share_estimate(rows, scenario),
        "confidence_level": round(confidence_total / n, 4),
        "constituencies": constituencies,
        "changed_seats": changed,
        "notes": SCENARIO_NOTES[scenario],
        "seat_validation": seat_validation,
    }


def build_kerala_summary(scenario: str) -> dict[str, Any]:
    """Compact summary payload matching the user-spec output."""
    if scenario not in SCENARIO_KEYS:
        raise ValueError(
            f"Unknown scenario {scenario!r}. Expected one of {list(SCENARIO_KEYS)}."
        )
    rows = _load_scenario_rows()
    winner_field = _scenario_winner_field(scenario)
    counts = {p: 0 for p in PARTIES}
    for row in rows:
        winner = row[winner_field]
        if winner in counts:
            counts[winner] += 1

    total = sum(counts.values())
    if total != 140:
        raise ScenarioSeatValidationError(
            f"{scenario}: total seats {total} != 140 (counts={counts})"
        )

    # Hide OTHERS when zero, per spec.
    seats_for_display = {p: v for p, v in counts.items() if v > 0}

    return {
        "scenario": SCENARIO_LABELS[scenario],
        "scenario_key": scenario,
        "result_status": "Prediction, not final result",
        "counting_date": "2026-05-04",
        "seats": seats_for_display,
        "total_seats": total,
        "all_seat_counts": counts,
        "active_scenario": ACTIVE_PREDICTION_SCENARIO,
    }


def list_scenarios() -> list[dict[str, str]]:
    return [
        {"key": key, "label": SCENARIO_LABELS[key], "notes": SCENARIO_NOTES[key]}
        for key in SCENARIO_KEYS
    ]
