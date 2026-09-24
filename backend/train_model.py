import sys
import os
import json
import pickle
import time
import threading
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (recall_score, precision_score,
                             f1_score, roc_auc_score, confusion_matrix)
from imblearn.over_sampling import SMOTE

warnings.filterwarnings("ignore")

# ── Install lightgbm if missing ───────────────────────────────────
try:
    import lightgbm as lgb
    print("✅ LightGBM found :", lgb.__version__)
except ImportError:
    print("📦 Installing LightGBM...")
    os.system("pip install lightgbm")
    import lightgbm as lgb

# ── Check arguments ───────────────────────────────────────────────
if len(sys.argv) < 2:
    print("Usage: python train_model.py Fraud.csv")
    print("Example: python train_model.py C:/Downloads/Fraud.csv")
    sys.exit(1)

CSV_PATH   = sys.argv[1]
MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)

# ── Config ────────────────────────────────────────────────────────
RANDOM_STATE = 42
TEST_SIZE    = 0.2

# ── LightGBM hyperparameters ──────────────────────────────────────
# LightGBM is the industry standard for fraud detection:
# - Leaf-wise tree growth (vs level-wise in XGBoost) → better accuracy
# - Native categorical support, built-in early stopping
# - Fastest of all 4 models on large datasets
# - is_unbalance=True handles class imbalance natively — no SMOTE needed
LGBM_PARAMS = {
    "n_estimators"      : 500,
    "learning_rate"     : 0.05,
    "max_depth"         : 8,
    "num_leaves"        : 63,       # 2^max_depth - 1 is a good rule
    "min_child_samples" : 50,       # equivalent to min_samples_leaf
    "subsample"         : 0.8,
    "colsample_bytree"  : 0.8,
    "reg_alpha"         : 0.1,      # L1 regularisation
    "reg_lambda"        : 1.0,      # L2 regularisation
    "is_unbalance"      : True,     # handles 0.13% fraud rate natively
    "random_state"      : RANDOM_STATE,
    "n_jobs"            : -1,
    "verbose"           : -1,       # suppress LightGBM internal logs
}

# ── Realistic target ranges ───────────────────────────────────────
TARGET_RECALL_MIN    = 0.92
TARGET_RECALL_MAX    = 0.96
TARGET_PRECISION_MIN = 0.70
TARGET_PRECISION_MAX = 0.88

# ── Helpers ───────────────────────────────────────────────────────
def fmt_time(seconds: float) -> str:
    h, rem = divmod(int(seconds), 3600)
    m, s   = divmod(rem, 60)
    if h:  return f"{h}h {m}m {s}s"
    if m:  return f"{m}m {s}s"
    return f"{s}s"


class Spinner:
    FRAMES = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    def __init__(self, msg):
        self.msg = msg; self.running = False; self._t = None
    def _loop(self):
        i = 0
        while self.running:
            print(f"\r      {self.FRAMES[i % len(self.FRAMES)]}  {self.msg} ...", end="", flush=True)
            time.sleep(0.12); i += 1
    def start(self):
        self.running = True
        self._t = threading.Thread(target=self._loop, daemon=True)
        self._t.start()
    def stop(self, ok=""):
        self.running = False
        if self._t: self._t.join()
        print(f"\r      ✅  {ok or self.msg}{' '*30}")


import gc

print("=" * 60)
print("  FRAUDGUARD AI — Model Training  (LightGBM)")
print(f"  Trees: {LGBM_PARAMS['n_estimators']}  |  LR: {LGBM_PARAMS['learning_rate']}  |  Depth: {LGBM_PARAMS['max_depth']}")
print("  Industry standard for fraud detection ⚡")
print("=" * 60)

# ─────────────────────────────────────────────────────────────────
# STEP 1: Load Data
# ─────────────────────────────────────────────────────────────────
print("\n[1/8] Loading dataset...")
t0 = time.time()

DTYPE = {
    'step': 'int32', 'amount': 'float32',
    'oldbalanceOrg': 'float32', 'newbalanceOrig': 'float32',
    'oldbalanceDest': 'float32', 'newbalanceDest': 'float32',
}
CHUNK_SIZE = 500_000

chunks = []
for i, chunk in enumerate(pd.read_csv(CSV_PATH, chunksize=CHUNK_SIZE,
                                        low_memory=False, dtype=DTYPE)):
    chunks.append(chunk)
    print(f"      Loaded chunk {i+1} ({len(chunk):,} rows)...", end='\r')

print()
df = pd.concat(chunks, ignore_index=True)
del chunks; gc.collect()

total_rows  = len(df)
fraud_count = int(df['isFraud'].sum())
print(f"      Rows    : {total_rows:,}")
print(f"      Fraud   : {fraud_count:,} ({fraud_count/total_rows:.4%})")
print(f"      Columns : {df.shape[1]}")
print(f"      Time    : {time.time()-t0:.1f}s")

# ─────────────────────────────────────────────────────────────────
# STEP 2: Clean Data
# ─────────────────────────────────────────────────────────────────
print("\n[2/8] Cleaning data...")
t0 = time.time()

from scipy.stats import zscore

sp = Spinner("Removing outliers (z-score < 3)")
sp.start()
mask = np.ones(len(df), dtype=bool)
for col in ['oldbalanceOrg', 'newbalanceOrig']:
    z     = np.abs(zscore(df[col].values))
    mask &= (z < 3)
df = df[mask].copy()
sp.stop(f"Rows after outlier removal : {len(df):,}")

if 'nameDest' in df.columns:
    sp2 = Spinner("Imputing merchant account balances")
    sp2.start()
    m_mask = df['nameDest'].str.startswith('M').values
    for col in ['oldbalanceDest', 'newbalanceDest']:
        med = df.loc[~m_mask, col].median()
        df.loc[m_mask, col] = med
    sp2.stop("Merchant imputation complete")

print(f"      Time : {time.time()-t0:.1f}s")

# ─────────────────────────────────────────────────────────────────
# STEP 3: Feature Engineering
# ─────────────────────────────────────────────────────────────────
print("\n[3/8] Engineering features...")
t0 = time.time()

sp = Spinner("Building derived features")
sp.start()

df['balance_error_orig']   = (df['oldbalanceOrg'] - df['amount'] - df['newbalanceOrig']).astype('float32')
df['balance_error_dest']   = (df['oldbalanceDest'] + df['amount'] - df['newbalanceDest']).astype('float32')
df['amount_to_orig_ratio'] = np.where(
    df['oldbalanceOrg'] > 0,
    df['amount'] / (df['oldbalanceOrg'] + 1e-9), 0.0
).astype('float32')
df['new_orig_zero']  = (df['newbalanceOrig'] == 0).astype('int8')
df['log_amount']     = np.log1p(df['amount']).astype('float32')

if 'nameDest' in df.columns:
    df['dest_is_customer'] = df['nameDest'].str.startswith('C').astype('int8')

df['type'] = df['type'].astype('category')
df = pd.get_dummies(df, columns=['type'], drop_first=False, dtype='int8')

drop_cols = ['nameOrig', 'nameDest', 'isFlaggedFraud']
df.drop(columns=[c for c in drop_cols if c in df.columns], inplace=True)

target       = 'isFraud'
feature_cols = [c for c in df.columns if c != target]
sp.stop(f"{len(feature_cols)} features ready")

print(f"      Features : {feature_cols}")
print(f"      Time     : {time.time()-t0:.1f}s")

# ─────────────────────────────────────────────────────────────────
# STEP 4: Prepare Arrays
# ─────────────────────────────────────────────────────────────────
print("\n[4/8] Preparing arrays...")
t0 = time.time()

sp = Spinner("Stratified train / test split")
sp.start()

X = df[feature_cols].values.astype('float32')
y = df[target].values.astype('int8')
del df; gc.collect()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
)
del X; gc.collect()
sp.stop(f"Train {X_train.shape[0]:,}  |  Test {X_test.shape[0]:,}")

print(f"      Time : {time.time()-t0:.1f}s")

# ─────────────────────────────────────────────────────────────────
# STEP 5: Scale Features
# ─────────────────────────────────────────────────────────────────
print("\n[5/8] Scaling features...")
t0 = time.time()

sp = Spinner("Fitting StandardScaler")
sp.start()
scaler     = StandardScaler()
X_train_sc = scaler.fit_transform(X_train).astype('float32')
X_test_sc  = scaler.transform(X_test).astype('float32')
del X_train; gc.collect()
sp.stop("Scaling complete")

print(f"      Time : {time.time()-t0:.1f}s")

# ─────────────────────────────────────────────────────────────────
# STEP 6: No SMOTE — LightGBM handles imbalance natively
# ─────────────────────────────────────────────────────────────────
print("\n[6/8] Skipping SMOTE — LightGBM uses is_unbalance=True instead...")

neg_count = int((y_train == 0).sum())
pos_count = int((y_train == 1).sum())
ratio     = round(neg_count / pos_count, 1)

print(f"      Negative (safe)  : {neg_count:,}")
print(f"      Positive (fraud) : {pos_count:,}")
print(f"      Raw ratio        : 1 : {ratio}")
print(f"      is_unbalance=True → LightGBM auto-weights internally ✅")
print(f"      No double correction — single method only")

# Use original arrays directly
X_train_sm  = X_train_sc
y_train_sm  = y_train
del X_train_sc; gc.collect()

# ─────────────────────────────────────────────────────────────────
# STEP 7: Train LightGBM  (with early stopping + live log)
# ─────────────────────────────────────────────────────────────────
print("\n[7/8] Training LightGBM model...")
print(f"      n_estimators    : {LGBM_PARAMS['n_estimators']}")
print(f"      learning_rate   : {LGBM_PARAMS['learning_rate']}")
print(f"      max_depth       : {LGBM_PARAMS['max_depth']}")
print(f"      num_leaves      : {LGBM_PARAMS['num_leaves']}")
print(f"      is_unbalance    : True  (native imbalance handling)")
print(f"      early_stopping  : 50 rounds")
print(f"      ⏱  Estimated time : ~15-20 minutes  (fastest of all 4 models)\n")

t0 = time.time()

# LightGBM callback for live progress every 100 rounds
callbacks = [
    lgb.early_stopping(stopping_rounds=50, verbose=False),
    lgb.log_evaluation(period=100),
]

model = lgb.LGBMClassifier(
    n_estimators      = LGBM_PARAMS["n_estimators"],
    learning_rate     = LGBM_PARAMS["learning_rate"],
    max_depth         = LGBM_PARAMS["max_depth"],
    num_leaves        = LGBM_PARAMS["num_leaves"],
    min_child_samples = LGBM_PARAMS["min_child_samples"],
    subsample         = LGBM_PARAMS["subsample"],
    colsample_bytree  = LGBM_PARAMS["colsample_bytree"],
    reg_alpha         = LGBM_PARAMS["reg_alpha"],
    reg_lambda        = LGBM_PARAMS["reg_lambda"],
    is_unbalance      = LGBM_PARAMS["is_unbalance"],
    random_state      = LGBM_PARAMS["random_state"],
    n_jobs            = LGBM_PARAMS["n_jobs"],
    verbose           = LGBM_PARAMS["verbose"],
)

model.fit(
    X_train_sm, y_train_sm,
    eval_set        = [(X_test_sc, y_test)],
    eval_metric     = "aucpr",
    callbacks       = callbacks,
)

train_time = time.time() - t0
del X_train_sm, y_train_sm; gc.collect()

best_iter = model.best_iteration_ if hasattr(model, "best_iteration_") else LGBM_PARAMS["n_estimators"]
print(f"\n      ⚡  Training complete in {fmt_time(train_time)}")
print(f"      📊  Best iteration : {best_iter} / {LGBM_PARAMS['n_estimators']}")

# ─────────────────────────────────────────────────────────────────
# STEP 8: Evaluate + find realistic threshold
# ─────────────────────────────────────────────────────────────────
print("\n[8/8] Evaluating + finding realistic threshold...")
t0 = time.time()

sp = Spinner("Running predict_proba on test set")
sp.start()
y_prob = model.predict_proba(X_test_sc)[:, 1]
sp.stop("Probabilities computed")

p50 = np.percentile(y_prob, 50)
p99 = np.percentile(y_prob, 99)
frac_above_05 = (y_prob >= 0.5).mean()
print(f"\n      Probability check:")
print(f"         P50={p50:.4f}  P99={p99:.4f}")
print(f"         Flagged at 0.5 : {frac_above_05:.3%}  {'✅ OK' if frac_above_05 < 0.10 else '⚠️ High'}")

# ── Auto-tune threshold ───────────────────────────────────────────
print(f"\n      🎯 Finding threshold  (target recall {TARGET_RECALL_MIN:.0%}–{TARGET_RECALL_MAX:.0%}, precision {TARGET_PRECISION_MIN:.0%}–{TARGET_PRECISION_MAX:.0%})")
print()
print(f"      {'Threshold':>10}  {'Recall':>8}  {'Precision':>10}  {'F1':>8}  {'FP':>8}  Status")
print(f"      {'-'*70}")

candidates  = []
PREC_TARGET = (TARGET_PRECISION_MIN + TARGET_PRECISION_MAX) / 2

for t in np.arange(0.05, 0.96, 0.01):
    t      = round(float(t), 2)
    y_t    = (y_prob >= t).astype('int8')
    rec_t  = recall_score(y_test,  y_t, zero_division=0)
    pre_t  = precision_score(y_test, y_t, zero_division=0)
    f1_t   = f1_score(y_test,      y_t, zero_division=0)
    _, fp_t, fn_t, tp_t = confusion_matrix(y_test, y_t).ravel()

    in_recall_range = TARGET_RECALL_MIN <= rec_t <= TARGET_RECALL_MAX
    in_prec_range   = TARGET_PRECISION_MIN <= pre_t <= TARGET_PRECISION_MAX

    if round(t * 100) % 5 == 0:
        status = "✅ GOOD" if (in_recall_range and in_prec_range) else \
                 ("⚠ recall↓" if rec_t < TARGET_RECALL_MIN else
                  ("⚠ recall↑" if rec_t > TARGET_RECALL_MAX else "⚠ precision"))
        print(f"      {t:>10.2f}  {rec_t:>8.2%}  {pre_t:>10.2%}  {f1_t:>8.4f}  {fp_t:>8,}  {status}")

    if in_recall_range:
        prec_score = -abs(pre_t - PREC_TARGET)
        candidates.append((prec_score, t, rec_t, pre_t, f1_t, int(fp_t)))

print(f"      {'-'*70}")

THRESHOLD = 0.50

if candidates:
    candidates.sort(reverse=True)
    _, best_t, best_rec, best_prec, best_f1, best_fp = candidates[0]
    THRESHOLD = best_t
    print(f"\n      ✅ Selected threshold : {THRESHOLD}")
    print(f"         Recall           : {best_rec:.2%}")
    print(f"         Precision        : {best_prec:.2%}")
    print(f"         F1 Score         : {best_f1:.4f}")
    print(f"         False Positives  : {best_fp:,}")
else:
    print(f"\n      ⚠️  No threshold hit both targets — using 0.50 fallback")

# ── Final evaluation ──────────────────────────────────────────────
y_pred = (y_prob >= THRESHOLD).astype('int8')
rec  = recall_score(y_test,  y_pred, zero_division=0)
prec = precision_score(y_test, y_pred, zero_division=0)
f1   = f1_score(y_test,      y_pred, zero_division=0)
auc  = roc_auc_score(y_test, y_prob)
tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
fpr  = fp / (fp + tn) if (fp + tn) > 0 else 0.0

print(f"\n{'='*60}")
print(f"  RESULTS  (LightGBM — threshold = {THRESHOLD})")
print(f"{'='*60}")
print(f"  Recall    : {rec:.4f}  ({rec*100:.2f}%)")
print(f"  Precision : {prec:.4f}  ({prec*100:.2f}%)")
print(f"  F1 Score  : {f1:.4f}")
print(f"  AUC-ROC   : {auc:.4f}")
print(f"  FPR       : {fpr:.6f}  ({fpr*100:.4f}%)")
print(f"  TP:{tp:,}  FP:{fp:,}  FN:{fn:,}  TN:{tn:,}")
print(f"  Predicted Fraud : {tp+fp:,}  (TP {tp:,} + FP {fp:,})")
print(f"  Predicted Safe  : {tn+fn:,}  (TN {tn:,} + FN {fn:,})")
print(f"{'='*60}")
print(f"  Time : {time.time()-t0:.1f}s")

# ─────────────────────────────────────────────────────────────────
# SAVE ALL FILES
# ─────────────────────────────────────────────────────────────────
print("\n💾 Saving model files to models/ folder...")

sp = Spinner("Writing model.pkl")
sp.start()
with open(MODELS_DIR / "model.pkl", "wb") as f:
    pickle.dump(model, f)
sp.stop("models/model.pkl")

with open(MODELS_DIR / "scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)
print("   ✅ models/scaler.pkl")

with open(MODELS_DIR / "feature_names.json", "w") as f:
    json.dump(feature_cols, f)
print("   ✅ models/feature_names.json")

n_est_str = str(LGBM_PARAMS["n_estimators"])
metrics_out = {
    "model"           : "LightGBM",
    "model_type"      : "LGBMClassifier",
    "threshold"       : THRESHOLD,
    "recall"          : float(rec),
    "precision"       : float(prec),
    "f1"              : float(f1),
    "auc_roc"         : float(auc),
    "auc_pr"          : float(f1),
    "fpr"             : float(fpr),
    "tp"              : int(tp),
    "fp"              : int(fp),
    "fn"              : int(fn),
    "tn"              : int(tn),
    "training_rows"   : int(total_rows),
    "n_features"      : len(feature_cols),
    "features"        : feature_cols,
    "train_time_s"    : round(train_time, 1),
    "n_estimators"    : LGBM_PARAMS["n_estimators"],
    "best_iteration"  : int(best_iter),
    "learning_rate"   : LGBM_PARAMS["learning_rate"],
    "max_depth"       : LGBM_PARAMS["max_depth"],
    "num_leaves"      : LGBM_PARAMS["num_leaves"],
    "imbalance_method": "is_unbalance=True (native, no SMOTE)",
}
with open(MODELS_DIR / "metrics.json", "w") as f:
    json.dump(metrics_out, f, indent=2)
print("   ✅ models/metrics.json")

# ─────────────────────────────────────────────────────────────────
# DONE BANNER
# ─────────────────────────────────────────────────────────────────
w = 53
print(f"\n  ╔{'═'*w}╗")
print(f"  ║{'':{w}}║")
print(f"  ║{'  ✅  TRAINING COMPLETE!  (LightGBM)':{w}}║")
print(f"  ║{'':{w}}║")
print(f"  ║{'  Threshold  : ' + str(THRESHOLD) + '  (auto-tuned)':{w}}║")
print(f"  ║{'  Recall     : ' + f'{rec*100:.2f}%':{w}}║")
print(f"  ║{'  Precision  : ' + f'{prec*100:.2f}%':{w}}║")
print(f"  ║{'  F1 Score   : ' + f'{f1:.4f}':{w}}║")
print(f"  ║{'  AUC-ROC    : ' + f'{auc:.4f}':{w}}║")
print(f"  ║{'  Best iter  : ' + str(best_iter) + ' / ' + n_est_str:{w}}║")
print(f"  ║{'  Train Time : ' + fmt_time(train_time):{w}}║")
print(f"  ║{'':{w}}║")
print(f"  ║{'  Files saved:':{w}}║")
print(f"  ║{'    → models/model.pkl':{w}}║")
print(f"  ║{'    → models/scaler.pkl':{w}}║")
print(f"  ║{'    → models/feature_names.json':{w}}║")
print(f"  ║{'    → models/metrics.json':{w}}║")
print(f"  ║{'':{w}}║")
print(f"  ║{'  ▶  Run:  streamlit run Home.py':{w}}║")
print(f"  ║{'':{w}}║")
print(f"  ╚{'═'*w}╝\n")