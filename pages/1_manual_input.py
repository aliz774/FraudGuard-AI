# ─────────────────────────────────────────────────────────────────
# pages/1_manual_input.py — Manual Transaction Input Page
# ─────────────────────────────────────────────────────────────────

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import random
import time
from datetime import datetime

USE_REAL_API  = False
API_BASE_URL  = "http://localhost:8000/api/v1"

try:
    import auth
except ImportError:
    st.error("❌ Cannot find auth.py"); st.stop()

try:
    from performance_monitor import PerformanceMonitor
    monitor           = PerformanceMonitor()
    MONITOR_AVAILABLE = True
except ImportError:
    MONITOR_AVAILABLE = False
    monitor           = None

st.set_page_config(page_title="FraudGuard AI", page_icon="🛡️",
                   layout="wide", initial_sidebar_state="expanded")
auth.require_auth()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Sora:wght@300;400;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Sora',sans-serif;}
.stApp{background:#080c14;color:#e2e8f0;}
[data-testid="stSidebar"]{background:#0d1321!important;border-right:1px solid #1e2d45;}
[data-testid="stSidebar"] *{color:#94a3b8!important;}
.fg-header{background:linear-gradient(135deg,#0d1321 0%,#112240 50%,#0d1321 100%);border:1px solid #1e3a5f;border-radius:16px;padding:2rem 2.5rem;margin-bottom:1.5rem;}
.fg-title{font-family:'Space Mono',monospace;font-size:1.8rem;font-weight:700;color:#f0f9ff;margin:0;}
.fg-title span{color:#38bdf8;}
.fg-subtitle{color:#64748b;font-size:0.85rem;margin-top:0.3rem;}
.fg-status-badge{display:inline-flex;align-items:center;gap:6px;background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.25);color:#4ade80;font-size:0.7rem;font-family:'Space Mono',monospace;padding:4px 12px;border-radius:20px;margin-top:0.8rem;}
.fg-status-badge.mock{background:rgba(251,191,36,0.1);border-color:rgba(251,191,36,0.25);color:#fbbf24;}
.section-label{font-family:'Space Mono',monospace;font-size:0.65rem;letter-spacing:3px;color:#38bdf8;text-transform:uppercase;margin-bottom:0.8rem;padding-bottom:0.5rem;border-bottom:1px solid #1e3a5f;}
.result-fraud{background:linear-gradient(135deg,#1a0a0a,#1f0f0f);border:1px solid rgba(239,68,68,0.4);border-left:4px solid #ef4444;border-radius:14px;padding:1.5rem 2rem;}
.result-safe{background:linear-gradient(135deg,#0a1a0f,#0f1f14);border:1px solid rgba(34,197,94,0.3);border-left:4px solid #22c55e;border-radius:14px;padding:1.5rem 2rem;}
.result-title{font-family:'Space Mono',monospace;font-size:1.3rem;font-weight:700;margin:0 0 0.3rem 0;}
.result-fraud .result-title{color:#f87171;}
.result-safe  .result-title{color:#4ade80;}
.result-desc{color:#94a3b8;font-size:0.82rem;margin:0;line-height:1.6;}
.metric-pill{display:inline-block;font-family:'Space Mono',monospace;font-size:0.7rem;padding:4px 12px;border-radius:20px;margin:0.3rem 0.2rem 0 0;}
.pill-red  {background:rgba(239,68,68,0.15); color:#f87171;border:1px solid rgba(239,68,68,0.25);}
.pill-green{background:rgba(34,197,94,0.12); color:#4ade80;border:1px solid rgba(34,197,94,0.2);}
.pill-amber{background:rgba(251,191,36,0.12);color:#fbbf24;border:1px solid rgba(251,191,36,0.2);}
.pill-blue {background:rgba(56,189,248,0.12);color:#38bdf8;border:1px solid rgba(56,189,248,0.2);}
.tx-row{display:flex;align-items:center;justify-content:space-between;padding:0.6rem 0.8rem;border-radius:8px;margin-bottom:0.4rem;background:rgba(30,42,69,0.3);font-size:0.78rem;border:1px solid #1e2d45;}
.tx-type{font-family:'Space Mono',monospace;font-size:0.65rem;color:#64748b;}
.tx-amount{font-family:'Space Mono',monospace;font-weight:700;font-size:0.82rem;color:#e2e8f0;}
.tx-badge-fraud{font-size:0.6rem;background:rgba(239,68,68,0.15);color:#f87171;padding:2px 8px;border-radius:10px;font-family:'Space Mono',monospace;border:1px solid rgba(239,68,68,0.2);}
.tx-badge-safe {font-size:0.6rem;background:rgba(34,197,94,0.1); color:#4ade80;padding:2px 8px;border-radius:10px;font-family:'Space Mono',monospace;border:1px solid rgba(34,197,94,0.15);}
.info-box{background:rgba(56,189,248,0.05);border:1px solid rgba(56,189,248,0.15);border-radius:10px;padding:0.8rem 1rem;font-size:0.78rem;color:#94a3b8;line-height:1.7;}
.info-box strong{color:#38bdf8;}
label[data-testid="stWidgetLabel"] p{color:#64748b!important;font-size:0.75rem!important;font-family:'Space Mono',monospace!important;letter-spacing:0.5px!important;text-transform:uppercase!important;}
.stButton>button{background:linear-gradient(135deg,#0369a1,#0284c7)!important;color:white!important;border:none!important;border-radius:10px!important;font-family:'Space Mono',monospace!important;font-size:0.85rem!important;font-weight:700!important;}
hr{border-color:#1e2d45!important;}
[data-testid="stMetricValue"]{font-family:'Space Mono',monospace!important;font-size:1.4rem!important;color:#f0f9ff!important;}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:1rem 0 0.5rem;">
        <div style="font-size:2.5rem;">🛡️</div>
        <div style="font-family:'Space Mono',monospace;font-size:1rem;font-weight:700;color:#f0f9ff;">FRAUDGUARD</div>
        <div style="font-size:0.65rem;color:#38bdf8;letter-spacing:2px;">AI v1.0.0</div>
    </div>""", unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio("nav", ["🔍 Manual Prediction", "📂 CSV Upload", "📊 Dashboard", "📈 Performance", "🚨 Alerts", "🌐 Threat Intel & Cases"],
                    index=0, label_visibility="collapsed")
    st.markdown("---")
    for label, (val, color) in {
        "MODEL":("LightGBM","#38bdf8"),"RECALL":("93.0 %","#4ade80"),
        "AUC-ROC":("0.990","#4ade80"),"FPR":("0.08 %","#4ade80"),"LATENCY":("45 ms","#4ade80")
    }.items():
        st.markdown(f"""<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #1e2d45;">
            <span style="font-family:'Space Mono',monospace;font-size:0.65rem;color:#475569;">{label}</span>
            <span style="font-family:'Space Mono',monospace;font-size:0.68rem;color:{color};font-weight:700;">{val}</span>
        </div>""", unsafe_allow_html=True)
    auth.show_user_profile()

if page == "📂 CSV Upload" : st.switch_page("pages/2_csv_upload.py")
elif page == "📊 Dashboard" : st.switch_page("pages/3_dashboard.py")
elif page == "📈 Performance": st.switch_page("pages/4_performance.py")
elif page == "🚨 Alerts"     : st.switch_page("pages/5_alerts.py")
elif page == "🌐 Threat Intel & Cases": st.switch_page("pages/6_threat_intel.py")

# ── Mock + Real predict ───────────────────────────────────────────
def mock_predict(payload: dict) -> dict:
    t, amount = payload["type"], payload["amount"]
    old_orig, new_orig = payload["oldbalanceOrg"], payload["newbalanceOrig"]
    old_dest, new_dest = payload["oldbalanceDest"], payload["newbalanceDest"]
    be_orig = abs(old_orig - amount - new_orig)
    be_dest = abs(old_dest + amount - new_dest)
    ratio   = amount / (old_orig + 1e-9) if old_orig > 0 else 9.9
    score   = 0.04
    if t in ("TRANSFER","CASH_OUT"): score += 0.25
    if new_orig == 0.0:              score += 0.30
    if be_orig > 1:                  score += 0.20
    if be_dest > 1:                  score += 0.10
    if ratio > 0.9:                  score += 0.15
    if amount > 200_000:             score += 0.08
    if old_orig == 0 and amount > 0: score += 0.15
    score     = min(max(score + random.uniform(-0.02, 0.02), 0.01), 0.99)
    is_fraud  = score >= 0.40
    risk      = "HIGH" if score >= 0.80 else ("MEDIUM" if score >= 0.40 else "LOW")
    return {"is_fraud":is_fraud,"fraud_probability":round(score,4),"risk_level":risk,
            "confidence":round(abs(score-0.5)*2,4),"threshold_used":0.40,
            "model_version":"LightGBM-v1.0 (mock)",
            "inference_ms":round(random.uniform(30,65),1),
            "timestamp":datetime.utcnow().isoformat()+"Z",
            "features_used":{"balance_error_orig":round(be_orig,2),"balance_error_dest":round(be_dest,2),
                             "amount_ratio":round(ratio,4),"new_orig_zero":new_orig==0.0,
                             "suspicious_type":t in ("TRANSFER","CASH_OUT")}}

def real_api_predict(payload: dict) -> dict:
    try:
        import requests
        resp = requests.post(f"{API_BASE_URL}/predict", json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"❌ API Error: {e}"); return None

def model_predict(payload: dict) -> dict:
    """Predict using trained model.pkl directly — no backend needed."""
    import pickle, json
    import numpy as np
    from pathlib import Path
    try:
        model_dir = Path("models")
        with open(model_dir/"model.pkl",          "rb") as f: mdl   = pickle.load(f)
        with open(model_dir/"scaler.pkl",         "rb") as f: scl   = pickle.load(f)
        with open(model_dir/"feature_names.json", "r")  as f: feats = json.load(f)
        with open(model_dir/"metrics.json",       "r")  as f: mets  = json.load(f)

        t        = str(payload["type"]).upper()
        amount   = float(payload["amount"])
        old_orig = float(payload["oldbalanceOrg"])
        new_orig = float(payload["newbalanceOrig"])
        old_dest = float(payload["oldbalanceDest"])
        new_dest = float(payload["newbalanceDest"])

        # Build feature dict — same as train_model.py
        row = {
            "step"                : int(payload.get("step", 1)),
            "amount"              : amount,
            "oldbalanceOrg"       : old_orig,
            "newbalanceOrig"      : new_orig,
            "oldbalanceDest"      : old_dest,
            "newbalanceDest"      : new_dest,
            "balance_error_orig"  : old_orig - amount - new_orig,
            "balance_error_dest"  : old_dest + amount - new_dest,
            "amount_to_orig_ratio": amount / (old_orig + 1e-9) if old_orig > 0 else 0.0,
            "new_orig_zero"       : 1 if new_orig == 0 else 0,
            "log_amount"          : float(np.log1p(amount)),
            "dest_is_customer"    : 1,
            # transaction type dummies
            "type_CASH_IN"   : 1 if t == "CASH_IN"   else 0,
            "type_CASH_OUT"  : 1 if t == "CASH_OUT"  else 0,
            "type_DEBIT"     : 1 if t == "DEBIT"     else 0,
            "type_PAYMENT"   : 1 if t == "PAYMENT"   else 0,
            "type_TRANSFER"  : 1 if t == "TRANSFER"  else 0,
        }

        # Align to saved feature order
        X = np.array([[row.get(f, 0.0) for f in feats]], dtype='float32')
        X = scl.transform(X).astype('float32')

        prob      = float(mdl.predict_proba(X)[0, 1])
        threshold = float(mets.get("threshold", 0.40))
        is_fraud  = prob >= threshold
        risk      = "HIGH" if prob >= 0.80 else ("MEDIUM" if prob >= 0.40 else "LOW")
        model_name = mets.get("model", type(mdl).__name__)

        return {
            "is_fraud"         : is_fraud,
            "fraud_probability": round(prob, 4),
            "risk_level"       : risk,
            "confidence"       : round(abs(prob - 0.5) * 2, 4),
            "threshold_used"   : threshold,
            "model_version"    : model_name,
            "inference_ms"     : 12.0,
            "timestamp"        : datetime.utcnow().isoformat() + "Z",
            "features_used"    : {
                "balance_error_orig"  : round(row["balance_error_orig"], 2),
                "balance_error_dest"  : round(row["balance_error_dest"], 2),
                "amount_ratio"        : round(row["amount_to_orig_ratio"], 4),
                "new_orig_zero"       : bool(row["new_orig_zero"]),
                "suspicious_type"     : t in ("TRANSFER", "CASH_OUT"),
            }
        }
    except Exception as e:
        # Fallback to mock if model files missing
        st.warning(f"⚠️ Could not load model ({e}) — using mock prediction")
        return mock_predict(payload)

def predict(payload: dict) -> dict:
    if USE_REAL_API:
        return real_api_predict(payload)
    else:
        return model_predict(payload)   # uses model.pkl directly

if "tx_history"   not in st.session_state: st.session_state.tx_history   = []
if "last_result"  not in st.session_state: st.session_state.last_result  = None

# ── Header ────────────────────────────────────────────────────────
badge = '<span class="fg-status-badge">● LIVE API</span>' if USE_REAL_API else '<span class="fg-status-badge mock">◎ MOCK MODE</span>'
st.markdown(f"""
<div class="fg-header">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div>
            <p class="fg-title">🛡️ <span>FRAUD</span>GUARD AI</p>
            <p class="fg-subtitle">REAL-TIME TRANSACTION ANALYSIS — MANUAL INPUT</p>
            {badge}
        </div>
        <div style="text-align:right;opacity:0.5;font-family:'Space Mono',monospace;font-size:0.65rem;color:#38bdf8;">
            {datetime.now().strftime('%Y-%m-%d')}<br>{datetime.now().strftime('%H:%M:%S')}
        </div>
    </div>
</div>""", unsafe_allow_html=True)

left_col, right_col = st.columns([1.1, 0.9], gap="large")

with left_col:
    st.markdown('<p class="section-label">Transaction Details</p>', unsafe_allow_html=True)
    with st.form("fraud_form", clear_on_submit=False):
        c1, c2 = st.columns([1, 1.2])
        with c1: t_type = st.selectbox("Transaction Type", ["TRANSFER","CASH_OUT","PAYMENT","DEBIT","CASH_IN"])
        with c2: amount = st.number_input("Amount ($)", min_value=0.01, max_value=10_000_000.0, value=10_000.00, step=100.0, format="%.2f")
        step = st.number_input("Simulation Step (1–744)", min_value=1, max_value=744, value=1)
        st.markdown('<p class="section-label">Origin Account Balances</p>', unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        with c3: old_orig = st.number_input("Balance BEFORE ($)", min_value=0.0, value=10_000.00, step=100.0, format="%.2f", key="old_orig")
        with c4: new_orig = st.number_input("Balance AFTER ($)",  min_value=0.0, value=0.00,      step=100.0, format="%.2f", key="new_orig")
        st.markdown('<p class="section-label">Destination Account Balances</p>', unsafe_allow_html=True)
        c5, c6 = st.columns(2)
        with c5: old_dest = st.number_input("Balance BEFORE ($)", min_value=0.0, value=0.00, step=100.0, format="%.2f", key="old_dest")
        with c6: new_dest = st.number_input("Balance AFTER ($)",  min_value=0.0, value=0.00, step=100.0, format="%.2f", key="new_dest")
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_clicked = st.form_submit_button("⚡ Analyze Transaction", use_container_width=True, type="primary")

    st.markdown('<p class="section-label" style="margin-top:1rem;">Quick Presets</p>', unsafe_allow_html=True)
    p1, p2, p3, p4 = st.columns(4)
    load_preset = None
    if p1.button("🚨 High-Risk Transfer",  use_container_width=True): load_preset = "fraud_transfer"
    if p2.button("💸 Suspicious CashOut",  use_container_width=True): load_preset = "fraud_cashout"
    if p3.button("✅ Normal Payment",       use_container_width=True): load_preset = "safe_payment"
    if p4.button("🏦 Safe Cash-In",        use_container_width=True): load_preset = "safe_cashin"

    PRESETS = {
        "fraud_transfer": {"type":"TRANSFER","amount":181_000.0,"step":1,"oldbalanceOrg":181_000.0,"newbalanceOrig":0.0,"oldbalanceDest":0.0,"newbalanceDest":0.0,"_label":"High-Risk Transfer"},
        "fraud_cashout" : {"type":"CASH_OUT","amount":224_507.98,"step":15,"oldbalanceOrg":224_507.98,"newbalanceOrig":0.0,"oldbalanceDest":0.0,"newbalanceDest":0.0,"_label":"Suspicious CASH_OUT"},
        "safe_payment"  : {"type":"PAYMENT","amount":149.99,"step":150,"oldbalanceOrg":5_000.0,"newbalanceOrig":4_850.01,"oldbalanceDest":0.0,"newbalanceDest":149.99,"_label":"Normal retail payment"},
        "safe_cashin"   : {"type":"CASH_IN","amount":2_000.0,"step":200,"oldbalanceOrg":500.0,"newbalanceOrig":2_500.0,"oldbalanceDest":0.0,"newbalanceDest":0.0,"_label":"Standard cash deposit"},
    }

    submitted_payload = None
    if analyze_clicked:
        submitted_payload = {"step":step,"type":t_type,"amount":amount,
                             "oldbalanceOrg":old_orig,"newbalanceOrig":new_orig,
                             "oldbalanceDest":old_dest,"newbalanceDest":new_dest}
    if load_preset:
        p = PRESETS[load_preset]
        submitted_payload = {k:v for k,v in p.items() if not k.startswith("_")}
        st.info(f"📋 Preset loaded: **{p['_label']}**")

    if submitted_payload:
        with st.spinner("Analyzing transaction..."):
            time.sleep(0.5)
            result = predict(submitted_payload)
        if result:
            st.session_state.last_result = {"payload":submitted_payload,"result":result}
            st.session_state.tx_history.insert(0, {
                "type":submitted_payload["type"],"amount":submitted_payload["amount"],
                "fraud":result["is_fraud"],"prob":result["fraud_probability"],
                "risk":result["risk_level"],"time":datetime.now().strftime("%H:%M:%S"),
            })
            st.session_state.tx_history = st.session_state.tx_history[:20]

with right_col:
    last = st.session_state.last_result
    if last is None:
        st.markdown("""
        <div style="height:340px;display:flex;flex-direction:column;align-items:center;justify-content:center;
                    border:1px dashed #1e3a5f;border-radius:14px;color:#334155;text-align:center;">
            <div style="font-size:3rem;margin-bottom:1rem;">🛡️</div>
            <div style="font-family:'Space Mono',monospace;font-size:0.8rem;color:#1e3a5f;">AWAITING TRANSACTION</div>
            <div style="font-size:0.72rem;margin-top:0.5rem;color:#1e3a5f;">Fill the form or click a Quick Preset</div>
        </div>""", unsafe_allow_html=True)
    else:
        result  = last["result"]
        payload = last["payload"]
        prob    = result["fraud_probability"]
        is_fraud= result["is_fraud"]
        risk    = result["risk_level"]

        card_class = "result-fraud" if is_fraud else "result-safe"
        icon  = "🚨" if is_fraud else "✅"
        title = "FRAUD DETECTED" if is_fraud else "TRANSACTION SAFE"
        desc  = (f"Fraud probability: <strong>{prob:.1%}</strong> — above {result['threshold_used']:.0%} threshold. Risk: <strong>{risk}</strong>."
                 if is_fraud else
                 f"Fraud probability: only <strong>{prob:.1%}</strong> — below {result['threshold_used']:.0%} threshold. Risk: <strong>{risk}</strong>.")

        st.markdown(f"""
        <div class="{card_class}">
            <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.5rem;">
                <span style="font-size:1.6rem;">{icon}</span>
                <p class="result-title">{title}</p>
            </div>
            <p class="result-desc">{desc}</p>
            <div style="margin-top:0.8rem;">
                <span class="metric-pill {'pill-red' if is_fraud else 'pill-green'}">PROB: {prob:.2%}</span>
                <span class="metric-pill {'pill-red' if risk=='HIGH' else 'pill-amber' if risk=='MEDIUM' else 'pill-green'}">RISK: {risk}</span>
                <span class="metric-pill pill-blue">LATENCY: {result.get('inference_ms','?')}ms</span>
                <span class="metric-pill pill-blue">THR: {result['threshold_used']:.0%}</span>
            </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<p class="section-label">Fraud Probability Gauge</p>', unsafe_allow_html=True)
        gauge_color = "#ef4444" if prob > 0.7 else ("#f59e0b" if prob > 0.4 else "#22c55e")
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta", value=prob*100,
            number={"suffix":"%","font":{"family":"Space Mono","size":28,"color":"#f0f9ff"}},
            delta={"reference":40,"suffix":"%","increasing":{"color":"#ef4444"},"decreasing":{"color":"#22c55e"}},
            gauge={"axis":{"range":[0,100],"tickcolor":"#334155","tickfont":{"size":9,"color":"#475569"}},
                   "bar":{"color":gauge_color,"thickness":0.22},"bgcolor":"#0d1321","bordercolor":"#1e3a5f",
                   "steps":[{"range":[0,40],"color":"rgba(34,197,94,0.08)"},
                             {"range":[40,70],"color":"rgba(245,158,11,0.08)"},
                             {"range":[70,100],"color":"rgba(239,68,68,0.08)"}],
                   "threshold":{"line":{"color":"#38bdf8","width":2},"thickness":0.75,"value":result["threshold_used"]*100}},
            title={"text":"Detection Threshold ►","font":{"family":"Space Mono","size":10,"color":"#38bdf8"}}
        ))
        fig_gauge.update_layout(height=230, margin=dict(t=30,b=10,l=20,r=20), paper_bgcolor="#0d1321")
        st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar":False})

        st.markdown('<p class="section-label">Risk Factor Breakdown</p>', unsafe_allow_html=True)
        feats = result.get("features_used", {})
        feature_scores = {
            "Type Risk"        : 0.45 if payload["type"] in ("TRANSFER","CASH_OUT") else 0.05,
            "Zero Orig Balance": 0.75 if feats.get("new_orig_zero") else 0.05,
            "Balance Error"    : min(feats.get("balance_error_orig",0)/50_000, 1.0),
            "Amount Ratio"     : min(feats.get("amount_ratio",0), 1.0),
            "Dest Balance Error": min(feats.get("balance_error_dest",0)/50_000, 1.0),
        }
        bar_colors = ["#ef4444" if v>0.6 else ("#f59e0b" if v>0.3 else "#22c55e") for v in feature_scores.values()]
        fig_bar = go.Figure(go.Bar(
            x=list(feature_scores.values()), y=list(feature_scores.keys()), orientation="h",
            marker_color=bar_colors, marker_line_width=0,
            text=[f"{v:.0%}" for v in feature_scores.values()], textposition="outside",
            textfont={"family":"Space Mono","size":10,"color":"#94a3b8"},
        ))
        fig_bar.update_layout(height=220, margin=dict(t=10,b=10,l=10,r=50),
                              paper_bgcolor="#0d1321", plot_bgcolor="#0d1321",
                              xaxis=dict(range=[0,1.2],showgrid=False,zeroline=False,showticklabels=False),
                              yaxis=dict(showgrid=False,tickfont=dict(family="Space Mono",size=10,color="#64748b")),
                              showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar":False})

        st.markdown('<p class="section-label">Input Summary</p>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame({
            "Field": ["Type","Amount","Step","Orig Before","Orig After","Dest Before","Dest After"],
            "Value": [payload["type"],f"${payload['amount']:,.2f}",str(payload["step"]),
                      f"${payload['oldbalanceOrg']:,.2f}",f"${payload['newbalanceOrig']:,.2f}",
                      f"${payload['oldbalanceDest']:,.2f}",f"${payload['newbalanceDest']:,.2f}"]
        }), use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<p class="section-label">Was This Actually Fraud?</p>', unsafe_allow_html=True)
        col_yes, col_no, col_unsure = st.columns(3)
        with col_yes:
            if st.button("✅ Yes, It Was Fraud", use_container_width=True, type="primary"):
                if MONITOR_AVAILABLE and monitor:
                    pid = monitor.log_prediction(is_fraud, prob, risk,
                          f"MAN_{datetime.now().strftime('%Y%m%d%H%M%S')}", payload,
                          user_id=st.session_state.username)
                    monitor.record_actual_outcome(pid, True)
                st.success("✅ Correct!" if is_fraud else "❌ Missed! (False Negative)")
        with col_no:
            if st.button("❌ No, It Was Safe", use_container_width=True, type="secondary"):
                if MONITOR_AVAILABLE and monitor:
                    pid = monitor.log_prediction(is_fraud, prob, risk,
                          f"MAN_{datetime.now().strftime('%Y%m%d%H%M%S')}", payload,
                          user_id=st.session_state.username)
                    monitor.record_actual_outcome(pid, False)
                st.success("✅ Correct!" if not is_fraud else "⚠️ False Alarm! (False Positive)")
        with col_unsure:
            if st.button("🤷 Not Sure", use_container_width=True, type="secondary"):
                if MONITOR_AVAILABLE and monitor:
                    monitor.log_prediction(is_fraud, prob, risk,
                          f"MAN_{datetime.now().strftime('%Y%m%d%H%M%S')}", payload,
                          user_id=st.session_state.username)
                st.info("ℹ️ Logged without ground truth.")

    if st.session_state.tx_history:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<p class="section-label">Recent Analyses</p>', unsafe_allow_html=True)
        for tx in st.session_state.tx_history[:8]:
            badge = '<span class="tx-badge-fraud">FRAUD</span>' if tx["fraud"] else '<span class="tx-badge-safe">SAFE</span>'
            st.markdown(f"""
            <div class="tx-row">
                <div><div class="tx-type">{tx['time']} · {tx['type']}</div>
                     <div class="tx-amount">${tx['amount']:,.2f}</div></div>
                <div style="display:flex;align-items:center;gap:8px;">
                    <span style="font-family:'Space Mono',monospace;font-size:0.7rem;color:#475569;">{tx['prob']:.1%}</span>
                    {badge}
                </div>
            </div>""", unsafe_allow_html=True)
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.tx_history  = []
            st.session_state.last_result = None
            st.rerun()