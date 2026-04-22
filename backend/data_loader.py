"""
CSV-driven training-data loader for Kerala Assembly Election 2026.

Reads every file in backend/data_files/ and merges them into a single
constituency-level DataFrame ready for the model. Replaces the hardcoded
dictionaries previously kept inside create_dataset.py.

Inputs (all under backend/data_files/):
  Per-constituency (140 rows):
    kerala_constituency_master_2026.csv  -- spine: ac_name, district, region, reservation
    kerala_assembly_2026.csv             -- per-AC historical (2016/2021) + 2026 targets
  Per-district (14 rows):
    kerala_demographics.csv              -- demographics joined by district
    kerala_district_list.csv             -- validation only
  State-level historical (per alliance):
    kerala_lok_sabha_election_2014.csv
    kerala_lok_sabha_election_2019.csv
    kerala_lok_sabha_election_2024.csv
    kerala_assembly_election_2016.csv
    kerala_assembly_election_2021.csv
  Per-alliance / per-party (2026):
    kerala_sentiment_analysis_2026.csv
    kerala_party_wise_seat_table_2026.csv
    kerala_LDF_alliance_seat_sharing_2026.csv
    kerala_UDF_alliance_seat_sharing_2026.csv
    kerala_NDA_seat_sharing_2026.csv
    kerala_main_parties_2026.csv
  State-level voter aggregates (2026):
    kerala_electorate_total_2026.csv
    kerala_people_yet_to_vote_2026.csv
    kerala_first_time_voters_2026.csv
    kerala_nominations_and_candidates_2026.csv
    kerala_gender_wise_voters_2026.csv   -- empty in this dataset; tolerated
  Cross-checks only (no features extracted):
    kerala_election_comparison_table.csv
    kerala_elections_results_past_10_years.csv

Outputs:
  load_training_dataframe() -> pd.DataFrame with 140 rows, including
    target columns (proj_2026_winner + proj_2026_*_pct) and all engineered
    features. Targets are read from kerala_assembly_2026.csv as persisted
    data; no synthetic projection logic lives in code.
"""

from __future__ import annotations

import os
import warnings
import numpy as np
import pandas as pd

PARTIES = ("LDF", "UDF", "NDA", "OTHERS")
_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_files")

CONFIDENCE_MAP = {
    "Low": 0.20,
    "Low-Medium": 0.40,
    "Medium": 0.60,
    "Medium-High": 0.75,
    "High": 0.90,
    "Slight edge / virtual tie": 0.55,
    "Competitive": 0.50,
    "Third front": 0.30,
    "Minor": 0.15,
}


def _read(name: str) -> pd.DataFrame:
    path = os.path.join(_DATA_DIR, name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing required CSV: {path}")
    return pd.read_csv(path)


def _try_read(name: str) -> pd.DataFrame | None:
    """Return None if the file is missing or empty (e.g. zero-byte CSV)."""
    path = os.path.join(_DATA_DIR, name)
    if not os.path.exists(path) or os.path.getsize(path) <= 3:
        return None
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return None


def _normalize_party(series: pd.Series) -> pd.Series:
    """Normalize party labels across files (Others -> OTHERS, etc.)."""
    return series.astype(str).str.strip().str.upper()


def _state_alliance_trends() -> dict[str, float]:
    """
    Build a flat dict of state-level alliance vote shares for each historical
    election, plus inter-period swings. Keys look like 'LDF_ls24', 'UDF_as_swing_2021_2016'.
    """
    files = {
        "ls14": "kerala_lok_sabha_election_2014.csv",
        "ls19": "kerala_lok_sabha_election_2019.csv",
        "ls24": "kerala_lok_sabha_election_2024.csv",
        "as16": "kerala_assembly_election_2016.csv",
        "as21": "kerala_assembly_election_2021.csv",
    }
    trends: dict[str, float] = {}
    for tag, fname in files.items():
        df = _read(fname)
        df["party"] = _normalize_party(df["party"])
        share = df.set_index("party")["vote_share"] / 100.0
        for p in PARTIES:
            trends[f"{p}_{tag}"] = float(share.get(p, 0.0))

    for p in PARTIES:
        trends[f"{p}_ls_swing_2024_2019"] = trends[f"{p}_ls24"] - trends[f"{p}_ls19"]
        trends[f"{p}_ls_swing_2019_2014"] = trends[f"{p}_ls19"] - trends[f"{p}_ls14"]
        trends[f"{p}_as_swing_2021_2016"] = trends[f"{p}_as21"] - trends[f"{p}_as16"]
    return trends


def _alliance_sentiment() -> dict[str, float]:
    df = _read("kerala_sentiment_analysis_2026.csv")
    df["party"] = _normalize_party(df["party"])
    df["score"] = df["confidence_pre_result"].map(CONFIDENCE_MAP)
    if df["score"].isna().any():
        unknown = df.loc[df["score"].isna(), "confidence_pre_result"].unique()
        raise ValueError(f"Unknown confidence_pre_result label(s): {list(unknown)}")
    return df.set_index("party")["score"].to_dict()


def _alliance_concentration() -> dict[str, float]:
    """Herfindahl index per alliance: sum of squared seat-share fractions."""
    df = _read("kerala_party_wise_seat_table_2026.csv")
    out = {}
    for alliance, group in df.groupby("front"):
        total = float(group["seats"].sum())
        if total <= 0:
            out[alliance] = 0.0
            continue
        shares = group["seats"].astype(float) / total
        out[alliance] = float((shares ** 2).sum())
    return out


def _alliance_breadth() -> dict[str, int]:
    """Number of distinct allied parties per alliance (from the 3 sharing CSVs)."""
    breadth = {}
    for alliance, fname in [
        ("LDF", "kerala_LDF_alliance_seat_sharing_2026.csv"),
        ("UDF", "kerala_UDF_alliance_seat_sharing_2026.csv"),
        ("NDA", "kerala_NDA_seat_sharing_2026.csv"),
    ]:
        df = _read(fname)
        breadth[alliance] = int(df["party"].nunique())
    breadth["OTHERS"] = 0
    return breadth


def _state_voter_features() -> dict[str, float]:
    elec = _read("kerala_electorate_total_2026.csv").set_index("metric")["value"]
    yet = _read("kerala_people_yet_to_vote_2026.csv").set_index("metric")["value"]
    ftv = _read("kerala_first_time_voters_2026.csv")["count"].iloc[0]
    nom = _read("kerala_nominations_and_candidates_2026.csv").set_index("metric")["count"]

    total_electorate = float(
        elec.get("published_detailed_roll_apr_2026")
        or elec.get("published_final_roll_feb_2026")
        or 0
    )
    if total_electorate <= 0:
        raise ValueError("kerala_electorate_total_2026.csv has no usable electorate total")

    cast = float(yet.get("provisional_votes_cast_polling_day", 0))
    final_candidates = float(nom.get("final_candidates_in_fray", 0))

    return {
        "state_turnout_pct": cast / total_electorate if cast else 0.77,
        "state_first_time_voter_pct": float(ftv) / total_electorate,
        "state_candidates_per_seat": final_candidates / 140.0 if final_candidates else 6.0,
    }


def _validate_cross_checks() -> None:
    """Compare comparison table + 10-year history against the per-year CSVs."""
    cmp_df = _read("kerala_election_comparison_table.csv")
    hist_df = _read("kerala_elections_results_past_10_years.csv")

    # comparison table should agree with the per-year files on winner
    for _, row in cmp_df.iterrows():
        year, etype = int(row["year"]), str(row["election"]).strip()
        if etype == "Lok Sabha":
            fname = f"kerala_lok_sabha_election_{year}.csv"
        elif etype == "Assembly":
            fname = f"kerala_assembly_election_{year}.csv"
        else:
            continue
        df = _try_read(fname)
        if df is None:
            continue
        df["party"] = _normalize_party(df["party"])
        winner = df.sort_values("seats_won", ascending=False).iloc[0]["party"]
        if winner != _normalize_party(pd.Series([row["winner"]])).iloc[0]:
            warnings.warn(
                f"Cross-check mismatch: comparison_table says {row['winner']} won "
                f"{etype} {year}, but {fname} says {winner}",
                stacklevel=2,
            )

    # past_10_years should also agree
    for _, row in hist_df.iterrows():
        year, etype = int(row["year"]), str(row["election_type"]).strip()
        fname = (
            f"kerala_lok_sabha_election_{year}.csv"
            if etype == "Lok Sabha"
            else f"kerala_assembly_election_{year}.csv"
        )
        df = _try_read(fname)
        if df is None:
            continue
        df["party"] = _normalize_party(df["party"])
        winner = df.sort_values("seats_won", ascending=False).iloc[0]["party"]
        expected = _normalize_party(pd.Series([row["winner"]])).iloc[0]
        if winner != expected:
            warnings.warn(
                f"Cross-check mismatch: past_10_years says {row['winner']} won "
                f"{etype} {year}, but {fname} says {winner}",
                stacklevel=2,
            )


def load_training_dataframe() -> pd.DataFrame:
    """
    Returns a 140-row DataFrame with all engineered features and target columns.
    Raises ValueError on any data-quality problem.
    """
    # ── Spine: 140 ACs from the constituency master ────────────────────────
    master = _read("kerala_constituency_master_2026.csv")
    if len(master) != 140:
        raise ValueError(f"Expected 140 constituencies in master, got {len(master)}")
    spine = master.rename(columns={"ac_name": "constituency"})[
        ["constituency", "district", "region_5way", "is_reserved"]
    ].copy()

    # ── Per-AC historical and 2026 targets ─────────────────────────────────
    ac = _read("kerala_assembly_2026.csv")
    keep_cols = [
        "constituency",
        "winner_2016", "winner_2021", "runner_up_2021",
        "vote_share_2021", "margin_pct_2021",
        "fin_crisis_impact", "wildlife_conflict_impact", "turnout_pct",
        "proj_2026_winner",
        "proj_2026_ldf_pct", "proj_2026_udf_pct",
        "proj_2026_nda_pct", "proj_2026_others_pct",
    ]
    df = spine.merge(ac[keep_cols], on="constituency", how="left")

    missing = df["winner_2021"].isna().sum()
    if missing:
        raise ValueError(
            f"{missing} constituencies in master are missing from "
            f"kerala_assembly_2026.csv. Check ac_name vs constituency spelling."
        )

    # ── District demographics (replaces the hardcoded DEMOGRAPHICS dict) ───
    demo = _read("kerala_demographics.csv").rename(
        columns={"density": "population_density", "literacy": "literacy_rate"}
    )
    df = df.merge(demo, on="district", how="left")
    if df["population"].isna().any():
        bad = df.loc[df["population"].isna(), "district"].unique().tolist()
        raise ValueError(f"District demographics missing for: {bad}")

    # ── District-list cross-check ──────────────────────────────────────────
    dlist = _read("kerala_district_list.csv")["District"].astype(str).str.strip().tolist()
    unknown_districts = set(df["district"]) - set(dlist)
    if unknown_districts:
        warnings.warn(
            f"Districts not present in kerala_district_list.csv: {unknown_districts}",
            stacklevel=2,
        )

    # ── State-level historical trends → incumbent/runner-up interactions ───
    trends = _state_alliance_trends()
    for tag in ("ls_swing_2024_2019", "ls_swing_2019_2014", "as_swing_2021_2016"):
        df[f"incumbent_{tag}"] = df["winner_2021"].map(
            lambda p, t=tag: trends.get(f"{p}_{t}", 0.0)
        )
    for tag in ("ls_swing_2024_2019", "as_swing_2021_2016"):
        df[f"runnerup_{tag}"] = df["runner_up_2021"].map(
            lambda p, t=tag: trends.get(f"{p}_{t}", 0.0)
        )

    # ── Sentiment + alliance structure (joined via incumbent / challenger) ─
    sent = _alliance_sentiment()
    conc = _alliance_concentration()
    breadth = _alliance_breadth()

    df["incumbent_sentiment"] = df["winner_2021"].map(sent).fillna(0.5)
    df["challenger_sentiment"] = df["runner_up_2021"].map(sent).fillna(0.5)
    df["incumbent_concentration"] = df["winner_2021"].map(conc).fillna(0.5)
    df["challenger_concentration"] = df["runner_up_2021"].map(conc).fillna(0.5)
    df["incumbent_breadth"] = df["winner_2021"].map(breadth).fillna(0).astype(float)
    df["challenger_breadth"] = df["runner_up_2021"].map(breadth).fillna(0).astype(float)

    # ── State-level voter aggregates (broadcast as constants) ──────────────
    voter = _state_voter_features()
    for k, v in voter.items():
        df[k] = v

    # ── Sanity / completeness ──────────────────────────────────────────────
    if df.isna().any().any():
        bad_cols = df.columns[df.isna().any()].tolist()
        raise ValueError(f"NaN values remain after merging in columns: {bad_cols}")

    target_cols = [
        "proj_2026_ldf_pct", "proj_2026_udf_pct",
        "proj_2026_nda_pct", "proj_2026_others_pct",
    ]
    sums = df[target_cols].sum(axis=1)
    if (sums - 1.0).abs().max() > 0.05:
        raise ValueError(
            f"Vote-share targets in kerala_assembly_2026.csv deviate from 1.0 "
            f"by more than 5% on at least one row (max drift {(sums - 1.0).abs().max():.4f})."
        )
    df[target_cols] = df[target_cols].div(sums, axis=0)  # renormalize

    # Optional cross-check (warns on inconsistencies, never raises)
    _validate_cross_checks()

    # Tolerate the empty gender-wise CSV but log it
    if _try_read("kerala_gender_wise_voters_2026.csv") is None:
        warnings.warn(
            "kerala_gender_wise_voters_2026.csv is empty — gender-split features skipped.",
            stacklevel=2,
        )

    return df


if __name__ == "__main__":
    out = load_training_dataframe()
    print(f"Loaded {len(out)} constituencies, {out.shape[1]} columns")
    print("Target winner counts:", out["proj_2026_winner"].value_counts().to_dict())
    print("Sample row:")
    print(out.iloc[0])
