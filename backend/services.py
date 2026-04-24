"""Data-loading and meta-building helpers shared by the FastAPI routers.

Extracted from the legacy ``server.py`` module so the HTTP layer (FastAPI)
stays thin. Behaviour is byte-identical to the previous BaseHTTPRequestHandler
implementation — the same source files are read, the same fallback rules
apply, and the same meta payload is produced.
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
ASSEMBLY_FALLBACK_FILE = ROOT / "data_files" / "kerala_assembly_2026.csv"
PARTIES = ("LDF", "UDF", "NDA", "OTHERS")
API_VERSION = "2026-04-12.1"

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


ALLOW_ASSEMBLY_FALLBACK = _env_flag("ALLOW_ASSEMBLY_FALLBACK", default=False)


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


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
    """Return ``(rows, source_file, fallback_in_use)``.

    Prefers ``predictions_2026.csv``. Falls back to ``kerala_assembly_2026.csv``
    only when ``ALLOW_ASSEMBLY_FALLBACK=1``. Raises ``FileNotFoundError``
    otherwise so the API surfaces a clear error instead of quietly serving
    stale or synthetic data.
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
        "total_constituencies": len(rows),
        "seat_counts": counts,
        "projected_winner": projected_winner,
    }
