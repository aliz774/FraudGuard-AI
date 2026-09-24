"""
Run this AFTER training to diagnose why XGBoost predictions are wrong.
Usage: python diagnose_xgb.py Fraud.csv
"""
import sys, pickle, json, warnings
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import recall_score, precision_score, f1_score, confusion_matrix, roc_auc_score

warnings.filterwarnings("ignore")

if len(sys.argv) < 2:
    print("Usage: python diagnose_xgb.py Fraud.csv"); sys.exit(1)

CSV_PATH   = sys.argv[1]
MODELS_DIR = Path("models")

print("=" * 60)
print("  XGBoost Diagnosis")
print("=" * 60)

# ── Load model ────────────────────────────────────────────────────
print("\n[1] Loading saved model...")
with open(MODELS_DIR / "model.pkl",          "rb") as f: model   = pickle.load(f)
with open(MODELS_DIR / "scaler.pkl",         "rb") as f: scaler  = pickle.load(f)
with open(MODELS_DIR / "feature_names.json", "r")  as f: features = json.load(f)
print(f"     Model type   : {type(model).__name__}")
print(f"     Features     : {len(features)}")

# ── Load small sample of data ─────────────────────────────────────
print("\n[2] Loading data sample (first 500k rows)...")
df = pd.read_csv(CSV_PATH, nrows=500_000, low_memory=False)
print(f"     Shape  : {df.shape}")
print(f"     Fraud  : {df['isFraud'].sum():,} ({df['isFraud'].mean():.4%})")

# ── Quick feature engineering (same as train) ─────────────────────
print("\n[3] Building features...")
df['balance_error_orig']   = df['oldbalanceOrg'] - df['amount'] - df['newbalanceOrig']
df['balance_error_dest']   = df['oldbalanceDest'] + df['amount'] - df['newbalanceDest']
df['amount_to_orig_ratio'] = np.where(df['oldbalanceOrg'] > 0, df['amount'] / (df['oldbalanceOrg'] + 1e-9), 0.0)
df['new_orig_zero']        = (df['newbalanceOrig'] == 0).astype(int)
df['log_amount']           = np.log1p(df['amount'])
if 'nameDest' in df.columns:
    df['dest_is_customer'] = df['nameDest'].str.startswith('C').astype(int)
df = pd.get_dummies(df, columns=['type'], drop_first=False)
drop_cols = ['nameOrig', 'nameDest', 'isFlaggedFraud', 'isFraud']
target = df['isFraud'] if 'isFraud' in df.columns else None

# align features
for col in features:
    if col not in df.columns:
        df[col] = 0
X = df[features].values.astype('float32')
y = df['isFraud'].values

X_sc = scaler.transform(X)

# ── Get probabilities ─────────────────────────────────────────────
print("\n[4] Getting prediction probabilities...")
y_prob = model.predict_proba(X_sc)[:, 1]

print(f"\n  ── Probability Distribution ──────────────────")
print(f"     Min    : {y_prob.min():.6f}")
print(f"     Max    : {y_prob.max():.6f}")
print(f"     Mean   : {y_prob.mean():.6f}")
print(f"     Median : {np.median(y_prob):.6f}")
print(f"     P90    : {np.percentile(y_prob, 90):.6f}")
print(f"     P95    : {np.percentile(y_prob, 95):.6f}")
print(f"     P99    : {np.percentile(y_prob, 99):.6f}")
print(f"     P99.9  : {np.percentile(y_prob, 99.9):.6f}")

print(f"\n  ── Fraction flagged at each threshold ────────")
for t in [0.01, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90]:
    frac = (y_prob >= t).mean()
    n    = (y_prob >= t).sum()
    print(f"     t={t:.2f}  →  {frac:.4%}  ({n:,} flagged)")

print(f"\n  ── Per-class probabilities ───────────────────")
fraud_probs = y_prob[y == 1]
safe_probs  = y_prob[y == 0]
print(f"     FRAUD  transactions — mean prob : {fraud_probs.mean():.6f}  max: {fraud_probs.max():.6f}")
print(f"     SAFE   transactions — mean prob : {safe_probs.mean():.6f}   max: {safe_probs.max():.6f}")

print(f"\n  ── Threshold scan ────────────────────────────")
print(f"     {'t':>6}  {'Recall':>8}  {'Precision':>10}  {'F1':>8}  {'TP':>6}  {'FP':>8}")
print(f"     {'-'*55}")
for t in np.arange(0.01, 1.0, 0.05):
    t     = round(float(t), 2)
    y_t   = (y_prob >= t).astype(int)
    if y_t.sum() == 0:
        print(f"     {t:>6.2f}  {'—':>8}  {'no predictions':>10}")
        continue
    rec_t = recall_score(y, y_t, zero_division=0)
    pre_t = precision_score(y, y_t, zero_division=0)
    f1_t  = f1_score(y, y_t, zero_division=0)
    cm    = confusion_matrix(y, y_t).ravel()
    tn_t, fp_t, fn_t, tp_t = cm if len(cm) == 4 else (0, 0, 0, 0)
    print(f"     {t:>6.2f}  {rec_t:>8.2%}  {pre_t:>10.2%}  {f1_t:>8.4f}  {tp_t:>6,}  {fp_t:>8,}")

print(f"\n{'='*60}")
print(f"  DIAGNOSIS COMPLETE")
print(f"  Look at 'Per-class probabilities' above.")
print(f"  If FRAUD mean prob is near 0 → scale_pos_weight too low")
print(f"  If SAFE  mean prob is near 1 → scale_pos_weight too high")
print(f"  Best threshold is where recall ~93% and precision ~75%")
print(f"{'='*60}\n")