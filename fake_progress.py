# ─────────────────────────────────────────────────────────────────
# fake_progress.py — Training & Scanning Animation
# ─────────────────────────────────────────────────────────────────

import streamlit as st
import time

def simulate_training_progress(total_rows: int):
    steps = [
        ("📥 Loading dataset...",            8,  2.0),
        ("🧹 Cleaning & validating data...", 18, 2.5),
        ("⚙️  Engineering features...",      32, 2.0),
        ("✂️  Splitting train/test sets...", 45, 1.5),
        ("📐 Scaling features...",           58, 1.5),
        ("⚖️  Applying SMOTE balancing...", 72, 3.0),
        ("🌲 Training LightGBM model...",    88, 4.0),
        ("📊 Evaluating on test set...",    100, 2.0),
    ]
    progress = st.progress(0, text="Starting training pipeline...")
    status   = st.empty()
    for i, (msg, pct, delay) in enumerate(steps):
        status.markdown(f"**Step {i+1}/8:** {msg}")
        progress.progress(pct / 100, text=msg)
        time.sleep(delay)
    progress.empty()
    status.empty()

def simulate_scanning_progress(total_rows: int):
    num_chunks = max(1, total_rows // 10000)
    progress   = st.progress(0, text="Initializing scanner...")
    status     = st.empty()
    for i in range(num_chunks):
        pct      = (i + 1) / num_chunks
        rows_done = min((i + 1) * 10000, total_rows)
        progress.progress(pct, text=f"Scanning: {rows_done:,} / {total_rows:,} transactions...")
        status.markdown(f"🔍 Batch **{i+1}/{num_chunks}** — checking for fraud patterns...")
        time.sleep(0.03)
    progress.empty()
    status.empty()

def show_model_architecture(model_type: str, metrics: dict):
    st.success(f"✅ **{model_type}** model loaded successfully!")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Training Rows", f"{metrics.get('training_rows', 0):,}")
    with c2:
        st.metric("Recall",    f"{metrics.get('recall', 0):.2%}")
    with c3:
        st.metric("Precision", f"{metrics.get('precision', 0):.2%}")
    with c4:
        st.metric("AUC-ROC",   f"{metrics.get('auc_roc', 0):.4f}")