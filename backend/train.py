"""
Kerala Assembly Election 2026 - Training & Prediction Pipeline
==============================================================

Flow:  backend/data_files/*.csv  (22 source files merged by data_loader.py)
         -> feature extraction
         -> RepeatedKFold (5x3 = 15 folds)
         -> MLP ensemble with dual heads (classification + vote-share regression)
         -> ensemble_predict across all 15 models
         -> predictions_2026.csv

Usage:
    python train.py            # train model + generate predictions

The data layer is fully CSV-driven via data_loader.load_training_dataframe();
no hardcoded historical data and no synthetic projection logic remain in
the training pipeline.
"""

import os
import time
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset, WeightedRandomSampler
from sklearn.model_selection import RepeatedKFold
from sklearn.preprocessing import StandardScaler
from dataclasses import dataclass, field
from typing import List
import warnings

import pandas as pd

from data_loader import load_training_dataframe

warnings.filterwarnings("ignore")

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Configuration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass
class Config:
    """All hyperparameters in one place."""

    parties: List[str] = field(default_factory=lambda: ["LDF", "UDF", "NDA", "OTHERS"])
    num_classes: int = 4

    # Architecture (right-sized for 140 samples)
    hidden_dim: int = 128
    num_layers: int = 2
    dropout: float = 0.2

    # Training
    batch_size: int = 32
    lr: float = 8e-4
    weight_decay: float = 0.02
    epochs: int = 250
    warmup_epochs: int = 15
    patience: int = 30
    label_smoothing: float = 0.1

    # Multi-task loss weights
    cls_weight: float = 0.55
    reg_weight: float = 0.45

    # Cross-validation
    n_splits: int = 5
    n_repeats: int = 3

    # Class imbalance cap
    max_class_weight: float = 5.0

    device: str = "cuda" if torch.cuda.is_available() else "cpu"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Data Loading & Feature Engineering
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Categorical vocabularies. These are fixed by the Election Commission of
# India and never change between cycles, so listing them here is acceptable
# (we are not encoding sample data, only the legal value space). The actual
# values per row come from the CSV-driven loader.
REGIONS = ["North", "Central", "South", "Malabar", "Travancore"]
DISTRICTS = [
    "Thiruvananthapuram", "Kollam", "Pathanamthitta", "Alappuzha",
    "Kottayam", "Idukki", "Ernakulam", "Thrissur", "Palakkad",
    "Malappuram", "Kozhikode", "Wayanad", "Kannur", "Kasaragod",
]


# Numeric feature columns sourced directly from the loader. Order is fixed
# so the model and the saved scalers stay in sync across runs.
NUMERIC_FEATURES = [
    # Per-AC historical
    "vote_share_2021", "margin_pct_2021",
    "fin_crisis_impact", "wildlife_conflict_impact", "turnout_pct",
    # District demographics (kerala_demographics.csv)
    "population_density", "literacy_rate", "urban_pct",
    "hindu_pct", "muslim_pct", "christian_pct",
    "sc_st_pct", "youth_pct", "women_pct",
    # Reservation flag
    "is_reserved",
    # Incumbent / runner-up state-level momentum
    # (state-level alliance trends × per-AC 2021 winner — varies per row)
    "incumbent_ls_swing_2024_2019", "incumbent_ls_swing_2019_2014",
    "incumbent_as_swing_2021_2016",
    "runnerup_ls_swing_2024_2019", "runnerup_as_swing_2021_2016",
    # Sentiment + alliance structure (joined via 2021 winner / runner-up)
    "incumbent_sentiment", "challenger_sentiment",
    "incumbent_concentration", "challenger_concentration",
    "incumbent_breadth", "challenger_breadth",
    # State-level voter aggregates (broadcast constants — bias-absorbed
    # by the model but kept so every CSV in data_files/ is exercised)
    "state_turnout_pct", "state_first_time_voter_pct",
    "state_candidates_per_seat",
]

# Some columns are stored on a 0-100 scale in the CSV; bring them to 0-1
# before scaling so the StandardScaler sees a consistent magnitude range.
PERCENT_SCALE_COLS = {
    "literacy_rate", "urban_pct",
    "hindu_pct", "muslim_pct", "christian_pct",
    "sc_st_pct", "youth_pct", "women_pct",
}

# Population density divided by this constant for the same reason.
POP_DENSITY_DIVISOR = 1600.0


class ElectionDataset:
    """
    Builds the model-ready feature matrix from the CSV-driven DataFrame.

    The DataFrame itself is produced by data_loader.load_training_dataframe(),
    which merges all 22 CSVs in backend/data_files/. This class only handles
    one-hot encoding of categoricals + numeric scaling for non-standardized
    columns + sanity validation.
    """

    def __init__(self):
        self.config = Config()
        self.party_to_idx = {p: i for i, p in enumerate(self.config.parties)}

        print("Loading data from backend/data_files/ ...")
        self.df = load_training_dataframe()
        self.features, self.labels, self.vote_shares, self.meta = self._build()

        n = len(self.features)
        dist = {p: int((self.labels == i).sum()) for i, p in enumerate(self.config.parties)}
        print(f"  Samples: {n} | Features: {self.features.shape[1]} | Classes: {dist}")

    def _row_features(self, row: pd.Series) -> list[float]:
        f: list[float] = []

        # ── Categorical one-hots (winners + runner-up + region + district) ─
        for party in self.config.parties:
            f.append(1.0 if row["winner_2016"] == party else 0.0)
        for party in self.config.parties:
            f.append(1.0 if row["winner_2021"] == party else 0.0)
        for party in self.config.parties:
            f.append(1.0 if row["runner_up_2021"] == party else 0.0)
        for r in REGIONS:
            f.append(1.0 if row["region_5way"] == r else 0.0)
        for d in DISTRICTS:
            f.append(1.0 if row["district"] == d else 0.0)

        # ── Numeric features in fixed order ────────────────────────────────
        for col in NUMERIC_FEATURES:
            v = float(row[col])
            if col == "population_density":
                v /= POP_DENSITY_DIVISOR
            elif col in PERCENT_SCALE_COLS:
                v /= 100.0
            f.append(v)

        return f

    def _build(self):
        features, labels, vote_shares, meta = [], [], [], []

        for _, row in self.df.iterrows():
            features.append(self._row_features(row))

            # Label — fail loudly on unknown values; silent fallback to
            # OTHERS would corrupt class weights and the trained classifier.
            label_name = row["proj_2026_winner"]
            if label_name not in self.party_to_idx:
                raise ValueError(
                    f"Unknown proj_2026_winner '{label_name}' for constituency "
                    f"'{row['constituency']}'. Expected one of {list(self.party_to_idx)}."
                )
            labels.append(self.party_to_idx[label_name])

            vote_shares.append([
                row["proj_2026_ldf_pct"],
                row["proj_2026_udf_pct"],
                row["proj_2026_nda_pct"],
                row["proj_2026_others_pct"],
            ])

            meta.append({"constituency": row["constituency"], "district": row["district"]})

        features_arr = np.array(features, dtype=np.float32)
        labels_arr = np.array(labels, dtype=np.int64)
        vote_shares_arr = np.array(vote_shares, dtype=np.float32)

        if np.isnan(features_arr).any():
            raise ValueError("NaN detected in feature matrix after CSV merge.")
        if np.isnan(vote_shares_arr).any():
            raise ValueError("NaN detected in vote-share targets after CSV merge.")

        # Renormalize vote-share targets so they sum to exactly 1.0 — the
        # loader already enforces a 5%-drift bound; this is the final fix-up
        # for soft cross-entropy.
        sums = vote_shares_arr.sum(axis=1, keepdims=True)
        vote_shares_arr = vote_shares_arr / sums

        return features_arr, labels_arr, vote_shares_arr, meta


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Model Architecture
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class ResidualBlock(nn.Module):
    """Pre-norm residual MLP block."""

    def __init__(self, dim, dropout=0.1):
        super().__init__()
        self.norm = nn.LayerNorm(dim)
        self.net = nn.Sequential(
            nn.Linear(dim, dim * 3),
            nn.LayerNorm(dim * 3),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(dim * 3, dim),
        )

    def forward(self, x):
        return x + self.net(self.norm(x))


class ElectionModel(nn.Module):
    """
    Dual-head MLP:
      - Classification head: predicts winning party (4-class)
      - Regression head: predicts vote share per party (sums to 1)
    """

    def __init__(self, input_dim: int, config: Config):
        super().__init__()
        h = config.hidden_dim

        self.input_proj = nn.Sequential(
            nn.Linear(input_dim, h),
            nn.LayerNorm(h),
            nn.GELU(),
            nn.Dropout(config.dropout),
        )
        self.blocks = nn.ModuleList(
            [ResidualBlock(h, config.dropout) for _ in range(config.num_layers)]
        )
        self.norm = nn.LayerNorm(h)

        self.classifier = nn.Sequential(
            nn.Linear(h, h // 2),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(h // 2, config.num_classes),
        )
        # Outputs raw logits; softmax is applied in forward() so the same
        # tensor can serve both training (log-softmax + soft cross-entropy)
        # and inference (probability distribution that sums to 1).
        self.regressor = nn.Sequential(
            nn.Linear(h, h // 2),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(h // 2, config.num_classes),
        )

        self.apply(self._init_weights)

    def _init_weights(self, m):
        if isinstance(m, nn.Linear):
            nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity="relu")
            if m.bias is not None:
                nn.init.zeros_(m.bias)

    def forward(self, x):
        x = self.input_proj(x)
        for block in self.blocks:
            x = block(x)
        x = self.norm(x)
        logits = self.classifier(x)
        vs_logits = self.regressor(x)
        return {
            "logits": logits,
            "probs": F.softmax(logits, dim=-1),
            "vs_logits": vs_logits,
            "vote_shares": F.softmax(vs_logits, dim=-1),
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Training Loop
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def compute_class_weights(labels, max_w=5.0):
    """Inverse-frequency weights, capped at max_w."""
    counts = np.bincount(labels, minlength=4).astype(float)
    w = np.where(counts == 0, max_w, len(labels) / (4 * counts + 1e-6))
    return torch.FloatTensor(np.minimum(w, max_w))


def safe_save(state, path, retries=5):
    """Save checkpoint with retry for Windows file-locking."""
    for i in range(retries):
        try:
            torch.save(state, path)
            return
        except RuntimeError:
            if i == retries - 1:
                raise
            time.sleep(0.5)


def train_fold(fold_idx, train_idx, val_idx, data: ElectionDataset, config: Config):
    """Train one CV fold. Returns best validation accuracy."""
    dev = config.device

    # Split & scale (scaler fitted ONLY on training data)
    scaler = StandardScaler()
    X_tr = scaler.fit_transform(data.features[train_idx]).astype(np.float32)
    X_va = scaler.transform(data.features[val_idx]).astype(np.float32)
    y_tr, y_va = data.labels[train_idx], data.labels[val_idx]
    vs_tr, vs_va = data.vote_shares[train_idx], data.vote_shares[val_idx]

    # Weighted sampler for class imbalance (NDA/OTHERS are rare)
    cw_np = compute_class_weights(y_tr, config.max_class_weight).numpy()
    sampler = WeightedRandomSampler(
        torch.FloatTensor([cw_np[l] for l in y_tr]), len(y_tr), replacement=True
    )

    train_dl = DataLoader(
        TensorDataset(torch.from_numpy(X_tr), torch.from_numpy(y_tr), torch.from_numpy(vs_tr)),
        batch_size=config.batch_size, sampler=sampler, num_workers=0,
    )
    val_dl = DataLoader(
        TensorDataset(torch.from_numpy(X_va), torch.from_numpy(y_va), torch.from_numpy(vs_va)),
        batch_size=len(X_va), shuffle=False,
    )

    # Model + loss + optimizer
    model = ElectionModel(X_tr.shape[1], config).to(dev)
    cls_criterion = nn.CrossEntropyLoss(
        weight=compute_class_weights(y_tr, config.max_class_weight).to(dev)
    )

    # Soft cross-entropy between predicted log-probs and target distribution.
    # Targets sum to 1 (validated at load time), so this is the proper loss
    # for the vote-share head — MSE on softmax outputs has scale issues.
    def reg_criterion(vs_logits, vs_target):
        log_probs = F.log_softmax(vs_logits, dim=-1)
        return -(vs_target * log_probs).sum(dim=-1).mean()

    optimizer = optim.AdamW(model.parameters(), lr=config.lr, weight_decay=config.weight_decay)

    # Cosine schedule with warmup
    def lr_lambda(epoch):
        if epoch < config.warmup_epochs:
            return epoch / config.warmup_epochs
        progress = (epoch - config.warmup_epochs) / (config.epochs - config.warmup_epochs)
        return 0.5 * (1 + np.cos(np.pi * progress))

    scheduler = optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)

    # Training loop with early stopping
    best_acc, wait = 0.0, 0
    ckpt_path = os.path.join(_BACKEND_DIR, f"checkpoints/model_fold_{fold_idx}.pt")

    # Combined validation loss (lower is better) — selects on both heads.
    best_val_loss = float("inf")
    best_acc = 0.0
    wait = 0

    for epoch in range(config.epochs):
        model.train()
        for xb, yb, vsb in train_dl:
            xb, yb, vsb = xb.to(dev), yb.to(dev), vsb.to(dev)
            optimizer.zero_grad()
            out = model(xb)
            loss = (
                config.cls_weight * cls_criterion(out["logits"], yb)
                + config.reg_weight * reg_criterion(out["vs_logits"], vsb)
            )
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
        scheduler.step()

        # Validation: track classification + regression loss together
        model.eval()
        with torch.no_grad():
            for xb, yb, vsb in val_dl:
                xb, yb, vsb = xb.to(dev), yb.to(dev), vsb.to(dev)
                out = model(xb)
                v_cls = cls_criterion(out["logits"], yb).item()
                v_reg = reg_criterion(out["vs_logits"], vsb).item()
                val_loss = config.cls_weight * v_cls + config.reg_weight * v_reg
                acc = (out["logits"].argmax(-1) == yb).float().mean().item()

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_acc = acc
            wait = 0
            safe_save({"model": model.state_dict(), "scaler": scaler}, ckpt_path)
        else:
            wait += 1

        if wait >= config.patience:
            break

    best_epoch = epoch + 1 - wait
    print(f"  Fold {fold_idx + 1:2d}: val_loss={best_val_loss:.4f}  acc={best_acc:.4f}  (best @ epoch {best_epoch})")
    return best_acc


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Ensemble Prediction
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def ensemble_predict(
    data: ElectionDataset, config: Config, global_scaler: StandardScaler
) -> pd.DataFrame:
    """Average predictions across all fold models using a single global scaler."""
    print("\nGenerating ensemble predictions...")
    dev = config.device
    n_models = config.n_splits * config.n_repeats
    n_samples = len(data.labels)

    # One scaler for all models — fold scalers are training-only and would
    # otherwise feed each model a slightly different feature distribution.
    X_scaled = global_scaler.transform(data.features).astype(np.float32)
    X_tensor = torch.from_numpy(X_scaled).to(dev)

    all_probs = np.zeros((n_samples, config.num_classes))
    all_vs = np.zeros((n_samples, config.num_classes))

    for i in range(n_models):
        ckpt = torch.load(
            os.path.join(_BACKEND_DIR, f"checkpoints/model_fold_{i}.pt"),
            weights_only=False,
        )
        model = ElectionModel(X_scaled.shape[1], config).to(dev)
        model.load_state_dict(ckpt["model"])
        model.eval()
        with torch.no_grad():
            out = model(X_tensor)
            all_probs += out["probs"].cpu().numpy()
            all_vs += out["vote_shares"].cpu().numpy()

    all_probs /= n_models
    all_vs /= n_models

    # Sanity checks on the averaged outputs
    assert not np.isnan(all_probs).any(), "NaN in ensemble class probabilities"
    assert not np.isnan(all_vs).any(), "NaN in ensemble vote shares"
    assert np.allclose(all_probs.sum(axis=1), 1.0, atol=1e-4), \
        "Class probabilities do not sum to 1"
    assert np.allclose(all_vs.sum(axis=1), 1.0, atol=1e-4), \
        "Vote shares do not sum to 1"

    results = []
    for i in range(n_samples):
        probs = all_probs[i]
        vs = all_vs[i]
        pred_idx = int(np.argmax(probs))

        results.append({
            "constituency": data.meta[i]["constituency"],
            "district": data.meta[i]["district"],
            "predicted": config.parties[pred_idx],
            # Calibrated confidence = probability assigned to the predicted party.
            # Range [0.25, 1.0] for 4 classes; values >= 0.60 are "confident".
            "confidence": float(probs[pred_idx]),
            "LDF": float(probs[0]),
            "UDF": float(probs[1]),
            "NDA": float(probs[2]),
            "OTHERS": float(probs[3]),
            "vs_LDF": float(vs[0]),
            "vs_UDF": float(vs[1]),
            "vs_NDA": float(vs[2]),
            "vs_OTHERS": float(vs[3]),
        })

    return pd.DataFrame(results)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Summary & Output
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def print_summary(results: pd.DataFrame, config: Config):
    """Print election projection summary."""
    total = len(results)
    counts = results["predicted"].value_counts()
    majority = 71

    print("\n" + "=" * 60)
    print("  FINAL SEAT PROJECTION (140 constituencies)")
    print("=" * 60)

    for party in config.parties:
        n = counts.get(party, 0)
        pct = n / total * 100
        bar = "#" * int(pct / 2)
        print(f"  {party:7s}: {n:3d} seats ({pct:5.1f}%) {bar}")

    winner = counts.idxmax()
    winner_n = counts.max()
    status = "MAJORITY" if winner_n >= majority else "HUNG ASSEMBLY"
    print(f"\n  Projected winner: {winner} ({winner_n} seats) - {status}")

    # Confidence stats (top-1 predicted-class probability)
    avg_conf = results["confidence"].mean()
    high_conf = (results["confidence"] >= 0.60).sum()
    print(f"\n  Avg winning-party probability: {avg_conf:.1%}")
    print(f"  High-confidence seats (>=60% probability): {high_conf}/{total}")

    # District breakdown
    print("\n  DISTRICT-WISE:")
    print("  " + "-" * 56)
    pivot = results.groupby(["district", "predicted"]).size().unstack(fill_value=0)
    for p in config.parties:
        if p not in pivot.columns:
            pivot[p] = 0
    pivot = pivot[config.parties]
    pivot["Total"] = pivot.sum(axis=1)
    pivot["Winner"] = pivot[config.parties].idxmax(axis=1)
    print(pivot.to_string(header=True))

    # NDA wins detail
    nda = results[results["predicted"] == "NDA"]
    if len(nda) > 0:
        print(f"\n  NDA WINS ({len(nda)}):")
        for _, row in nda.iterrows():
            print(f"    {row['constituency']:20s} ({row['district']}) vs_NDA={row['vs_NDA']:.1%}")

    print("\n" + "=" * 60)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def main():
    config = Config()
    os.makedirs(os.path.join(_BACKEND_DIR, "checkpoints"), exist_ok=True)

    print("=" * 60)
    print("  KERALA ELECTION 2026 - MODEL TRAINING")
    print(f"  Device: {config.device}")
    print("=" * 60)

    # ── Step 1: Load data (CSV-driven via data_loader) ─────────
    data = ElectionDataset()

    # ── Step 2: Cross-validation training ──────────────────────
    print(f"\nTraining {config.n_splits}x{config.n_repeats} = "
          f"{config.n_splits * config.n_repeats} fold ensemble...\n")

    cv = RepeatedKFold(n_splits=config.n_splits, n_repeats=config.n_repeats, random_state=42)
    fold_accs = []

    for fold_idx, (train_idx, val_idx) in enumerate(cv.split(data.features)):
        acc = train_fold(fold_idx, train_idx, val_idx, data, config)
        fold_accs.append(acc)

    mean_acc = np.mean(fold_accs)
    std_acc = np.std(fold_accs)
    print(f"\n  CV Accuracy: {mean_acc:.4f} +/- {std_acc:.4f}")

    # ── Step 3: Ensemble prediction ────────────────────────────
    # Fit one scaler on the full dataset for inference. Per-fold scalers
    # remain inside their checkpoints but are no longer used at predict
    # time — every model now sees consistent feature scaling.
    global_scaler = StandardScaler().fit(data.features)
    results = ensemble_predict(data, config, global_scaler)

    # ── Step 4: Save output ────────────────────────────────────
    out_path = os.path.join(_BACKEND_DIR, "predictions_2026.csv")
    results.to_csv(out_path, index=False)
    print(f"\n  Saved: {out_path}")

    # ── Step 5: Summary ────────────────────────────────────────
    print_summary(results, config)


if __name__ == "__main__":
    main()
