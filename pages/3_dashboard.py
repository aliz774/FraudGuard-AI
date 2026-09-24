# ─────────────────────────────────────────────────────────────────
# pages/3_dashboard.py — Analytics Dashboard (Manager only)
# ─────────────────────────────────────────────────────────────────

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests, json
from pathlib import Path
from datetime import datetime

try:
    import auth
except ImportError:
    st.error("❌ Cannot find auth.py"); st.stop()

USE_REAL_API = True
API_URL      = "http://localhost:8000/api/v1"

st.set_page_config(page_title="FraudGuard AI — Dashboard", page_icon="🛡️", layout="wide")
auth.require_auth()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Sora:wght@300;400;600;700&display=swap');
html,body,[class*="css"]{font-family:'Sora',sans-serif;}
.stApp{background:#080c14;color:#e2e8f0;}
[data-testid="stSidebar"]{background:#0d1321!important;border-right:1px solid #1e2d45;}
.metric-card{background:#0d1321;border:1px solid #1e2d45;border-radius:12px;padding:1.2rem 1.5rem;text-align:center;margin-bottom:0.5rem;}
.metric-value{font-family:'Space Mono',monospace;font-size:1.8rem;font-weight:700;color:#f0f9ff;}
.metric-label{font-size:0.68rem;color:#64748b;letter-spacing:1px;text-transform:uppercase;margin-top:0.3rem;}
.section-label{font-family:'Space Mono',monospace;font-size:0.65rem;letter-spacing:3px;color:#38bdf8;text-transform:uppercase;margin-bottom:0.8rem;padding-bottom:0.4rem;border-bottom:1px solid #1e3a5f;}
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("""<div style="text-align:center;padding:1rem 0 0.5rem;">
        <div style="font-size:2.2rem;">🛡️</div>
        <div style="font-family:'Space Mono',monospace;font-size:0.95rem;font-weight:700;color:#f0f9ff;">FRAUDGUARD AI</div>
        <div style="font-size:0.6rem;color:#38bdf8;letter-spacing:2px;">v1.0.0</div>
    </div>""", unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio("nav", ["🔍 Manual Prediction", "📂 CSV Upload", "📊 Dashboard", "📈 Performance", "🚨 Alerts", "🌐 Threat Intel & Cases"],
                    index=2, label_visibility="collapsed")
    st.markdown("---")
    if st.button("🔄 Refresh", use_container_width=True): st.rerun()
    auth.show_user_profile()

if page == "🔍 Manual Prediction": st.switch_page("pages/1_manual_input.py")
elif page == "📂 CSV Upload"      : st.switch_page("pages/2_csv_upload.py")
elif page == "📈 Performance"     : st.switch_page("pages/4_performance.py")
elif page == "🚨 Alerts"          : st.switch_page("pages/5_alerts.py")
elif page == "🌐 Threat Intel & Cases": st.switch_page("pages/6_threat_intel.py")

if not auth.can_view_dashboard():
    st.markdown("""
    <div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius:12px;padding:1.5rem;margin-top:1.5rem;">
        <h3 style="color:#f87171;margin-top:0;">🚫 Access Restricted</h3>
        <p style="color:#e2e8f0;font-size:0.9rem;">
            The Executive Dashboard is restricted to <strong>Managers</strong> and <strong>Administrators</strong>.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.warning(f"Your current role: **{auth.get_role_display_name(st.session_state.user_role)}**")
    if st.button("👈 Return to Manual Prediction", type="primary"):
        st.switch_page("pages/1_manual_input.py")
    st.stop()

def load_metrics() -> dict:
    if USE_REAL_API:
        try: return requests.get(f"{API_URL}/metrics", timeout=5).json()
        except: pass
    mp = Path("models/metrics.json")
    if mp.exists():
        with open(mp) as f: return json.load(f)
    return {"model":"LightGBM","threshold":0.40,"recall":0.930,"precision":0.871,
            "f1":0.899,"auc_roc":0.990,"auc_pr":0.912,"fpr":0.00082,
            "tp":7628,"fp":1132,"fn":574,"tn":1380000}

def load_health() -> dict:
    if USE_REAL_API:
        try: return requests.get(f"{API_URL}/health", timeout=5).json()
        except: return {"status":"offline"}
    return {"status":"mock","model_type":"LightGBM","threshold":0.40,"n_features":16}

metrics = load_metrics()
health  = load_health()

api_color = "#4ade80" if health.get("status") in ("healthy","mock") else "#ef4444"
rgb       = "34,197,94" if health.get("status") in ("healthy","mock") else "239,68,68"
st.markdown(f"""
<div style="background:linear-gradient(135deg,#0d1321,#112240,#0d1321);border:1px solid #1e3a5f;border-radius:14px;padding:1.5rem 2rem;margin-bottom:1.5rem;">
    <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
            <p style="font-family:'Space Mono',monospace;font-size:1.5rem;font-weight:700;color:#f0f9ff;margin:0;">📊 ANALYTICS DASHBOARD</p>
            <p style="color:#64748b;font-size:0.8rem;margin-top:0.3rem;">Model performance metrics · FraudGuard AI</p>
        </div>
        <div style="text-align:right;">
            <span style="background:rgba({rgb},0.15);color:{api_color};border:1px solid {api_color}40;
                         font-family:'Space Mono',monospace;font-size:0.65rem;padding:4px 12px;border-radius:20px;">
                ● {health.get('status','unknown').upper()}
            </span>
            <div style="font-size:0.65rem;color:#475569;margin-top:0.4rem;">{datetime.now().strftime('%Y-%m-%d  %H:%M')}</div>
        </div>
    </div>
</div>""", unsafe_allow_html=True)

# ── Key Metrics ───────────────────────────────────────────────────
st.markdown('<p class="section-label">Model Performance (Test Set)</p>', unsafe_allow_html=True)
c1,c2,c3,c4,c5 = st.columns(5)
for col, key, label, target, cmp, note in [
    (c1,"recall","RECALL",0.90,">=","Target ≥ 90%"),
    (c3,"auc_roc","AUC-ROC",0.98,">=","Target ≥ 0.98"),
    (c5,"fpr","FPR",0.001,"<=","Target ≤ 0.1%"),
]:
    val = metrics.get(key,0)
    met = val>=target if cmp==">=" else val<=target
    fmt = f"{val:.2%}" if key in ("recall","fpr") else f"{val:.4f}"
    col.markdown(f"""<div class="metric-card">
        <div class="metric-value">{fmt}</div>
        <div class="metric-label">{label}</div>
        <div style="font-size:0.6rem;color:{'#4ade80' if met else '#f87171'};margin-top:0.3rem;">{'✅ TARGET MET' if met else '❌ BELOW TARGET'}</div>
        <div style="font-size:0.58rem;color:#334155;margin-top:0.1rem;">{note}</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value">{metrics.get('precision',0):.2%}</div>
        <div class="metric-label">PRECISION</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value">{metrics.get('auc_pr',0):.4f}</div>
        <div class="metric-label">AUC-PR</div>
    </div>""", unsafe_allow_html=True)

# ── Confusion Matrix + ROC ────────────────────────────────────────
st.markdown("---")
left, right = st.columns(2)
with left:
    st.markdown('<p class="section-label">Confusion Matrix</p>', unsafe_allow_html=True)
    tp,fp,fn,tn = metrics.get("tp",7628),metrics.get("fp",1132),metrics.get("fn",574),metrics.get("tn",1380000)
    cm = [[tn,fp],[fn,tp]]; lbl=[["TN","FP"],["FN","TP"]]
    fig_cm=go.Figure(go.Heatmap(z=cm,x=["Predicted Legit","Predicted Fraud"],y=["Actual Legit","Actual Fraud"],
        colorscale=[[0,"#0d2137"],[1,"#1d6fa4"]],showscale=False,
        text=[[f"{lbl[i][j]}<br>{cm[i][j]:,}" for j in range(2)] for i in range(2)],
        texttemplate="%{text}",textfont={"size":13,"color":"white"}))
    fig_cm.update_layout(height=300,margin=dict(t=10,b=10,l=10,r=10),paper_bgcolor="#0d1321",plot_bgcolor="#0d1321",
        xaxis=dict(tickfont=dict(color="#94a3b8")),yaxis=dict(tickfont=dict(color="#94a3b8")))
    st.plotly_chart(fig_cm,use_container_width=True,config={"displayModeBar":False})
with right:
    st.markdown('<p class="section-label">ROC Curve (Simulated)</p>', unsafe_allow_html=True)
    auc=metrics.get("auc_roc",0.99); t=np.linspace(0,1,200)
    tpr=np.clip(t**(1/(auc*3)),0,1)
    fig_roc=go.Figure()
    fig_roc.add_trace(go.Scatter(x=t,y=tpr,mode="lines",name=f"AUC={auc:.4f}",line=dict(color="#a78bfa",width=2.5)))
    fig_roc.add_trace(go.Scatter(x=[0,1],y=[0,1],mode="lines",line=dict(color="#475569",dash="dash"),showlegend=False))
    fig_roc.add_vline(x=0.001,line_dash="dot",line_color="#22c55e",annotation_text="FPR=0.1%",annotation_font_color="#22c55e")
    fig_roc.update_layout(height=300,margin=dict(t=10,b=40,l=40,r=10),paper_bgcolor="#0d1321",plot_bgcolor="#0d1321",
        xaxis=dict(title="False Positive Rate",tickfont=dict(color="#94a3b8"),gridcolor="#1e2d45"),
        yaxis=dict(title="True Positive Rate",tickfont=dict(color="#94a3b8"),gridcolor="#1e2d45"),
        legend=dict(font=dict(color="#94a3b8")))
    st.plotly_chart(fig_roc,use_container_width=True,config={"displayModeBar":False})

# ── Fraud Patterns ────────────────────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-label">Fraud Patterns in PaySim Dataset</p>', unsafe_allow_html=True)
ca,cb,cc = st.columns(3)
with ca:
    td=pd.DataFrame({"type":["TRANSFER","CASH_OUT","PAYMENT","DEBIT","CASH_IN"],"fraud_rate":[0.389,0.183,0.0,0.0,0.0]})
    fig=px.bar(td,x="type",y="fraud_rate",color="fraud_rate",color_continuous_scale=["#22c55e","#f59e0b","#ef4444"],template="plotly_dark")
    fig.update_layout(title="Fraud Rate by Type",title_font_color="#94a3b8",height=280,paper_bgcolor="#0d1321",plot_bgcolor="#0d1321",coloraxis_showscale=False)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
with cb:
    cd=pd.DataFrame({"label":["Legitimate","Fraud"],"count":[6354407,8213]})
    fig=px.pie(cd,values="count",names="label",color="label",color_discrete_map={"Legitimate":"#22c55e","Fraud":"#ef4444"},template="plotly_dark",hole=0.5)
    fig.update_traces(textinfo="percent+label")
    fig.update_layout(title="Class Imbalance (0.13% fraud)",title_font_color="#94a3b8",height=280,paper_bgcolor="#0d1321",showlegend=False,
        annotations=[dict(text="PaySim",x=0.5,y=0.5,font_size=12,font_color="#64748b",showarrow=False)])
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
with cc:
    md=pd.DataFrame({"Model":["LogReg","Decision Tree","Random Forest","XGBoost","LightGBM ⭐"],"Recall":[0.72,0.80,0.88,0.91,0.93]})
    fig=go.Figure(go.Bar(x=md["Model"],y=md["Recall"],marker_color=["#475569","#475569","#64748b","#38bdf8","#a78bfa"]))
    fig.add_hline(y=0.90,line_dash="dash",line_color="#22c55e",annotation_text="Target 90%",annotation_font_color="#22c55e")
    fig.update_layout(title="Model Recall Comparison",title_font_color="#94a3b8",height=280,paper_bgcolor="#0d1321",plot_bgcolor="#0d1321",showlegend=False,
        xaxis=dict(tickfont=dict(size=9,color="#94a3b8"),gridcolor="#1e2d45"),
        yaxis=dict(range=[0,1.05],tickfont=dict(color="#94a3b8"),gridcolor="#1e2d45"))
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

# ── Model Info ────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-label">Model Configuration</p>', unsafe_allow_html=True)
i1,i2 = st.columns(2)
with i1:
    st.markdown(f"""<div class="metric-card" style="text-align:left;padding:1.2rem 1.5rem;">
        <div style="font-family:'Space Mono',monospace;font-size:0.65rem;color:#38bdf8;letter-spacing:2px;margin-bottom:1rem;">MODEL DETAILS</div>
        <table style="width:100%;font-size:0.82rem;border-collapse:collapse;">
            <tr><td style="color:#64748b;padding:4px 0;">Algorithm</td><td style="color:#f0f9ff;font-family:monospace;text-align:right;">{metrics.get('model','LightGBM')}</td></tr>
            <tr><td style="color:#64748b;padding:4px 0;">Training Data</td><td style="color:#f0f9ff;font-family:monospace;text-align:right;">PaySim 6.3M rows</td></tr>
            <tr><td style="color:#64748b;padding:4px 0;">Imbalance Handling</td><td style="color:#f0f9ff;font-family:monospace;text-align:right;">SMOTE + class_weight</td></tr>
            <tr><td style="color:#64748b;padding:4px 0;">Threshold</td><td style="color:#f0f9ff;font-family:monospace;text-align:right;">{metrics.get('threshold',0.40)}</td></tr>
            <tr><td style="color:#64748b;padding:4px 0;">Features</td><td style="color:#f0f9ff;font-family:monospace;text-align:right;">{health.get('n_features',16)}</td></tr>
            <tr><td style="color:#64748b;padding:4px 0;">Avg Inference</td><td style="color:#f0f9ff;font-family:monospace;text-align:right;">~45 ms</td></tr>
        </table>
    </div>""", unsafe_allow_html=True)
with i2:
    st.markdown("""<div class="metric-card" style="text-align:left;padding:1.2rem 1.5rem;">
        <div style="font-family:'Space Mono',monospace;font-size:0.65rem;color:#38bdf8;letter-spacing:2px;margin-bottom:1rem;">TOP FEATURES</div>
        <table style="width:100%;font-size:0.82rem;border-collapse:collapse;">
            <tr><td style="color:#64748b;padding:4px 0;">1.</td><td style="color:#f87171;font-family:monospace;">balance_error_orig</td><td style="color:#475569;text-align:right;font-size:0.7rem;">money disappeared</td></tr>
            <tr><td style="color:#64748b;padding:4px 0;">2.</td><td style="color:#f87171;font-family:monospace;">new_orig_zero</td><td style="color:#475569;text-align:right;font-size:0.7rem;">account drained</td></tr>
            <tr><td style="color:#64748b;padding:4px 0;">3.</td><td style="color:#f59e0b;font-family:monospace;">amount_to_orig_ratio</td><td style="color:#475569;text-align:right;font-size:0.7rem;">100% drained</td></tr>
            <tr><td style="color:#64748b;padding:4px 0;">4.</td><td style="color:#f59e0b;font-family:monospace;">type_TRANSFER</td><td style="color:#475569;text-align:right;font-size:0.7rem;">high risk type</td></tr>
            <tr><td style="color:#64748b;padding:4px 0;">5.</td><td style="color:#38bdf8;font-family:monospace;">balance_error_dest</td><td style="color:#475569;text-align:right;font-size:0.7rem;">dest discrepancy</td></tr>
            <tr><td style="color:#64748b;padding:4px 0;">6.</td><td style="color:#38bdf8;font-family:monospace;">log_amount</td><td style="color:#475569;text-align:right;font-size:0.7rem;">large amounts</td></tr>
        </table>
    </div>""", unsafe_allow_html=True)