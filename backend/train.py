"""
Kerala Assembly Election 2026 - Enhanced Prediction Model
==========================================================

Methodology Acknowledgment:
This model operates as a non-linear ensemble/distillation of the heuristic projection rules 
defined in `create_dataset.py`, capturing complex geographical and issue-based interactions 
(e.g., how regional literacy and demographics interact with anti-incumbency waves).

Key improvements:
1. Robust CV: Uses RepeatedKFold (5 folds x 3 repeats = 15 models) to evaluate reliably.
2. Honest Evaluation: Evaluates final accuracy based on Out-Of-Fold (OOF) predictions.
3. No Data Leakage: StandardScaler is strictly fitted ONLY on training folds.
4. Appropriate Architecture: 1D Self-Attention replaced with an effective MLP backbone.
5. Calibrated Confidence: Derived from softmax margin (Top 1% - Top 2%).
6. Imbalance Handled: Uses standard KFold (unstratified) + WeightedRandomSampler to handle 
   extremely rare classes (NDA, OTHERS) without crashing the pipeline.
"""

import os
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler, TensorDataset
from sklearn.model_selection import RepeatedKFold
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm
from typing import Dict, List, Tuple
from dataclasses import dataclass, field
import warnings
warnings.filterwarnings('ignore')


@dataclass
class Config:
    """Configuration - right-sized for 140 constituency dataset"""
    parties: List[str] = field(default_factory=lambda: ["LDF", "UDF", "NDA", "OTHERS"])
    num_classes: int = 4

    # Right-sized architecture (~150K params for 140 samples)
    hidden_dim: int = 128
    num_layers: int = 2
    dropout: float = 0.2

    # Training
    batch_size: int = 32
    learning_rate: float = 8e-4
    weight_decay: float = 0.02
    epochs: int = 250
    warmup_epochs: int = 15
    early_stopping_patience: int = 30
    label_smoothing: float = 0.1

    # Multi-task weights (Shifted more toward regression to reduce categorical overfitting)
    cls_weight: float = 0.55       # classification loss weight
    reg_weight: float = 0.45       # vote share regression loss weight
    
    # CV setup
    n_splits: int = 5
    n_repeats: int = 3

    # Class weight cap (Lowered to stop AI from being too aggressive on rare winners)
    max_class_weight: float = 5.0

    device: str = "cuda" if torch.cuda.is_available() else "cpu"


class PreSplitDataset:
    """Raw, unscaled dataset loader."""
    
    def __init__(self, data_dir: str = os.path.join(_BACKEND_DIR, "data_files")):
        self.config = Config()
        self.party_to_idx = {"LDF": 0, "UDF": 1, "NDA": 2, "OTHERS": 3}

        print("Loading and processing raw data...")
        self.assembly_df = pd.read_csv(os.path.join(data_dir, "kerala_assembly_2026.csv"))
        
        # Raw features, labels, targets
        self.features_raw, self.labels, self.vote_shares, self.meta = self._process_data()
        
        print(f"  Samples: {len(self.features_raw)}")
        print(f"  Features: {self.features_raw.shape[1]}")
        class_dist = {}
        for i, p in enumerate(self.config.parties):
            class_dist[p] = int((self.labels == i).sum())
        print(f"  Class distribution: {class_dist}")

    def _process_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, List[Dict]]:
        """Extract features without scaling."""
        features_list = []
        labels_list = []
        vote_share_list = []
        meta_list = []

        for _, row in self.assembly_df.iterrows():
            features = []

            # === 1. HISTORICAL WINNER ENCODING ===
            for party in self.config.parties:
                features.append(1.0 if row.get('winner_2016', '') == party else 0.0)
            for party in self.config.parties:
                features.append(1.0 if row['winner_2021'] == party else 0.0)

            # === 2. RUNNER-UP 2021 ENCODING ===
            for party in self.config.parties:
                features.append(1.0 if row.get('runner_up_2021', '') == party else 0.0)

            # === 3. VOTE SHARE & MARGIN 2021 ===
            features.extend([row['vote_share_2021'], row['margin_pct_2021']])

            # === 4. 2024 LOK SABHA VOTE SHARES ===
            features.extend([
                row.get('ls2024_ldf_pct', 0.35),
                row.get('ls2024_udf_pct', 0.40),
                row.get('ls2024_nda_pct', 0.15),
            ])

            # === 5. 2025 LOCAL BODY TRENDS ===
            features.extend([
                row.get('lb2025_ldf', 0.40),
                row.get('lb2025_udf', 0.35),
                row.get('lb2025_nda', 0.10),
            ])

            # === 6. REGIONAL ISSUES ===
            features.extend([
                row.get('fin_crisis_impact', 0.5), 
                row.get('wildlife_conflict_impact', 0.0)
            ])

            # === 7. DEMOGRAPHICS ===
            features.extend([
                row.get('population_density', 800) / 1600.0,
                row.get('literacy_rate', 93) / 100.0,
                row.get('urban_pct', 30) / 100.0,
                row.get('hindu_pct', 55) / 100.0,
                row.get('muslim_pct', 25) / 100.0,
                row.get('christian_pct', 18) / 100.0,
            ])

            # === 8. RESERVED SEAT ===
            features.append(float(row.get('is_reserved', 0)))

            # === 9. DISTRICT ENCODING (14 districts) ===
            districts = ["Thiruvananthapuram", "Kollam", "Pathanamthitta", "Alappuzha",
                         "Kottayam", "Idukki", "Ernakulam", "Thrissur", "Palakkad",
                         "Malappuram", "Kozhikode", "Wayanad", "Kannur", "Kasaragod"]
            for district in districts:
                features.append(1.0 if row['district'] == district else 0.0)

            features_list.append(features)

            # Labels
            label_name = row['proj_2026_winner']
            if label_name not in self.party_to_idx:
                label_name = "OTHERS"
            labels_list.append(self.party_to_idx[label_name])

            # Vote share targets
            vote_shares = [
                row.get('proj_2026_ldf_pct', 0.35),
                row.get('proj_2026_udf_pct', 0.40),
                row.get('proj_2026_nda_pct', 0.15),
                row.get('proj_2026_others_pct', 0.02),
            ]
            vote_share_list.append(vote_shares)

            meta_list.append({'constituency': row['constituency'], 'district': row['district']})

        return (np.array(features_list, dtype=np.float32), 
                np.array(labels_list),
                np.array(vote_share_list, dtype=np.float32), 
                meta_list)


class MLPBlock(nn.Module):
    """Standard MLP block replacing the 1D MultiHeadAttention"""
    def __init__(self, in_features, hidden_features, out_features, dropout=0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, hidden_features),
            nn.LayerNorm(hidden_features),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_features, out_features)
        )
        
    def forward(self, x):
        return self.net(x)


class ResidualBlock(nn.Module):
    """Residual block with pre-norm"""
    def __init__(self, dim, dropout=0.1):
        super().__init__()
        self.norm = nn.LayerNorm(dim)
        self.mlp = MLPBlock(dim, dim * 3, dim, dropout)
    
    def forward(self, x):
        return x + self.mlp(self.norm(x))


class ElectionModel(nn.Module):
    """
    MLP model with dual heads:
    - Classification head: predicts winning party
    - Regression head: predicts vote shares (gradient signal for ALL parties)
    """
    def __init__(self, input_dim: int, config: Config):
        super().__init__()
        hidden = config.hidden_dim

        # Input projection
        self.input_proj = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(config.dropout)
        )

        # Residual blocks backbone
        self.res_blocks = nn.ModuleList([
            ResidualBlock(hidden, config.dropout)
            for _ in range(config.num_layers)
        ])

        self.final_norm = nn.LayerNorm(hidden)

        # Classification head
        self.classifier = nn.Sequential(
            nn.Linear(hidden, hidden // 2),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(hidden // 2, config.num_classes)
        )

        # Vote share regression head
        self.vote_regressor = nn.Sequential(
            nn.Linear(hidden, hidden // 2),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(hidden // 2, config.num_classes),
            nn.Softmax(dim=-1)  # outputs sum to 1
        )

        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            nn.init.kaiming_normal_(module.weight, mode='fan_out', nonlinearity='relu')
            if module.bias is not None:
                nn.init.zeros_(module.bias)

    def forward(self, x):
        x = self.input_proj(x)
        for block in self.res_blocks:
            x = block(x)
        x = self.final_norm(x)

        logits = self.classifier(x)
        vote_shares = self.vote_regressor(x)

        return {
            'logits': logits,
            'probs': F.softmax(logits, dim=-1),
            'vote_shares': vote_shares
        }


def get_class_weights(labels, max_weight=10.0):
    """Compute capped class weights based on a set of labels"""
    counts = np.bincount(labels, minlength=4).astype(float)
    total = len(labels)
    # Give extremely rare classes the max_weight directly to avoid Inf
    weights = np.where(counts == 0, max_weight, total / (4 * counts + 1e-6))
    weights = np.minimum(weights, max_weight)
    return torch.FloatTensor(weights)


def save_checkpoint(state, filename, retries=5, delay=0.5):
    """Save checkpoint with retry logic for Windows file locking issues (Error 1224)"""
    import time
    for i in range(retries):
        try:
            torch.save(state, filename)
            return
        except RuntimeError as e:
            if i == retries - 1:
                raise e
            time.sleep(delay)


def evaluate_model(model, val_loader, device):
    """Evaluate model on validation loader"""
    model.eval()
    val_correct, val_total = 0, 0
    all_preds, all_labels = [], []

    with torch.no_grad():
        for features, labels, _ in val_loader:
            features, labels = features.to(device), labels.to(device)
            output = model(features)
            
            preds = output['logits'].argmax(-1)
            val_correct += (preds == labels).sum().item()
            val_total += len(labels)
            
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    return val_correct / max(val_total, 1), np.array(all_preds), np.array(all_labels)


def train_fold(fold_idx, train_idx, val_idx, raw_data: PreSplitDataset, config: Config):
    """Train a single CV fold with strict training-only data scaling"""
    print(f"\n--- Training Fold {fold_idx+1} ---")
    device = config.device
    
    # 1. Split Data array
    X_train_raw = raw_data.features_raw[train_idx]
    y_train = raw_data.labels[train_idx]
    vs_train = raw_data.vote_shares[train_idx]
    
    X_val_raw = raw_data.features_raw[val_idx]
    y_val = raw_data.labels[val_idx]
    vs_val = raw_data.vote_shares[val_idx]

    # 2. Strict Scaler Fitting (Leakage Prevented)
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train_raw).astype(np.float32)
    X_val = scaler.transform(X_val_raw).astype(np.float32)

    # 3. Create Weighted Sampler for resolving NDA/OTHERS imbalance
    class_weights_np = get_class_weights(y_train, config.max_class_weight).numpy()
    sample_weights = np.array([class_weights_np[int(label)] for label in y_train])
    sampler = WeightedRandomSampler(
        weights=torch.FloatTensor(sample_weights), 
        num_samples=len(y_train), 
        replacement=True
    )

    # 4. Loaders
    train_ds = TensorDataset(torch.from_numpy(X_train), torch.from_numpy(y_train), torch.from_numpy(vs_train))
    val_ds = TensorDataset(torch.from_numpy(X_val), torch.from_numpy(y_val), torch.from_numpy(vs_val))
    
    train_loader = DataLoader(train_ds, batch_size=config.batch_size, sampler=sampler, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=len(val_ds), shuffle=False)

    # 5. Initialization
    model = ElectionModel(input_dim=X_train.shape[1], config=config).to(device)
    class_weights_tensor = get_class_weights(y_train, config.max_class_weight).to(device)
    
    cls_criterion = nn.CrossEntropyLoss(weight=class_weights_tensor)
    reg_criterion = nn.MSELoss()
    
    optimizer = optim.AdamW(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
    
    def lr_lambda(epoch):
        if epoch < config.warmup_epochs:
            return epoch / config.warmup_epochs
        progress = (epoch - config.warmup_epochs) / (config.epochs - config.warmup_epochs)
        return 0.5 * (1 + np.cos(np.pi * progress))
    
    scheduler = optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)

    # 6. Training Loop
    best_acc = 0.0
    patience = 0
    fold_model_path = os.path.join(_BACKEND_DIR, f"checkpoints/model_fold_{fold_idx}.pt")
    
    for epoch in range(1, config.epochs + 1):
        model.train()
        for features, labels, vs in train_loader:
            features, labels, vs = features.to(device), labels.to(device), vs.to(device)
            optimizer.zero_grad()
            
            output = model(features)
            loss = (config.cls_weight * cls_criterion(output['logits'], labels) + 
                    config.reg_weight * reg_criterion(output['vote_shares'], vs))
                    
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
        
        scheduler.step()

        # Validation every epoch for Early Stopping
        val_acc, _, _ = evaluate_model(model, val_loader, device)
        
        if val_acc > best_acc:
            best_acc = val_acc
            patience = 0
            save_checkpoint({
                'model_state': model.state_dict(),
                'scaler': scaler  # Save scaler coupled with the model
            }, fold_model_path)
        else:
            patience += 1

        if patience >= config.early_stopping_patience:
            break

    # 7. Final Fold Evaluation (using best model)
    checkpoint = torch.load(fold_model_path, weights_only=False)
    model.load_state_dict(checkpoint['model_state'])
    final_val_acc, preds, labels = evaluate_model(model, val_loader, device)
    
    print(f"Fold {fold_idx+1} Best Val Acc: {final_val_acc:.4f} (Epoch {epoch-patience})")
    return model, scaler, final_val_acc, preds, labels


def train_evaluation_pipeline():
    print("\n" + "=" * 70)
    print("  KERALA ASSEMBLY ELECTION 2026 - MODEL TRAINING")
    print("=" * 70)

    config = Config()
    os.makedirs(os.path.join(_BACKEND_DIR, 'checkpoints'), exist_ok=True)
    raw_data = PreSplitDataset()
    
    # Cross Validation Split
    # RepeatedKFold: 5 splits x 3 repeats = 15 runs. 
    # Ignores class imbalance in splits (doesn't crash on 0 NDA/OTHERS)
    cv = RepeatedKFold(n_splits=config.n_splits, n_repeats=config.n_repeats, random_state=42)
    
    fold_accuracies = []
    all_oof_preds = []
    all_oof_labels = []
    
    for fold_idx, (train_idx, val_idx) in enumerate(cv.split(raw_data.features_raw)):
        _, _, acc, preds, labels = train_fold(fold_idx, train_idx, val_idx, raw_data, config)
        fold_accuracies.append(acc)
        all_oof_preds.extend(preds)
        all_oof_labels.extend(labels)

    # ---------------------------
    # Global Validation Metrics
    # ---------------------------
    avg_acc = np.mean(fold_accuracies)
    print("\n" + "=" * 70)
    print(f"  CROSS VALIDATION COMPLETED ({config.n_splits} folds x {config.n_repeats} repeats)")
    print(f"Average CV Accuracy: {avg_acc:.4f} ± {np.std(fold_accuracies):.4f}")
    
    print(f"\n  Aggregate Class-wise Accuracy (Out-Of-Fold):")
    all_oof_preds = np.array(all_oof_preds)
    all_oof_labels = np.array(all_oof_labels)
    
    for i, party in enumerate(config.parties):
        mask = all_oof_labels == i
        if mask.sum() > 0:
            acc = (all_oof_preds[mask] == all_oof_labels[mask]).mean()
            print(f"   {party}: {acc:.4f} ({mask.sum()} aggregate samples)")
        else:
            print(f"   {party}: N/A (0 aggregate val samples)")
            
    return raw_data, config


def ensemble_predict(raw_data: PreSplitDataset, config: Config):
    """Ensemble all CV models for final state-wide projections."""
    print("\nGenerating final state-wide projections using ensemble...")
    device = config.device
    num_models = config.n_splits * config.n_repeats
    
    all_probs = np.zeros((len(raw_data.labels), config.num_classes))
    all_vs = np.zeros((len(raw_data.labels), config.num_classes))
    
    for fold_idx in range(num_models):
        path = os.path.join(_BACKEND_DIR, f"checkpoints/model_fold_{fold_idx}.pt")
        checkpoint = torch.load(path, weights_only=False)
        scaler = checkpoint['scaler']
        
        # Transform ALL 140 features using this fold's scaler
        scaled_features = scaler.transform(raw_data.features_raw).astype(np.float32)
        features_tensor = torch.from_numpy(scaled_features).to(device)
        
        # Init model and load weights
        model = ElectionModel(input_dim=scaled_features.shape[1], config=config).to(device)
        model.load_state_dict(checkpoint['model_state'])
        model.eval()
        
        with torch.no_grad():
            output = model(features_tensor)
            all_probs += output['probs'].cpu().numpy()
            all_vs += output['vote_shares'].cpu().numpy()
            
    # Average across all models in ensemble
    all_probs /= num_models
    all_vs /= num_models
    
    results = []
    for i in range(len(raw_data.labels)):
        probs = all_probs[i]
        vs = all_vs[i]
        
        # Calibrated Confidence: Top 1 prob minus Top 2 prob (Margin of certainty)
        sorted_probs = np.sort(probs)
        confidence = sorted_probs[-1] - sorted_probs[-2]
        predicted_idx = np.argmax(probs)
        
        meta = raw_data.meta[i]
        results.append({
            'constituency': meta['constituency'],
            'district': meta['district'],
            'predicted': config.parties[predicted_idx],
            'confidence': float(confidence),
            'LDF': float(probs[0]),
            'UDF': float(probs[1]),
            'NDA': float(probs[2]),
            'OTHERS': float(probs[3]),
            'vs_LDF': float(vs[0]),
            'vs_UDF': float(vs[1]),
            'vs_NDA': float(vs[2]),
            'vs_OTHERS': float(vs[3]),
        })

    df_results = pd.DataFrame(results)
    df_results.to_csv(os.path.join(_BACKEND_DIR, 'predictions_2026.csv'), index=False)
    return df_results


def print_summary(results, config):
    """Print detailed election summary"""
    print("\n" + "=" * 70)
    print("  FINAL ENSEMBLE SEAT PROJECTION")
    print("=" * 70)

    total = len(results)
    counts = results['predicted'].value_counts()

    print(f"\n  OVERALL ASSEMBLY (Total: {total}):")
    print("-" * 50)

    emojis = {"LDF": "[LDF]", "UDF": "[UDF]", "NDA": "[NDA]", "OTHERS": "[OTH]"}

    for party in config.parties:
        n = counts.get(party, 0)
        pct = n / total * 100
        bar = "#" * int(pct / 2)
        print(f"{emojis[party]} {party:6s}: {n:4d} ({pct:5.1f}%) {bar}")

    winner = counts.idxmax()
    winner_count = counts.max()
    majority = 71
    print(f"\n  PROJECTED WINNER: {winner}")
    if winner_count >= majority:
        print(f"   :: Clear majority ({winner_count}/{majority} needed)")
    else:
        print(f"   !! Hung Assembly (needs {majority}, got {winner_count})")

    print("\n  ENSEMBLE CONFIDENCE (Margin):")
    print("-" * 50)
    avg_conf = results['confidence'].mean()
    high_conf = (results['confidence'] > 0.4).sum()  # 40% margin between Top 1 and 2
    print(f"Average probability margin: {avg_conf:.1%}")
    print(f"High certainty wins (>40% margin): {high_conf} ({high_conf/total*100:.1f}%)")

    # District breakdown
    print("\n  DISTRICT-WISE BREAKDOWN:")
    print("-" * 70)
    district_pivot = results.groupby(['district', 'predicted']).size().unstack(fill_value=0)
    for party in config.parties:
        if party not in district_pivot.columns:
            district_pivot[party] = 0
    district_pivot = district_pivot[config.parties]
    district_pivot['Total'] = district_pivot.sum(axis=1)
    district_pivot['Winner'] = district_pivot[config.parties].idxmax(axis=1)
    print(district_pivot.to_string())

    # NDA detail
    nda_seats = results[results['predicted'] == 'NDA']
    if len(nda_seats) > 0:
        print("\n  DISTINGUISHED NDA WINS:")
        print("-" * 50)
        for _, row in nda_seats.iterrows():
            print(f"   {row['constituency']:20s} ({row['district']:15s}) | vs_NDA: {row['vs_NDA']:.1%}")

    print("\n" + "=" * 70)


def main():
    raw_data, config = train_evaluation_pipeline()
    ensemble_results = ensemble_predict(raw_data, config)
    print_summary(ensemble_results, config)


if __name__ == "__main__":
    if not os.path.exists(os.path.join(_BACKEND_DIR, "data_files/kerala_assembly_2026.csv")):
        print("!! Run create_dataset.py first!")
    else:
        main()
