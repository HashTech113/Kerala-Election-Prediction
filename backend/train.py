"""
Kerala Assembly Election 2026 - Training & Prediction Pipeline
==============================================================

Flow:  data_files/kerala_assembly_2026.csv  (from create_dataset.py)
         -> feature extraction (49 dims)
         -> RepeatedKFold (5x3 = 15 folds)
         -> MLP ensemble with dual heads (classification + vote-share regression)
         -> ensemble_predict across all 15 models
         -> predictions_2026.csv

Usage:
    python create_dataset.py   # Step 1: build training CSV from dataset/*.xlsx
    python train.py            # Step 2: train model + generate predictions
"""

import os
import time
import numpy as np
import pandas as pd
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

REGIONS = ["North", "Central", "South", "Malabar", "Travancore"]
DISTRICTS = [
    "Thiruvananthapuram", "Kollam", "Pathanamthitta", "Alappuzha",
    "Kottayam", "Idukki", "Ernakulam", "Thrissur", "Palakkad",
    "Malappuram", "Kozhikode", "Wayanad", "Kannur", "Kasaragod",
]


class ElectionDataset:
    """
    Loads the constituency CSV and builds a numerical feature matrix.

    Feature groups (49 total):
      [0:4]   winner_2016 one-hot (LDF/UDF/NDA/OTHERS)
      [4:8]   winner_2021 one-hot
      [8:12]  runner_up_2021 one-hot
      [12:14] vote_share_2021, margin_pct_2021
      [14:17] ls2024_ldf/udf/nda_pct
      [17:20] lb2025_ldf/udf/nda
      [20:22] fin_crisis_impact, wildlife_conflict_impact
      [22]    turnout_pct
      [23:29] demographics (density, literacy, urban, hindu, muslim, christian)
      [29]    is_reserved
      [30:35] region_5way one-hot
      [35:49] district one-hot (14)
    """

    def __init__(self, csv_path: str):
        self.config = Config()
        self.party_to_idx = {p: i for i, p in enumerate(self.config.parties)}

        print("Loading data...")
        self.df = pd.read_csv(csv_path)
        self.features, self.labels, self.vote_shares, self.meta = self._build()

        n = len(self.features)
        dist = {p: int((self.labels == i).sum()) for i, p in enumerate(self.config.parties)}
        print(f"  Samples: {n} | Features: {self.features.shape[1]} | Classes: {dist}")

    def _build(self):
        features, labels, vote_shares, meta = [], [], [], []

        for _, row in self.df.iterrows():
            f = []

            # Historical winner encoding (2016 + 2021)
            for party in self.config.parties:
                f.append(1.0 if row.get("winner_2016", "") == party else 0.0)
            for party in self.config.parties:
                f.append(1.0 if row["winner_2021"] == party else 0.0)

            # Runner-up 2021
            for party in self.config.parties:
                f.append(1.0 if row.get("runner_up_2021", "") == party else 0.0)

            # Vote share & margin
            f.extend([row["vote_share_2021"], row["margin_pct_2021"]])

            # Lok Sabha 2024
            f.extend([
                row.get("ls2024_ldf_pct", 0.35),
                row.get("ls2024_udf_pct", 0.40),
                row.get("ls2024_nda_pct", 0.15),
            ])

            # Local body 2025
            f.extend([
                row.get("lb2025_ldf", 0.40),
                row.get("lb2025_udf", 0.35),
                row.get("lb2025_nda", 0.10),
            ])

            # Regional issues
            f.extend([
                row.get("fin_crisis_impact", 0.5),
                row.get("wildlife_conflict_impact", 0.0),
            ])

            # Turnout
            f.append(float(row.get("turnout_pct", 0.77)))

            # Demographics (normalized)
            f.extend([
                row.get("population_density", 800) / 1600.0,
                row.get("literacy_rate", 93) / 100.0,
                row.get("urban_pct", 30) / 100.0,
                row.get("hindu_pct", 55) / 100.0,
                row.get("muslim_pct", 25) / 100.0,
                row.get("christian_pct", 18) / 100.0,
            ])

            # Reserved seat
            f.append(float(row.get("is_reserved", 0)))

            # Region 5-way one-hot
            region = row.get("region_5way", "")
            for r in REGIONS:
                f.append(1.0 if region == r else 0.0)

            # District one-hot
            for d in DISTRICTS:
                f.append(1.0 if row["district"] == d else 0.0)

            features.append(f)

            # Label: projected winner
            label_name = row["proj_2026_winner"]
            labels.append(self.party_to_idx.get(label_name, 3))

            # Regression target: projected vote shares
            vote_shares.append([
                row.get("proj_2026_ldf_pct", 0.35),
                row.get("proj_2026_udf_pct", 0.40),
                row.get("proj_2026_nda_pct", 0.15),
                row.get("proj_2026_others_pct", 0.02),
            ])

            meta.append({"constituency": row["constituency"], "district": row["district"]})

        return (
            np.array(features, dtype=np.float32),
            np.array(labels, dtype=np.int64),
            np.array(vote_shares, dtype=np.float32),
            meta,
        )


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
        self.regressor = nn.Sequential(
            nn.Linear(h, h // 2),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(h // 2, config.num_classes),
            nn.Softmax(dim=-1),
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
        return {
            "logits": logits,
            "probs": F.softmax(logits, dim=-1),
            "vote_shares": self.regressor(x),
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
    reg_criterion = nn.MSELoss()
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

    for epoch in range(config.epochs):
        model.train()
        for xb, yb, vsb in train_dl:
            xb, yb, vsb = xb.to(dev), yb.to(dev), vsb.to(dev)
            optimizer.zero_grad()
            out = model(xb)
            loss = (
                config.cls_weight * cls_criterion(out["logits"], yb)
                + config.reg_weight * reg_criterion(out["vote_shares"], vsb)
            )
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
        scheduler.step()

        # Validation
        model.eval()
        with torch.no_grad():
            for xb, yb, _ in val_dl:
                preds = model(xb.to(dev))["logits"].argmax(-1)
                acc = (preds == yb.to(dev)).float().mean().item()

        if acc > best_acc:
            best_acc = acc
            wait = 0
            safe_save({"model": model.state_dict(), "scaler": scaler}, ckpt_path)
        else:
            wait += 1

        if wait >= config.patience:
            break

    best_epoch = epoch + 1 - wait
    print(f"  Fold {fold_idx + 1:2d}: val_acc={best_acc:.4f}  (best @ epoch {best_epoch})")
    return best_acc


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Ensemble Prediction
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def ensemble_predict(data: ElectionDataset, config: Config) -> pd.DataFrame:
    """Average predictions across all 15 fold models."""
    print("\nGenerating ensemble predictions...")
    dev = config.device
    n_models = config.n_splits * config.n_repeats
    n_samples = len(data.labels)

    all_probs = np.zeros((n_samples, config.num_classes))
    all_vs = np.zeros((n_samples, config.num_classes))

    for i in range(n_models):
        ckpt = torch.load(
            os.path.join(_BACKEND_DIR, f"checkpoints/model_fold_{i}.pt"),
            weights_only=False,
        )
        X_scaled = ckpt["scaler"].transform(data.features).astype(np.float32)
        model = ElectionModel(X_scaled.shape[1], config).to(dev)
        model.load_state_dict(ckpt["model"])
        model.eval()
        with torch.no_grad():
            out = model(torch.from_numpy(X_scaled).to(dev))
            all_probs += out["probs"].cpu().numpy()
            all_vs += out["vote_shares"].cpu().numpy()

    all_probs /= n_models
    all_vs /= n_models

    results = []
    for i in range(n_samples):
        probs = all_probs[i]
        vs = all_vs[i]
        sorted_p = np.sort(probs)
        pred_idx = np.argmax(probs)

        results.append({
            "constituency": data.meta[i]["constituency"],
            "district": data.meta[i]["district"],
            "predicted": config.parties[pred_idx],
            "confidence": float(sorted_p[-1] - sorted_p[-2]),
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

    # Confidence stats
    avg_conf = results["confidence"].mean()
    high_conf = (results["confidence"] > 0.4).sum()
    print(f"\n  Avg confidence margin: {avg_conf:.1%}")
    print(f"  High-confidence seats (>40% margin): {high_conf}/{total}")

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

    csv_path = os.path.join(_BACKEND_DIR, "data_files", "kerala_assembly_2026.csv")
    if not os.path.exists(csv_path):
        print("ERROR: Training data not found.")
        print("  Run this first:  python create_dataset.py")
        return

    print("=" * 60)
    print("  KERALA ELECTION 2026 - MODEL TRAINING")
    print(f"  Device: {config.device}")
    print("=" * 60)

    # ── Step 1: Load data ──────────────────────────────────────
    data = ElectionDataset(csv_path)

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
    results = ensemble_predict(data, config)

    # ── Step 4: Save output ────────────────────────────────────
    out_path = os.path.join(_BACKEND_DIR, "predictions_2026.csv")
    results.to_csv(out_path, index=False)
    print(f"\n  Saved: {out_path}")

    # ── Step 5: Summary ────────────────────────────────────────
    print_summary(results, config)


if __name__ == "__main__":
    main()
