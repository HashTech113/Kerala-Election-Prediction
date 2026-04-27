"""Phase 1 dataset validator. Run after ``generate_scores.py``.

Checks:
    * 140 rows in every constituency-level file
    * proj_2026_*_pct sums per row are within tolerance of 1.0
    * No missing proj_2026_winner labels
    * Per-party scores in scoring sheets are inside [0, 1] and sum to ~1.0
    * analysis_predicted == argmax(party scores) in each scoring sheet
    * final_prediction_score == 0.40*LT + 0.35*RS + 0.25*LI per row
    * Historical election CSVs are still present (this script never writes them)

Exit code: 0 if all checks pass, 1 if any check fails.

Usage:

    python backend/validate_data.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data_files"
PARTIES: tuple[str, ...] = ("LDF", "UDF", "NDA", "OTHERS")

# Tolerances
SUM_TOL = 0.005    # vote-share / score sum tolerance
SCORE_TOL = 0.001  # individual-score range tolerance ([0, 1])
BLEND_TOL = 0.001  # final-blend formula tolerance

ASSEMBLY = DATA_DIR / "kerala_assembly_2026.csv"
LT = DATA_DIR / "kerala_2026_long_term_trend_sheet.csv"
RS = DATA_DIR / "kerala_2026_recent_swing_sheet.csv"
LI = DATA_DIR / "kerala_2026_live_intelligence_score_sheet.csv"
FN = DATA_DIR / "kerala_2026_final_prediction_score.csv"
PP = DATA_DIR / "kerala_2026_projected_party_summary.csv"
PS = DATA_DIR / "kerala_past_election_projection_summary.csv"

HISTORICAL_FILES = (
    "kerala_assembly_election_2016.csv",
    "kerala_assembly_election_2021.csv",
    "kerala_lok_sabha_election_2014.csv",
    "kerala_lok_sabha_election_2019.csv",
    "kerala_lok_sabha_election_2024.csv",
)


passes: list[str] = []
warnings: list[str] = []
errors: list[str] = []


def _read(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as fp:
        return list(csv.DictReader(fp))


def _f(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _record(ok: bool, label: str, detail: str = "") -> None:
    line = f"  {'PASS' if ok else 'FAIL'}  {label}"
    if detail:
        line += f" - {detail}"
    (passes if ok else errors).append(line)


def _warn(label: str, detail: str = "") -> None:
    warnings.append(f"  WARN  {label}{(' - ' + detail) if detail else ''}")


def _check_140(path: Path) -> list[dict] | None:
    if not path.exists():
        _record(False, f"{path.name} exists", "file not found")
        return None
    rows = _read(path)
    _record(len(rows) == 140, f"{path.name} row count == 140",
            "" if len(rows) == 140 else f"got {len(rows)}")
    return rows


def check_assembly() -> None:
    rows = _check_140(ASSEMBLY)
    if not rows:
        return
    bad_sum = 0
    missing_winner = 0
    for r in rows:
        s = sum(_f(r.get(f"proj_2026_{p.lower()}_pct")) for p in PARTIES)
        if abs(s - 1.0) > SUM_TOL:
            bad_sum += 1
        if not (r.get("proj_2026_winner") or "").strip():
            missing_winner += 1
    _record(bad_sum == 0,
            f"{ASSEMBLY.name} proj_2026_*_pct rows sum to ~1.0",
            "" if bad_sum == 0 else f"{bad_sum} rows out of tolerance")
    _record(missing_winner == 0,
            f"{ASSEMBLY.name} proj_2026_winner populated",
            "" if missing_winner == 0 else f"{missing_winner} missing")


def check_score_sheet(path: Path, score_col: str, has_last_updated: bool = False) -> None:
    rows = _check_140(path)
    if not rows:
        return
    bad_range = bad_sum = bad_argmax = bad_topscore = missing_ts = 0
    for r in rows:
        scores = {p: _f(r.get(f"{p.lower()}_score")) for p in PARTIES}
        if any(v < -SCORE_TOL or v > 1 + SCORE_TOL for v in scores.values()):
            bad_range += 1
        if abs(sum(scores.values()) - 1.0) > SUM_TOL:
            bad_sum += 1
        top = max(scores, key=lambda p: scores[p])
        ap = (r.get("analysis_predicted") or "").strip()
        if ap != top:
            bad_argmax += 1
        if abs(_f(r.get(score_col)) - scores[top]) > SCORE_TOL:
            bad_topscore += 1
        if has_last_updated and not (r.get("last_updated") or "").strip():
            missing_ts += 1

    _record(bad_range == 0, f"{path.name} per-party scores in [0, 1]",
            "" if bad_range == 0 else f"{bad_range} rows")
    _record(bad_sum == 0, f"{path.name} per-party scores sum to ~1.0",
            "" if bad_sum == 0 else f"{bad_sum} rows")
    _record(bad_argmax == 0, f"{path.name} analysis_predicted == argmax",
            "" if bad_argmax == 0 else f"{bad_argmax} rows")
    _record(bad_topscore == 0, f"{path.name} {score_col} == argmax score",
            "" if bad_topscore == 0 else f"{bad_topscore} rows")
    if has_last_updated:
        _record(missing_ts == 0, f"{path.name} last_updated populated",
                "" if missing_ts == 0 else f"{missing_ts} missing")


def check_final() -> dict[str, int]:
    seat_counts = {p: 0 for p in PARTIES}
    rows = _check_140(FN)
    if not rows:
        return seat_counts
    bad_range = bad_blend = 0
    for r in rows:
        lt = _f(r.get("long_term_trend_score"))
        rs = _f(r.get("recent_swing_score"))
        li = _f(r.get("live_intelligence_score"))
        fp = _f(r.get("final_prediction_score"))
        if any(v < -SCORE_TOL or v > 1 + SCORE_TOL for v in (lt, rs, li, fp)):
            bad_range += 1
        expected = 0.40 * lt + 0.35 * rs + 0.25 * li
        if abs(expected - fp) > BLEND_TOL:
            bad_blend += 1
        winner = (r.get("final_predicted") or "").strip()
        if winner in seat_counts:
            seat_counts[winner] += 1
    _record(bad_range == 0, f"{FN.name} scores in [0, 1]",
            "" if bad_range == 0 else f"{bad_range} rows")
    _record(bad_blend == 0,
            f"{FN.name} final_prediction_score == 0.40*LT + 0.35*RS + 0.25*LI",
            "" if bad_blend == 0 else f"{bad_blend} rows out of tolerance")
    return seat_counts


def check_historical_present() -> None:
    missing = [h for h in HISTORICAL_FILES if not (DATA_DIR / h).exists()]
    _record(not missing, "historical election files still present",
            "" if not missing else f"missing: {missing}")


def check_summary_files_shape() -> None:
    if PP.exists():
        rows = _read(PP)
        ok = len(rows) == len(PARTIES) and {r.get("party") for r in rows} == set(PARTIES)
        _record(ok, f"{PP.name} has one row per party",
                "" if ok else f"got {len(rows)} rows")
    else:
        _record(False, f"{PP.name} exists", "file not found")
    if PS.exists():
        rows = _read(PS)
        _record(len(rows) == 4, f"{PS.name} has 4 projection rows",
                "" if len(rows) == 4 else f"got {len(rows)}")
    else:
        _record(False, f"{PS.name} exists", "file not found")


def report_summaries(final_seats: dict[str, int]) -> None:
    print()
    print("  [final_prediction] seat counts: " +
          ", ".join(f"{p}={final_seats[p]}" for p in PARTIES) +
          f"  (total={sum(final_seats.values())})")

    if PP.exists():
        rows = _read(PP)
        print()
        print(f"  [{PP.name}]")
        for r in rows:
            print(
                f"    {r['party']:6s}  seats={int(r['projected_seats']):>3d}  "
                f"avg_share={r['average_projected_vote_share_pct']}%"
            )

    if PS.exists():
        rows = _read(PS)
        print()
        print(f"  [{PS.name}]")
        for r in rows:
            print(
                f"    {r['projection_type']:42s}  "
                f"winner={r['projected_winner']:6s}  "
                f"avg_score={r['average_winning_score']}%"
            )


def main() -> None:
    print("[validate] Phase 1 dataset validation")
    print("=" * 64)

    check_assembly()
    check_score_sheet(LT, "long_term_trend_score")
    check_score_sheet(RS, "recent_swing_score")
    check_score_sheet(LI, "live_intelligence_score", has_last_updated=True)
    final_seats = check_final()
    check_historical_present()
    check_summary_files_shape()
    report_summaries(final_seats)

    print()
    print(f"[validate] {len(passes)} passed, {len(warnings)} warnings, {len(errors)} errors")
    print()
    for line in passes:
        print(line)
    if warnings:
        print("\nWARNINGS:")
        for line in warnings:
            print(line)
    if errors:
        print("\nERRORS:")
        for line in errors:
            print(line)
        sys.exit(1)
    print("\n[validate] All checks passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
