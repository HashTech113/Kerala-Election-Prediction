"""Phase 1 scoring pipeline for the Kerala 2026 dashboard.

Reads ``backend/data_files/kerala_assembly_2026.csv`` and writes six derived
files into the same directory:

    kerala_2026_long_term_trend_sheet.csv
    kerala_2026_recent_swing_sheet.csv
    kerala_2026_live_intelligence_score_sheet.csv
    kerala_2026_final_prediction_score.csv
    kerala_2026_projected_party_summary.csv
    kerala_past_election_projection_summary.csv

This script is purely deterministic: no AI, no network, no scheduler. Run it
manually after any change to the source CSVs:

    python backend/generate_scores.py

Adapted formulas (Option A) -- see ``CAVEATS`` below for the full caveat list.

* Long-term trend: 0.5 * winner_indicator_2021 + 0.3 * LS2024 + 0.2 * winner_indicator_2016
* Recent swing:    0.7 * LS2024              + 0.3 * LB2025
* Live intel:      proj_2026 vote shares (AI updates land in Phase 4)
* Final blend:     0.40 * long_term + 0.35 * recent_swing + 0.25 * live_intel

All party scores are normalised so LDF + UDF + NDA + OTHERS == 1.0 per
constituency. Pre-result intelligence -- not an official result.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data_files"
ASSEMBLY_FILE = DATA_DIR / "kerala_assembly_2026.csv"

PARTIES: tuple[str, ...] = ("LDF", "UDF", "NDA", "OTHERS")

LT_WEIGHTS = {"win_2021": 0.5, "ls2024": 0.3, "win_2016": 0.2}
RS_WEIGHTS = {"ls2024": 0.7, "lb2025": 0.3}
FINAL_WEIGHTS = {"long_term": 0.40, "recent_swing": 0.35, "live_intel": 0.25}

CAVEATS = (
    "Per-AC Assembly 2016/2021 vote shares are not available in the repo, so "
    "winner_2016 / winner_2021 are used as 0/1 indicators (Option A). "
    "LS 2019 per-AC data is not available, so the recent-swing lens uses LS 2024 + LB 2025. "
    "OTHERS in LS2024/LB2025 is derived as 1 - (UDF + LDF + NDA) and clamped to [0, 1]. "
    "All party scores are normalised to sum to 1.0 per constituency. "
    "Pre-result intelligence -- not an official result."
)

OUTPUT_FILES = {
    "long_term": DATA_DIR / "kerala_2026_long_term_trend_sheet.csv",
    "recent_swing": DATA_DIR / "kerala_2026_recent_swing_sheet.csv",
    "live_intel": DATA_DIR / "kerala_2026_live_intelligence_score_sheet.csv",
    "final": DATA_DIR / "kerala_2026_final_prediction_score.csv",
    "party_summary": DATA_DIR / "kerala_2026_projected_party_summary.csv",
    "projection_summary": DATA_DIR / "kerala_past_election_projection_summary.csv",
}


# ----------------------------------------------------------------- helpers

def _f(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def _normalize(scores: dict[str, float]) -> dict[str, float]:
    total = sum(scores.values())
    if total <= 0:
        # Degenerate row (no signal at all). Fall back to uniform.
        return {p: 0.25 for p in PARTIES}
    return {p: scores[p] / total for p in PARTIES}


def _winner_indicator(label: str, party: str) -> float:
    return 1.0 if (label or "").strip().upper() == party else 0.0


def _argmax(scores: dict[str, float]) -> str:
    return max(scores, key=lambda p: scores[p])


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --------------------------------------------------- per-row party shares

def _ls2024_share(row: dict, party: str) -> float:
    if party == "LDF":
        return _clamp01(_f(row.get("ls2024_ldf_pct")))
    if party == "UDF":
        return _clamp01(_f(row.get("ls2024_udf_pct")))
    if party == "NDA":
        return _clamp01(_f(row.get("ls2024_nda_pct")))
    udf = _f(row.get("ls2024_udf_pct"))
    ldf = _f(row.get("ls2024_ldf_pct"))
    nda = _f(row.get("ls2024_nda_pct"))
    return _clamp01(1.0 - (udf + ldf + nda))


def _lb2025_share(row: dict, party: str) -> float:
    if party == "LDF":
        return _clamp01(_f(row.get("lb2025_ldf")))
    if party == "UDF":
        return _clamp01(_f(row.get("lb2025_udf")))
    if party == "NDA":
        return _clamp01(_f(row.get("lb2025_nda")))
    udf = _f(row.get("lb2025_udf"))
    ldf = _f(row.get("lb2025_ldf"))
    nda = _f(row.get("lb2025_nda"))
    return _clamp01(1.0 - (udf + ldf + nda))


def _proj_2026_share(row: dict, party: str) -> float:
    return _clamp01(_f(row.get(f"proj_2026_{party.lower()}_pct")))


# ------------------------------------------------------- scoring lenses

def long_term_scores(row: dict) -> dict[str, float]:
    raw = {
        p: (
            LT_WEIGHTS["win_2021"] * _winner_indicator(row.get("winner_2021", ""), p)
            + LT_WEIGHTS["ls2024"] * _ls2024_share(row, p)
            + LT_WEIGHTS["win_2016"] * _winner_indicator(row.get("winner_2016", ""), p)
        )
        for p in PARTIES
    }
    return _normalize(raw)


def recent_swing_scores(row: dict) -> dict[str, float]:
    raw = {
        p: (
            RS_WEIGHTS["ls2024"] * _ls2024_share(row, p)
            + RS_WEIGHTS["lb2025"] * _lb2025_share(row, p)
        )
        for p in PARTIES
    }
    return _normalize(raw)


def live_intelligence_scores(row: dict) -> dict[str, float]:
    raw = {p: _proj_2026_share(row, p) for p in PARTIES}
    return _normalize(raw)


def final_blend(
    lt: dict[str, float],
    rs: dict[str, float],
    li: dict[str, float],
) -> dict[str, float]:
    blended = {
        p: (
            FINAL_WEIGHTS["long_term"] * lt[p]
            + FINAL_WEIGHTS["recent_swing"] * rs[p]
            + FINAL_WEIGHTS["live_intel"] * li[p]
        )
        for p in PARTIES
    }
    # Each input lens is normalised to 1, weights sum to 1, so the blend is
    # already normalised. _normalize is defensive (and rounds out FP drift).
    return _normalize(blended)


# ---------------------------------------------------------------- I/O

def load_assembly_rows() -> list[dict]:
    with ASSEMBLY_FILE.open("r", encoding="utf-8-sig", newline="") as fp:
        return list(csv.DictReader(fp))


def write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(header)
        w.writerows(rows)


# ------------------------------------------------------- summary builders

def _avg_winning_score(rows_data: list[tuple[str, float]]) -> tuple[float, dict[str, int]]:
    """rows_data is [(top_party, top_score), ...]. Returns mean score and seat counts."""
    counts = {p: 0 for p in PARTIES}
    total = 0.0
    for top_party, top_score in rows_data:
        if top_party in counts:
            counts[top_party] += 1
        total += top_score
    n = max(len(rows_data), 1)
    return total / n, counts


# ---- Historical aggregate loaders (real ECI-style totals, not derived) ----

def _load_aggregate(path: Path) -> dict[str, dict[str, float]]:
    """Load a kerala_*_election_*.csv (party, seats_won, votes, vote_share).

    Returns ``{PARTY_UPPER: {"seats": int, "vote_share": float}}``.
    Returns an empty dict if the file is missing -- callers must handle that.
    """
    if not path.exists():
        return {}
    out: dict[str, dict[str, float]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as fp:
        for row in csv.DictReader(fp):
            party = (row.get("party") or "").strip().upper()
            if not party:
                continue
            try:
                seats = int(row.get("seats_won") or 0)
            except ValueError:
                seats = 0
            try:
                share = float(row.get("vote_share") or 0)
            except ValueError:
                share = 0.0
            out[party] = {"seats": seats, "vote_share": share}
    return out


def _winner_from_aggregate(aggr: dict[str, dict[str, float]]) -> tuple[str, float]:
    """Return ``(party_with_most_seats, that_party_vote_share_percent)``."""
    if not aggr:
        return ("", 0.0)
    winner = max(aggr, key=lambda p: aggr[p].get("seats", 0))
    return (winner, float(aggr[winner].get("vote_share", 0.0)))


# ---- Projection summary (4 rows for the dashboard cards) -----------------

UNAVAILABLE_TEXT = "Not available in uploaded dataset"
UNAVAILABLE_INTERP = (
    "Cannot calculate from available data. "
    "Pre-result intelligence, not official election result."
)


def _build_projection_summary(
    party_share_sum: dict[str, float], n_ac: int
) -> list[list]:
    """Build the four-row projection summary using REAL historical aggregates
    for the first three rows. Live Intelligence row uses proj_2026_udf_pct
    averaged across 140 ACs (state-level UDF lead).
    """
    aggr_2016 = _load_aggregate(DATA_DIR / "kerala_assembly_election_2016.csv")
    aggr_2021 = _load_aggregate(DATA_DIR / "kerala_assembly_election_2021.csv")
    aggr_ls24 = _load_aggregate(DATA_DIR / "kerala_lok_sabha_election_2024.csv")

    # Row 1 -- Historical Projection [2011-2014]: strict N/A (no per-AC source).
    hist_row = [
        "Historical Projection [2011-2014]",
        n_ac,
        UNAVAILABLE_TEXT,
        "N/A",
        "",  # empty cell -- frontend renders this as an em-dash
        UNAVAILABLE_INTERP,
        "None",
    ]

    # Row 2 -- Long-Term Trend [2016-2021]: latest of the long-term window.
    lt_winner, lt_share = _winner_from_aggregate(aggr_2021)
    lt_present_2016 = bool(aggr_2016)
    lt_row = [
        "Long-Term Trend [2016-2021]",
        n_ac,
        "kerala_assembly_election_2016.csv + kerala_assembly_election_2021.csv",
        lt_winner or "N/A",
        round(lt_share, 2) if lt_winner else "",
        (
            "Strong LDF dominance across two consecutive assembly elections. "
            "Pre-result intelligence, not official election result."
            if lt_present_2016 and lt_winner
            else UNAVAILABLE_INTERP
        ),
        "kerala_assembly_election_2016.csv, kerala_assembly_election_2021.csv",
    ]

    # Row 3 -- Recent Swing [2021-2024]: 2024 LS aggregate is the freshest signal.
    rs_winner, rs_share = _winner_from_aggregate(aggr_ls24)
    rs_row = [
        "Recent Swing [2021-2024]",
        n_ac,
        "kerala_assembly_election_2021.csv + kerala_lok_sabha_election_2024.csv",
        rs_winner or "N/A",
        round(rs_share, 2) if rs_winner else "",
        (
            "Significant swing from LDF to UDF in Lok Sabha 2024. "
            "Pre-result intelligence, not official election result."
            if rs_winner
            else UNAVAILABLE_INTERP
        ),
        "kerala_assembly_election_2021.csv, kerala_lok_sabha_election_2024.csv",
    ]

    # Row 4 -- Live Intelligence Score: per-AC UDF mean from kerala_assembly_2026.csv.
    udf_avg = round(party_share_sum.get("UDF", 0.0) / max(n_ac, 1) * 100.0, 2)
    live_row = [
        "Live Intelligence Score [LIVE DATA]",
        n_ac,
        "kerala_assembly_2026.csv",
        "UDF (slight edge / near tie)",
        udf_avg,
        (
            "Based on projected 2026 vote share data. "
            "Pre-result intelligence, not official election result."
        ),
        "kerala_assembly_2026.csv",
    ]

    return [hist_row, lt_row, rs_row, live_row]


def main() -> None:
    print(f"[generate_scores] Loading {ASSEMBLY_FILE.name} ...")
    assembly = load_assembly_rows()
    n_ac = len(assembly)
    print(f"[generate_scores] {n_ac} constituencies loaded")

    now = _utc_now_iso()
    party_score_cols = [f"{p.lower()}_score" for p in PARTIES]

    lt_rows: list[list] = []
    rs_rows: list[list] = []
    li_rows: list[list] = []
    fn_rows: list[list] = []

    for row in assembly:
        ac = row.get("constituency", "")
        lt = long_term_scores(row)
        rs = recent_swing_scores(row)
        li = live_intelligence_scores(row)
        fb = final_blend(lt, rs, li)

        lt_top, rs_top, li_top, fb_top = (
            _argmax(lt), _argmax(rs), _argmax(li), _argmax(fb)
        )

        lt_rows.append(
            [ac, *(round(lt[p], 6) for p in PARTIES),
             round(lt[lt_top], 6), lt_top]
        )
        rs_rows.append(
            [ac, *(round(rs[p], 6) for p in PARTIES),
             round(rs[rs_top], 6), rs_top]
        )
        li_rows.append(
            [ac, *(round(li[p], 6) for p in PARTIES),
             round(li[li_top], 6), li_top, now]
        )
        fn_rows.append(
            [
                ac,
                round(lt[fb_top], 6),
                round(rs[fb_top], 6),
                round(li[fb_top], 6),
                round(fb[fb_top], 6),
                fb_top,
                now,
            ]
        )

    # 1) long-term trend sheet
    write_csv(
        OUTPUT_FILES["long_term"],
        ["constituency", *party_score_cols,
         "long_term_trend_score", "analysis_predicted"],
        lt_rows,
    )

    # 2) recent swing sheet
    write_csv(
        OUTPUT_FILES["recent_swing"],
        ["constituency", *party_score_cols,
         "recent_swing_score", "analysis_predicted"],
        rs_rows,
    )

    # 3) live intelligence sheet (Phase 1 stub: copies proj_2026 shares)
    write_csv(
        OUTPUT_FILES["live_intel"],
        ["constituency", *party_score_cols,
         "live_intelligence_score", "analysis_predicted", "last_updated"],
        li_rows,
    )

    # 4) final prediction sheet
    write_csv(
        OUTPUT_FILES["final"],
        [
            "constituency",
            "long_term_trend_score",
            "recent_swing_score",
            "live_intelligence_score",
            "final_prediction_score",
            "final_predicted",
            "last_updated",
        ],
        fn_rows,
    )

    # 5) party summary (from kerala_assembly_2026.csv only)
    party_seats = {p: 0 for p in PARTIES}
    party_share_sum = {p: 0.0 for p in PARTIES}
    for row in assembly:
        winner = (row.get("proj_2026_winner") or "").strip()
        if winner in party_seats:
            party_seats[winner] += 1
        for p in PARTIES:
            party_share_sum[p] += _f(row.get(f"proj_2026_{p.lower()}_pct"))
    party_summary_rows = [
        [
            p,
            party_seats[p],
            round(party_share_sum[p] / max(n_ac, 1) * 100.0, 2),
            "Projected seat count from kerala_assembly_2026.csv (proj_2026_winner)",
        ]
        for p in PARTIES
    ]
    write_csv(
        OUTPUT_FILES["party_summary"],
        ["party", "projected_seats", "average_projected_vote_share_pct", "note"],
        party_summary_rows,
    )

    # 6) projection summary (4 rows, one per lens).
    #
    # IMPORTANT: the first three rows are sourced from REAL historical aggregate
    # files only -- never from the 2026 projection blend. Live Intelligence is
    # the only row that reads from kerala_assembly_2026.csv.
    #
    # Historical Projection [2011-2014] is intentionally marked unavailable
    # because per-AC 2011 Assembly + 2014 LS results are not in the dataset.
    proj_summary = _build_projection_summary(party_share_sum, n_ac)

    write_csv(
        OUTPUT_FILES["projection_summary"],
        [
            "projection_type",
            "total_constituencies",
            "data_reference",
            "projected_winner",
            "average_winning_score",
            "interpretation",
            "source_files",
        ],
        proj_summary,
    )

    print()
    print("[generate_scores] Wrote 6 derived files:")
    for key, path in OUTPUT_FILES.items():
        print(f"  {path.relative_to(ROOT.parent)} ({path.stat().st_size:,} bytes)")

    print()
    print("[generate_scores] Phase 1 caveats:")
    print(f"  {CAVEATS}")
    print()
    print("[generate_scores] Done. Next: python backend/validate_data.py")


if __name__ == "__main__":
    main()
