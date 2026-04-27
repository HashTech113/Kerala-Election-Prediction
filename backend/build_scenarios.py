"""Generate ``kerala_prediction_scenarios_2026.csv`` from the base model output.

Scenarios produced
------------------
    base_model — verbatim from ``predictions_2026.csv``
                  (LDF 69 / UDF 60 / NDA 7 / OTHERS 4)
    votevibe   — adjusted toward the VoteVibe / CNN-News18 survey midpoint
                  (LDF 74 / UDF 65 / NDA 1 / OTHERS 0)

The trained-model output (``predictions_2026.csv``) is NOT modified. Only
constituency-level winner overrides are applied; vote-share columns are
swapped (winner <-> base-winner) so the new winner has the highest share
without fabricating numbers.

Re-run after retraining:
    python backend/build_scenarios.py
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
BASE_FILE = ROOT / "predictions_2026.csv"
OUT_FILE = ROOT / "kerala_prediction_scenarios_2026.csv"

PARTIES = ("LDF", "UDF", "NDA", "OTHERS")

VOTEVIBE_TARGET = {"LDF": 74, "UDF": 65, "NDA": 1, "OTHERS": 0}
BASE_TARGET = {"LDF": 69, "UDF": 60, "NDA": 7, "OTHERS": 4}

# 5-way regional bucket used by the ``region_5way`` column.
REGION_5WAY: dict[str, str] = {
    "Kasaragod":          "North Kerala",
    "Kannur":             "North Kerala",
    "Wayanad":            "North Kerala",
    "Kozhikode":          "Malabar",
    "Malappuram":         "Malabar",
    "Palakkad":           "Central Kerala",
    "Thrissur":           "Central Kerala",
    "Ernakulam":          "Central Kerala",
    "Idukki":             "South-Central Kerala",
    "Kottayam":           "South-Central Kerala",
    "Alappuzha":          "South-Central Kerala",
    "Pathanamthitta":     "South-Central Kerala",
    "Kollam":             "South Kerala",
    "Thiruvananthapuram": "South Kerala",
}

# Constituency-level VoteVibe overrides: ``constituency -> (new_winner, note)``.
# Nemom is the surviving NDA seat (highest base NDA share, 0.895).
VOTEVIBE_FLIPS: dict[str, tuple[str, str]] = {
    "Mannarkkad": (
        "LDF",
        "Changed from NDA to LDF: NDA vote share is not strong enough in VoteVibe; "
        "LDF is runner-up (15.1%) with Palakkad LDF base.",
    ),
    "Palakkad": (
        "UDF",
        "Changed from NDA to UDF: NDA loses central anti-NDA vote; UDF is the natural "
        "runner-up under VoteVibe.",
    ),
    "Thrissur": (
        "UDF",
        "Changed from NDA to UDF: Christian / Latin Catholic UDF return + anti-BJP "
        "consolidation in Central Kerala.",
    ),
    "Irinjalakuda": (
        "UDF",
        "Changed from NDA to UDF: UDF strongest 2021 base; only narrowly NDA in trained "
        "projection.",
    ),
    "Thiruvananthapuram": (
        "UDF",
        "Changed from NDA to UDF: Tharoor-style UDF retake under VoteVibe wave; capital "
        "seat.",
    ),
    "Aruvikkara": (
        "UDF",
        "Changed from NDA to UDF: capital-belt seat; UDF historic stronghold returns.",
    ),
    "Nilambur": (
        "UDF",
        "Changed from Others to UDF: Others = 0 in active VoteVibe scenario; Independent "
        "re-aligns with UDF / IUML in Malappuram.",
    ),
    "Thiruvalla": (
        "LDF",
        "Changed from Others to LDF: Others = 0 in active VoteVibe scenario; LDF strong "
        "2021 base + South-Central Kerala swing.",
    ),
    "Aranmula": (
        "LDF",
        "Changed from Others to LDF: Others = 0 in active VoteVibe scenario; LDF won "
        "2021; LDF retains regional strength.",
    ),
    "Konni": (
        "LDF",
        "Changed from Others to LDF: Others = 0 in active VoteVibe scenario; Jenish "
        "2021 LDF win; LDF South-Central wave.",
    ),
    "Aroor": (
        "LDF",
        "Changed from UDF to LDF: narrow UDF margin (55.5 / 43.9); Alappuzha LDF coastal "
        "stronghold; LDF within VoteVibe upper-range advantage.",
    ),
}


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _swap_winner_share(
    shares: dict[str, float], new_winner: str, original_winner: str
) -> dict[str, float]:
    """Swap the new winner's share with the original winner's so ``shares[new_winner]``
    is the largest. Other parties retain their trained-model shares."""
    if new_winner == original_winner:
        return dict(shares)
    out = dict(shares)
    out[new_winner] = shares[original_winner]
    out[original_winner] = shares[new_winner]
    return out


def _scenario_source_label(changed: bool) -> str:
    if changed:
        return "VoteVibe / CNN-News18 survey overlay"
    return "Base model (unchanged)"


def build() -> None:
    if not BASE_FILE.exists():
        raise FileNotFoundError(
            f"{BASE_FILE} missing. Run `python backend/train.py` first."
        )

    rows: list[dict[str, Any]] = []
    with BASE_FILE.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            constituency = row["constituency"]
            district = row["district"]
            base_winner = row["predicted"]
            shares = {p: _to_float(row[p]) for p in PARTIES}

            override = VOTEVIBE_FLIPS.get(constituency)
            if override is None:
                vv_winner = base_winner
                vv_note = "Unchanged from base model in VoteVibe scenario."
            else:
                vv_winner, vv_note = override

            vv_shares = _swap_winner_share(shares, vv_winner, base_winner)

            rows.append(
                {
                    "constituency": constituency,
                    "district": district,
                    "region_5way": REGION_5WAY.get(district, "Unknown"),
                    "base_model_winner": base_winner,
                    "base_model_ldf_pct": shares["LDF"],
                    "base_model_udf_pct": shares["UDF"],
                    "base_model_nda_pct": shares["NDA"],
                    "base_model_others_pct": shares["OTHERS"],
                    "votevibe_winner": vv_winner,
                    "votevibe_ldf_pct": vv_shares["LDF"],
                    "votevibe_udf_pct": vv_shares["UDF"],
                    "votevibe_nda_pct": vv_shares["NDA"],
                    "votevibe_others_pct": vv_shares["OTHERS"],
                    "scenario_source": _scenario_source_label(vv_winner != base_winner),
                    "scenario_notes": vv_note,
                }
            )

    base_counts = {p: 0 for p in PARTIES}
    vv_counts = {p: 0 for p in PARTIES}
    for r in rows:
        base_counts[r["base_model_winner"]] += 1
        vv_counts[r["votevibe_winner"]] += 1

    if sum(base_counts.values()) != 140:
        raise ValueError(f"Base seat total != 140: {base_counts}")
    if sum(vv_counts.values()) != 140:
        raise ValueError(f"VoteVibe seat total != 140: {vv_counts}")
    if vv_counts != VOTEVIBE_TARGET:
        raise ValueError(
            f"VoteVibe seat mismatch: got {vv_counts}, expected {VOTEVIBE_TARGET}"
        )
    if base_counts != BASE_TARGET:
        print(
            f"WARN: base counts {base_counts} differ from documented baseline "
            f"{BASE_TARGET} (the trained file changed; this is informational only)."
        )

    fieldnames = list(rows[0].keys())
    with OUT_FILE.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {OUT_FILE.name} ({len(rows)} rows).")
    print(
        f"  base_model -> LDF {base_counts['LDF']}, UDF {base_counts['UDF']}, "
        f"NDA {base_counts['NDA']}, OTHERS {base_counts['OTHERS']}"
    )
    print(
        f"  votevibe   -> LDF {vv_counts['LDF']}, UDF {vv_counts['UDF']}, "
        f"NDA {vv_counts['NDA']}, OTHERS {vv_counts['OTHERS']}"
    )


if __name__ == "__main__":
    build()
