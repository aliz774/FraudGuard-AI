# ─────────────────────────────────────────────────────────────────
# pages/4_performance.py — Model Performance Monitor
# ─────────────────────────────────────────────────────────────────

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import json
from pathlib import Path
from datetime import datetime

try:
    import auth
except ImportError:
    st.error("❌ Cannot find auth.py"); st.stop()

try:
    from performance_monitor import PerformanceMonitor
    monitor = PerformanceMonitor()
    MONITOR_AVAILABLE = True
except ImportError:
    MONITOR_AVAILABLE = False
    monitor = None

st.set_page_config(page_title="Performance Monitor — FraudGuard AI", page_icon="📈", layout="wide")
auth.require_auth()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Sora:wght@300;400;600;700&display=swap');
html,body,[class*="css"]{font-family:'Sora',sans-serif;}
.stApp{background:#080c14;color:#e2e8f0;}
[data-testid="stSidebar"]{background:#0d1321!important;border-right:1px solid #1e2d45;}
.metric-card{background:#0d1321;border:1px solid #1e2d45;border-radius:12px;padding:1.2rem 1.5rem;text-align:center;}
.metric-value{font-family:'Space Mono',monospace;font-size:1.8rem;font-weight:700;color:#f0f9ff;}
.metric-label{font-size:0.68rem;color:#64748b;letter-spacing:1px;text-transform:uppercase;margin-top:0.3rem;}
.section-label{font-family:'Space Mono',monospace;font-size:0.65rem;letter-spacing:3px;color:#38bdf8;text-transform:uppercase;margin-bottom:0.8rem;padding-bottom:0.4rem;border-bottom:1px solid #1e3a5f;}
.alert-box{border-radius:10px;padding:0.9rem 1.1rem;font-size:0.8rem;line-height:1.7;margin:0.8rem 0;display:flex;gap:0.8rem;align-items:flex-start;}
.alert-box.warn{background:rgba(251,191,36,0.08);border:1px solid rgba(251,191,36,0.2);}
.alert-box.good{background:rgba(34,197,94,0.08);border:1px solid rgba(34,197,94,0.2);}
.stat-row{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #1e2d45;}
</style>""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""<div style="text-align:center;padding:1rem 0 0.5rem;">
        <div style="font-size:2.2rem;">🛡️</div>
        <div style="font-family:'Space Mono',monospace;font-size:0.95rem;font-weight:700;color:#f0f9ff;">FRAUDGUARD AI</div>
        <div style="font-size:0.6rem;color:#38bdf8;letter-spacing:2px;">v1.0.0</div>
    </div>""", unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio("nav", ["🔍 Manual Prediction", "📂 CSV Upload", "📊 Dashboard", "📈 Performance", "🚨 Alerts", "🌐 Threat Intel & Cases"],
                    index=3, label_visibility="collapsed")
    st.markdown("---")
    if st.button("🔄 Refresh Data", use_container_width=True): st.rerun()
    auth.show_user_profile()

if page == "🔍 Manual Prediction": st.switch_page("pages/1_manual_input.py")
elif page == "📂 CSV Upload"      : st.switch_page("pages/2_csv_upload.py")
elif page == "📊 Dashboard"       : st.switch_page("pages/3_dashboard.py")
elif page == "🚨 Alerts"          : st.switch_page("pages/5_alerts.py")
elif page == "🌐 Threat Intel & Cases": st.switch_page("pages/6_threat_intel.py")

if not auth.can_view_dashboard():
    st.markdown("""
    <div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius:12px;padding:1.5rem;margin-top:1.5rem;">
        <h3 style="color:#f87171;margin-top:0;">🚫 Access Restricted</h3>
        <p style="color:#e2e8f0;font-size:0.9rem;">
            Performance monitoring is restricted to <strong>Managers</strong> and <strong>Administrators</strong>.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.warning(f"Your current role: **{auth.get_role_display_name(st.session_state.user_role)}**")
    if st.button("👈 Return to Manual Prediction", type="primary"):
        st.switch_page("pages/1_manual_input.py")
    st.stop()

# ── Page Header ───────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,#0d1321,#112240,#0d1321);border:1px solid #1e3a5f;border-radius:14px;padding:1.5rem 2rem;margin-bottom:1.5rem;">
    <p style="font-family:'Space Mono',monospace;font-size:1.5rem;font-weight:700;color:#f0f9ff;margin:0;">📈 MODEL PERFORMANCE MONITOR</p>
    <p style="color:#64748b;font-size:0.82rem;margin-top:0.3rem;">Real-time tracking · Confusion matrix · Fraud detection accuracy</p>
</div>""", unsafe_allow_html=True)

# ── Load metrics from models/metrics.json ─────────────────────────
metrics_path = Path("models/metrics.json")
metrics = {}
if metrics_path.exists():
    with open(metrics_path) as f:
        metrics = json.load(f)

# ═══════════════════════════════════════════════════════════════════
# SECTION 1 — KEY PERFORMANCE METRICS
# ═══════════════════════════════════════════════════════════════════
st.markdown('<p class="section-label">Model Performance on Test Set</p>', unsafe_allow_html=True)

recall    = metrics.get('recall', 0)
precision = metrics.get('precision', 0)
f1        = metrics.get('f1', 0)
auc_roc   = metrics.get('auc_roc', 0)
fpr       = metrics.get('fpr', 0)
tp        = metrics.get('tp', 0)
fp        = metrics.get('fp', 0)
fn        = metrics.get('fn', 0)
tn        = metrics.get('tn', 0)
total_test         = tp + fp + fn + tn
total_fraud_actual = tp + fn

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value" style="color:{'#4ade80' if recall>=0.90 else '#f87171'};">{recall:.2%}</div>
        <div class="metric-label">Recall</div>
        <div style="font-size:0.6rem;color:{'#4ade80' if recall>=0.90 else '#f87171'};margin-top:0.3rem;">{'✅ TARGET MET' if recall>=0.90 else '❌ BELOW TARGET'}</div>
        <div style="font-size:0.58rem;color:#334155;">Target ≥ 90%</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value">{precision:.2%}</div>
        <div class="metric-label">Precision</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value">{f1:.4f}</div>
        <div class="metric-label">F1 Score</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value" style="color:{'#4ade80' if auc_roc>=0.98 else '#f87171'};">{auc_roc:.4f}</div>
        <div class="metric-label">AUC-ROC</div>
        <div style="font-size:0.6rem;color:{'#4ade80' if auc_roc>=0.98 else '#f87171'};margin-top:0.3rem;">{'✅ TARGET MET' if auc_roc>=0.98 else '❌ BELOW TARGET'}</div>
        <div style="font-size:0.58rem;color:#334155;">Target ≥ 0.98</div>
    </div>""", unsafe_allow_html=True)
with c5:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value" style="color:{'#4ade80' if fpr<=0.001 else '#f87171'};">{fpr:.4%}</div>
        <div class="metric-label">False Positive Rate</div>
        <div style="font-size:0.6rem;color:{'#4ade80' if fpr<=0.001 else '#f87171'};margin-top:0.3rem;">{'✅ TARGET MET' if fpr<=0.001 else '❌ BELOW TARGET'}</div>
        <div style="font-size:0.58rem;color:#334155;">Target ≤ 0.1%</div>
    </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# SECTION 2 — CONFUSION MATRIX (REAL VALUES)
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<p class="section-label">Confusion Matrix — Real Test Results</p>', unsafe_allow_html=True)

col_cm, col_stats = st.columns([1, 1])

with col_cm:
    cm_data = [[tn, fp], [fn, tp]]
    labels  = [[f"TN\n{tn:,}", f"FP\n{fp:,}"], [f"FN\n{fn:,}", f"TP\n{tp:,}"]]
    fig_cm = go.Figure(go.Heatmap(
        z=cm_data,
        x=["Predicted Safe", "Predicted Fraud"],
        y=["Actually Safe", "Actually Fraud"],
        colorscale=[[0,"#0d2137"],[0.5,"#1d4f7a"],[1,"#1d6fa4"]],
        showscale=False,
        text=labels,
        texttemplate="%{text}",
        textfont={"size":14, "color":"white"},
    ))
    fig_cm.update_layout(
        height=320, margin=dict(t=20,b=20,l=20,r=20),
        paper_bgcolor="#0d1321", plot_bgcolor="#0d1321",
        xaxis=dict(tickfont=dict(color="#94a3b8", size=11)),
        yaxis=dict(tickfont=dict(color="#94a3b8", size=11)),
    )
    st.plotly_chart(fig_cm, use_container_width=True, config={"displayModeBar":False})

with col_stats:
    predicted_fraud = tp + fp
    predicted_safe  = tn + fn

    # Pre-compute all strings — prevents f-string brace conflicts with HTML curly braces
    s_total      = f"{total_test:,}"
    s_fraud_act  = f"{total_fraud_actual:,}"
    s_safe_act   = f"{tn + fp:,}"
    s_tp         = f"{tp:,}"
    s_tn         = f"{tn:,}"
    s_fn         = f"{fn:,}"
    s_fp         = f"{fp:,}"
    s_pred_fraud = f"{predicted_fraud:,}"
    s_pred_safe  = f"{predicted_safe:,}"

    html_breakdown = (
        '<div style="background:#0d1321;border:1px solid #1e2d45;border-radius:12px;padding:1.5rem;">'

        '<div style="font-family:\'Space Mono\',monospace;font-size:0.65rem;color:#38bdf8;'
        'letter-spacing:2px;margin-bottom:1rem;">DETAILED BREAKDOWN</div>'

        '<div class="stat-row">'
        '<span style="color:#64748b;font-size:0.82rem;">Total Test Transactions</span>'
        '<span style="color:#f0f9ff;font-family:monospace;font-weight:700;">' + s_total + '</span>'
        '</div>'

        '<div class="stat-row">'
        '<span style="color:#64748b;font-size:0.82rem;">Actual Fraud Cases</span>'
        '<span style="color:#f87171;font-family:monospace;font-weight:700;">' + s_fraud_act + '</span>'
        '</div>'

        '<div class="stat-row">'
        '<span style="color:#64748b;font-size:0.82rem;">Actual Safe Transactions</span>'
        '<span style="color:#4ade80;font-family:monospace;font-weight:700;">' + s_safe_act + '</span>'
        '</div>'

        '<div style="margin-top:1rem;margin-bottom:0.5rem;font-family:\'Space Mono\',monospace;'
        'font-size:0.6rem;color:#38bdf8;letter-spacing:1px;">CORRECT PREDICTIONS ✅</div>'

        '<div class="stat-row">'
        '<span style="color:#64748b;font-size:0.82rem;">✅ True Positives (Fraud caught)</span>'
        '<span style="color:#4ade80;font-family:monospace;font-weight:700;">' + s_tp + '</span>'
        '</div>'

        '<div class="stat-row">'
        '<span style="color:#64748b;font-size:0.82rem;">✅ True Negatives (Safe confirmed)</span>'
        '<span style="color:#4ade80;font-family:monospace;font-weight:700;">' + s_tn + '</span>'
        '</div>'

        '<div style="margin-top:1rem;margin-bottom:0.5rem;font-family:\'Space Mono\',monospace;'
        'font-size:0.6rem;color:#ef4444;letter-spacing:1px;">ERRORS ❌</div>'

        '<div class="stat-row">'
        '<span style="color:#64748b;font-size:0.82rem;">❌ False Negatives (Fraud missed)</span>'
        '<span style="color:#f87171;font-family:monospace;font-weight:700;">' + s_fn + '</span>'
        '</div>'

        '<div class="stat-row">'
        '<span style="color:#64748b;font-size:0.82rem;">⚠️ False Positives (False alarms)</span>'
        '<span style="color:#f59e0b;font-family:monospace;font-weight:700;">' + s_fp + '</span>'
        '</div>'

        '<div style="margin-top:1rem;margin-bottom:0.5rem;font-family:\'Space Mono\',monospace;'
        'font-size:0.6rem;color:#38bdf8;letter-spacing:1px;">PREDICTION TOTALS 🎯</div>'

        '<div class="stat-row">'
        '<span style="color:#64748b;font-size:0.82rem;">🚨 Total Predicted Fraud</span>'
        '<span style="font-family:monospace;font-weight:700;">'
        '<span style="color:#f87171;">' + s_pred_fraud + '</span>'
        '<span style="color:#475569;font-size:0.7rem;"> (TP ' + s_tp + ' + FP ' + s_fp + ')</span>'
        '</span>'
        '</div>'

        '<div class="stat-row">'
        '<span style="color:#64748b;font-size:0.82rem;">✅ Total Predicted Safe</span>'
        '<span style="font-family:monospace;font-weight:700;">'
        '<span style="color:#4ade80;">' + s_pred_safe + '</span>'
        '<span style="color:#475569;font-size:0.7rem;"> (TN ' + s_tn + ' + FN ' + s_fn + ')</span>'
        '</span>'
        '</div>'

        '<div style="margin-top:1.2rem;padding:0.8rem;background:rgba(34,197,94,0.08);'
        'border:1px solid rgba(34,197,94,0.2);border-radius:8px;font-size:0.78rem;color:#4ade80;">'
        '🎯 Caught <strong>' + s_tp + ' out of ' + s_fraud_act + '</strong> fraud cases<br>'
        '🚨 Flagged <strong>' + s_pred_fraud + ' as fraud</strong> — only ' + s_fp + ' were false alarms<br>'
        'Only <strong>' + s_fn + ' missed</strong> out of ' + s_total + ' transactions'
        '</div>'

        '</div>'
    )
    st.markdown(html_breakdown, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# SECTION 3 — FRAUD DETECTION SUMMARY (Visual)
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<p class="section-label">Fraud Detection Summary</p>', unsafe_allow_html=True)

col_a, col_b, col_c = st.columns(3)

with col_a:
    recall_pct    = f"{recall:.1%}"
    tp_caught_lbl = "Fraud Caught ✅  " + f"{tp:,}"
    fn_missed_lbl = "Fraud Missed ❌  " + f"{fn:,}"
    fig_caught = go.Figure(go.Pie(
        values=[tp, fn],
        labels=[tp_caught_lbl, fn_missed_lbl],
        hole=0.6,
        marker_colors=["#4ade80", "#ef4444"],
        textinfo="percent+label",
        textfont=dict(size=11),
    ))
    fig_caught.update_layout(
        title=dict(text="Fraud Detection Rate", font=dict(color="#94a3b8", size=13)),
        height=300, paper_bgcolor="#0d1321",
        showlegend=True,
        legend=dict(font=dict(color="#94a3b8", size=10), orientation="h", y=-0.15),
        annotations=[
            dict(text=recall_pct,       x=0.5, y=0.58, font_size=20, font_color="#4ade80", showarrow=False),
            dict(text=f"{tp:,} caught", x=0.5, y=0.42, font_size=11, font_color="#94a3b8", showarrow=False),
        ]
    )
    st.plotly_chart(fig_caught, use_container_width=True, config={"displayModeBar":False})

with col_b:
    total_safe     = tn + fp
    fpr_pct        = f"{fpr:.3%}"
    tn_safe_lbl    = "Correctly Safe ✅  " + f"{tn:,}"
    fp_alarm_lbl   = "False Alarms ⚠️  " + f"{fp:,}"
    fig_fp = go.Figure(go.Pie(
        values=[tn, fp],
        labels=[tn_safe_lbl, fp_alarm_lbl],
        hole=0.6,
        marker_colors=["#38bdf8", "#f59e0b"],
        textinfo="percent+label",
        textfont=dict(size=11),
    ))
    fig_fp.update_layout(
        title=dict(text="False Alarm Rate", font=dict(color="#94a3b8", size=13)),
        height=300, paper_bgcolor="#0d1321",
        showlegend=True,
        legend=dict(font=dict(color="#94a3b8", size=10), orientation="h", y=-0.15),
        annotations=[
            dict(text=fpr_pct,                 x=0.5, y=0.58, font_size=16, font_color="#f59e0b", showarrow=False),
            dict(text=f"{fp:,} false alarms",  x=0.5, y=0.42, font_size=11, font_color="#94a3b8", showarrow=False),
        ]
    )
    st.plotly_chart(fig_fp, use_container_width=True, config={"displayModeBar":False})

with col_c:
    metrics_compare = pd.DataFrame({
        "Metric"  : ["Recall", "Precision", "F1 Score", "AUC-ROC"],
        "Achieved": [recall,   precision,   f1,         auc_roc],
        "Target"  : [0.90,     0.80,        0.85,       0.98],
    })
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=metrics_compare["Metric"], y=metrics_compare["Target"],
        name="Target", marker_color="rgba(100,116,139,0.4)",
    ))
    fig_bar.add_trace(go.Bar(
        x=metrics_compare["Metric"], y=metrics_compare["Achieved"],
        name="Achieved", marker_color="#4ade80",
    ))
    fig_bar.update_layout(
        title=dict(text="Achieved vs Target", font=dict(color="#94a3b8", size=13)),
        barmode="group", height=300,
        paper_bgcolor="#0d1321", plot_bgcolor="#0d1321",
        yaxis=dict(range=[0,1.05], tickfont=dict(color="#94a3b8"), gridcolor="#1e2d45"),
        xaxis=dict(tickfont=dict(color="#94a3b8")),
        legend=dict(font=dict(color="#94a3b8")),
    )
    st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar":False})

# ═══════════════════════════════════════════════════════════════════
# SECTION 4 — MODEL INFO
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<p class="section-label">Active Model Info</p>', unsafe_allow_html=True)

model_path = Path("models/model.pkl")
if model_path.exists() and metrics:
    model_type    = metrics.get('model_type', metrics.get('model', 'LightGBM'))
    training_rows = metrics.get('training_rows', 0)
    n_features    = metrics.get('n_features', 0)
    threshold     = metrics.get('threshold', 0.40)

    icon_map = {
        'LGBMClassifier':'⚡','LightGBM':'⚡',
        'XGBClassifier':'🚀','XGBoost':'🚀',
        'RandomForestClassifier':'🌲','Random Forest':'🌲',
    }
    icon = icon_map.get(model_type, '🤖')
    if "Random" in model_type or "Forest" in model_type:
        color = "#22c55e"   # green for Random Forest
    elif "LGBM" in model_type or "LightGBM" in model_type:
        color = "#f59e0b"   # amber for LightGBM
    elif "XGB" in model_type or "XGBoost" in model_type:
        color = "#38bdf8"   # blue for XGBoost
    else:
        color = "#10b981"   # default teal

    s_training_rows = f"{training_rows:,}"
    s_n_features    = str(n_features)
    s_threshold     = str(threshold)
    s_f1            = f"{f1:.4f}"
    s_recall        = f"{recall:.2%}"
    s_precision     = f"{precision:.2%}"
    s_auc_roc       = f"{auc_roc:.4f}"
    s_fpr           = f"{fpr:.4%}"

    html_model = (
        '<div style="background:linear-gradient(135deg,#1e3a5f,#0f2847);border:2px solid ' + color + ';'
        'border-radius:12px;padding:1.5rem;margin:1rem 0;">'

        '<div style="display:flex;align-items:center;justify-content:space-between;">'
        '<div style="display:flex;align-items:center;gap:1rem;">'
        '<div style="font-size:3rem;">' + icon + '</div>'
        '<div>'
        '<div style="font-size:0.7rem;color:#64748b;text-transform:uppercase;letter-spacing:2px;">ACTIVE MODEL</div>'
        '<div style="font-size:1.5rem;font-weight:700;color:#f0f9ff;">' + model_type + '</div>'
        '<div style="font-size:0.82rem;color:#94a3b8;">Trained on ' + s_training_rows + ' transactions · ' + s_n_features + ' features</div>'
        '</div>'
        '</div>'
        '<div style="text-align:right;">'
        '<div style="font-size:0.7rem;color:#64748b;">F1 SCORE</div>'
        '<div style="font-size:2rem;font-weight:700;color:' + color + ';">' + s_f1 + '</div>'
        '</div>'
        '</div>'

        '<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:1rem;margin-top:1.5rem;'
        'padding-top:1.5rem;border-top:1px solid rgba(56,189,248,0.2);">'
        '<div><div style="font-size:0.65rem;color:#64748b;">RECALL</div>'
        '<div style="font-size:1.1rem;color:#4ade80;font-weight:600;">' + s_recall + '</div></div>'
        '<div><div style="font-size:0.65rem;color:#64748b;">PRECISION</div>'
        '<div style="font-size:1.1rem;color:#f0f9ff;font-weight:600;">' + s_precision + '</div></div>'
        '<div><div style="font-size:0.65rem;color:#64748b;">AUC-ROC</div>'
        '<div style="font-size:1.1rem;color:#f0f9ff;font-weight:600;">' + s_auc_roc + '</div></div>'
        '<div><div style="font-size:0.65rem;color:#64748b;">THRESHOLD</div>'
        '<div style="font-size:1.1rem;color:#f0f9ff;font-weight:600;">' + s_threshold + '</div></div>'
        '<div><div style="font-size:0.65rem;color:#64748b;">FPR</div>'
        '<div style="font-size:1.1rem;color:#4ade80;font-weight:600;">' + s_fpr + '</div></div>'
        '</div>'

        '</div>'
    )
    st.markdown(html_model, unsafe_allow_html=True)
else:
    st.info("ℹ️ No trained model found. Run `python train_model.py Fraud.csv` in terminal first.")

# ═══════════════════════════════════════════════════════════════════
# SECTION 5 — LIVE PREDICTION TRACKING (from performance_monitor)
# ═══════════════════════════════════════════════════════════════════
if MONITOR_AVAILABLE:
    st.markdown("---")
    st.markdown('<p class="section-label">Live Prediction Tracking</p>', unsafe_allow_html=True)

    summary = monitor.get_summary_stats()
    drift   = monitor.get_model_drift_indicators()

    s_total_pred   = str(summary["total_predictions"])
    s_pred_24h     = str(summary["predictions_24h"])
    s_fraud_rate   = f'{summary["current_fraud_rate"]*100:.2f}%'
    s_feedback_cov = f'{summary["feedback_coverage"]*100:.1f}%'
    fraud_color    = "#ef4444" if summary["current_fraud_rate"] > 0.05 else "#4ade80"
    fb_color       = "#4ade80" if summary["feedback_coverage"] > 0.7 else "#f59e0b"

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(
        '<div class="metric-card"><div class="metric-value">' + s_total_pred + '</div>'
        '<div class="metric-label">Total Predictions</div></div>',
        unsafe_allow_html=True)
    c2.markdown(
        '<div class="metric-card"><div class="metric-value">' + s_pred_24h + '</div>'
        '<div class="metric-label">Last 24 Hours</div></div>',
        unsafe_allow_html=True)
    c3.markdown(
        '<div class="metric-card"><div class="metric-value" style="color:' + fraud_color + ';">'
        + s_fraud_rate + '</div><div class="metric-label">Current Fraud Rate (7d)</div></div>',
        unsafe_allow_html=True)
    c4.markdown(
        '<div class="metric-card"><div class="metric-value" style="color:' + fb_color + ';">'
        + s_feedback_cov + '</div><div class="metric-label">Feedback Coverage</div></div>',
        unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if drift['drift_detected']:
        st.markdown("""<div style="background:rgba(251,191,36,0.08);border:1px solid rgba(251,191,36,0.2);border-radius:10px;padding:1rem;display:flex;gap:0.8rem;">
            <div style="font-size:1.5rem;">⚠️</div>
            <div><strong style="color:#fbbf24;">Model Drift Detected!</strong><br>
            <span style="color:#94a3b8;font-size:0.82rem;">Significant changes in prediction patterns. Consider retraining.</span></div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div style="background:rgba(34,197,94,0.08);border:1px solid rgba(34,197,94,0.2);border-radius:10px;padding:1rem;display:flex;gap:0.8rem;">
            <div style="font-size:1.5rem;">✅</div>
            <div><strong style="color:#22c55e;">Model Performance Stable</strong><br>
            <span style="color:#94a3b8;font-size:0.82rem;">No significant drift detected. Model is performing as expected.</span></div>
        </div>""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────
st.markdown("---")
last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.markdown(
    '<div style="text-align:center;font-size:0.7rem;color:#475569;">Last updated: ' + last_updated + '</div>',
    unsafe_allow_html=True)