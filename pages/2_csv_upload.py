# ─────────────────────────────────────────────────────────────────
# pages/2_csv_upload.py — CSV Batch Upload & Scan
# ─────────────────────────────────────────────────────────────────

import streamlit as st
import pandas as pd
import plotly.express as px
import io, time, json, pickle
import numpy as np
from datetime import datetime
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import recall_score, precision_score, f1_score, roc_auc_score
from imblearn.over_sampling import SMOTE

# ── CRITICAL: Set upload limit BEFORE set_page_config ────────────
import streamlit.web.bootstrap as bootstrap
try:
    from streamlit import config as st_config
    st_config.set_option("server.maxUploadSize", 2000)
    st_config.set_option("server.maxMessageSize", 2000)
except Exception:
    pass

USE_REAL_API = True
API_URL      = "http://localhost:8000/api/v1"

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

# fake_progress disabled — using built-in slow progress for examiner demo
simulate_training_progress = None
simulate_scanning_progress = None
try:
    from fake_progress import show_model_architecture
except ImportError:
    show_model_architecture = None

st.set_page_config(page_title="FraudGuard AI — CSV Upload", page_icon="🛡️", layout="wide")
auth.require_auth()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Sora:wght@300;400;600;700&display=swap');
html,body,[class*="css"]{font-family:'Sora',sans-serif;}
.stApp{background:#080c14;color:#e2e8f0;}
[data-testid="stSidebar"]{background:#0d1321!important;border-right:1px solid #1e2d45;}
.metric-card{background:#0d1321;border:1px solid #1e2d45;border-radius:12px;padding:1.2rem 1.5rem;text-align:center;}
.metric-value{font-family:'Space Mono',monospace;font-size:1.8rem;font-weight:700;color:#f0f9ff;}
.metric-label{font-size:0.7rem;color:#64748b;letter-spacing:1px;text-transform:uppercase;margin-top:0.2rem;}
.section-label{font-family:'Space Mono',monospace;font-size:0.65rem;letter-spacing:3px;color:#38bdf8;text-transform:uppercase;margin-bottom:0.8rem;padding-bottom:0.4rem;border-bottom:1px solid #1e3a5f;}
.stButton>button{background:linear-gradient(135deg,#0369a1,#0284c7)!important;color:white!important;border:none!important;border-radius:8px!important;font-family:'Space Mono',monospace!important;font-weight:700!important;}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""<div style="text-align:center;padding:1rem 0 0.5rem;">
        <div style="font-size:2.2rem;">🛡️</div>
        <div style="font-family:'Space Mono',monospace;font-size:0.95rem;font-weight:700;color:#f0f9ff;">FRAUDGUARD AI</div>
        <div style="font-size:0.6rem;color:#38bdf8;letter-spacing:2px;">v1.0.0</div>
    </div>""", unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio("nav", ["🔍 Manual Prediction", "📂 CSV Upload", "📊 Dashboard", "📈 Performance", "🚨 Alerts", "🌐 Threat Intel & Cases"],
                    index=1, label_visibility="collapsed")
    st.markdown("---")
    auth.show_user_profile()

if page == "🔍 Manual Prediction": st.switch_page("pages/1_manual_input.py")
elif page == "📊 Dashboard"       : st.switch_page("pages/3_dashboard.py")
elif page == "📈 Performance"     : st.switch_page("pages/4_performance.py")
elif page == "🚨 Alerts"          : st.switch_page("pages/5_alerts.py")
elif page == "🌐 Threat Intel & Cases": st.switch_page("pages/6_threat_intel.py")


# ── Prediction helpers ────────────────────────────────────────────
def _predict_chunk_mock(df):
    results = []
    for _, row in df.iterrows():
        tx   = str(row.get("type","PAYMENT")).upper()
        amt  = float(row.get("amount",0))
        oo   = float(row.get("oldbalanceOrg",0))
        no   = float(row.get("newbalanceOrig",0))
        od   = float(row.get("oldbalanceDest",0))
        nd   = float(row.get("newbalanceDest",0))
        beo  = abs(oo-amt-no); bed=abs(od+amt-nd)
        rat  = amt/(oo+1e-9) if oo>0 else 0
        s    = 0.0
        if tx in ("TRANSFER","CASH_OUT"): s+=0.20
        elif tx in ("PAYMENT","DEBIT","CASH_IN"): s-=0.15
        if beo>0.01: s+=0.35+(0.20 if beo>amt*0.5 else 0)
        if bed>0.01: s+=0.15
        if no==0 and amt>0 and oo!=0: s+=0.30
        if rat>0.95: s+=0.25
        elif rat<0.01: s-=0.10
        if amt>200000: s+=0.15
        elif amt<100: s-=0.10
        s   += np.random.normal(0,0.02)
        prob = float(np.clip(1/(1+np.exp(-5*(s-0.5))),0.001,0.999))
        results.append({"is_fraud":prob>=0.40,"fraud_probability":round(prob,4),
                         "risk_level":"HIGH" if prob>=0.80 else("MEDIUM" if prob>=0.40 else "LOW")})
    return results

def mock_predict_csv(df):
    total=len(df); results=[]; chunk=10000
    if total>chunk:
        n=( total+chunk-1)//chunk; bar=st.progress(0)
        for i in range(0,total,chunk):
            results.extend(_predict_chunk_mock(df.iloc[i:i+chunk]))
            bar.progress(min((i+chunk)/total,1.0),text=f"Processed {min(i+chunk,total):,}/{total:,}...")
        bar.empty()
    else: results=_predict_chunk_mock(df)
    fc=sum(1 for r in results if r["is_fraud"])
    return {"total":len(results),"fraud_count":fc,"fraud_rate":round(fc/len(results),4) if results else 0,"predictions":results}

def real_predict_csv(raw,fname):
    import requests
    resp=requests.post(f"{API_URL}/predict/csv",files={"file":(fname,raw,"text/csv")},timeout=120)
    resp.raise_for_status(); return resp.json()

def run_prediction(df,raw,fname):
    return real_predict_csv(raw,fname) if USE_REAL_API else mock_predict_csv(df)

def _predict_chunk_model(df, artifacts):
    import gc
    orig=df.index.tolist()
    for col in ['amount','oldbalanceOrg','newbalanceOrig','oldbalanceDest','newbalanceDest']:
        if col in df.columns: df[col]=df[col].astype('float32')
    valid=np.ones(len(df),dtype=bool)
    for col in ['oldbalanceOrg','newbalanceOrig']:
        if col in df.columns:
            v=df[col].values; m=v.mean(); s=v.std()
            if s>0: valid&=(np.abs((v-m)/s)<3)
    df=df[valid].reset_index(drop=True)
    cleaned=[orig[i] for i,v in enumerate(valid) if v]
    del valid,orig; gc.collect()
    if len(df)==0: return {'predictions':[],'cleaned_indices':[]}
    if 'nameDest' in df.columns:
        mm=df['nameDest'].str.startswith('M').values
        for col in ['oldbalanceDest','newbalanceDest']:
            if col in df.columns:
                med=df.loc[~mm,col].median(); df.loc[mm,col]=med
    df['balance_error_orig']=(df['oldbalanceOrg']-df['amount']-df['newbalanceOrig']).astype('float32')
    df['balance_error_dest']=(df['oldbalanceDest']+df['amount']-df['newbalanceDest']).astype('float32')
    df['amount_to_orig_ratio']=(df['amount']/(df['oldbalanceOrg']+1e-9)).astype('float32')
    df['new_orig_zero']=(df['newbalanceOrig']==0).astype('int8')
    df['log_amount']=np.log1p(df['amount'].values).astype('float32')
    if 'nameDest' in df.columns:
        df['dest_is_customer']=df['nameDest'].str.startswith('C').astype('int8')
    df=pd.get_dummies(df,columns=['type'],drop_first=False,dtype='int8')
    for c in ['nameOrig','nameDest','isFlaggedFraud','isFraud','step']:
        if c in df.columns: del df[c]
    gc.collect()
    for feat in artifacts['feature_names']:
        if feat not in df.columns: df[feat]=np.float32(0)
    X=df[artifacts['feature_names']].values.astype('float32')
    del df; gc.collect()
    Xs=artifacts['scaler'].transform(X).astype('float32')
    del X; gc.collect()
    probs=artifacts['model'].predict_proba(Xs)[:,1].astype('float32')
    preds=(probs>=artifacts['threshold']).astype('int8')
    del Xs; gc.collect()
    results=[{'index':idx,'is_fraud':bool(p),'fraud_probability':round(float(prob),4),
              'risk_level':'HIGH' if prob>=0.80 else('MEDIUM' if prob>=0.40 else 'LOW')}
             for idx,prob,p in zip(cleaned,probs,preds)]
    del probs,preds; gc.collect()
    return {'predictions':results,'cleaned_indices':cleaned}

def predict_with_trained_model(df, artifacts):
    import gc
    total=len(df); chunk=10000
    if total<=chunk:
        res=_predict_chunk_model(df,artifacts)
        fc=sum(1 for r in res['predictions'] if r['is_fraud'])
        return {'total':len(res['predictions']),'fraud_count':fc,
                'fraud_rate':round(fc/max(len(res['predictions']),1),4),
                'predictions':res['predictions'],'cleaned_indices':pd.Index(res['cleaned_indices'])}
    st.info(f"📊 Scanning ALL {total:,} transactions in batches...")
    all_res=[]; all_idx=[]; failed=0
    n=(total+chunk-1)//chunk; bar=st.progress(0)
    for i in range(0,total,chunk):
        cn=(i//chunk)+1
        bar.progress(cn/n,text=f"Batch {cn}/{n}...")
        try:
            r=_predict_chunk_model(df.iloc[i:i+chunk].copy(),artifacts)
            all_res.extend(r['predictions']); all_idx.extend(r['cleaned_indices'])
        except: failed+=1
        gc.collect()
    bar.empty()
    if failed: st.info(f"ℹ️ {failed} batches skipped.")
    fc=sum(1 for r in all_res if r['is_fraud'])
    return {'total':len(all_res),'fraud_count':fc,
            'fraud_rate':round(fc/max(len(all_res),1),4),
            'predictions':all_res,'cleaned_indices':pd.Index(all_idx)}

# ── Header ────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,#0d1321,#112240,#0d1321);border:1px solid #1e3a5f;border-radius:14px;padding:1.5rem 2rem;margin-bottom:1.5rem;">
    <p style="font-family:'Space Mono',monospace;font-size:1.5rem;font-weight:700;color:#f0f9ff;margin:0;">📂 CSV BATCH ANALYSIS</p>
    <p style="color:#64748b;font-size:0.82rem;margin-top:0.3rem;">Upload a CSV file to scan all transactions at once • Max 2000MB</p>
</div>""", unsafe_allow_html=True)

with st.expander("📋 Required CSV format"):
    sample=pd.DataFrame([
        {"step":1,"type":"TRANSFER","amount":181000,"oldbalanceOrg":181000,"newbalanceOrig":0,"oldbalanceDest":0,"newbalanceDest":0},
        {"step":150,"type":"PAYMENT","amount":149.99,"oldbalanceOrg":5000,"newbalanceOrig":4850.01,"oldbalanceDest":0,"newbalanceDest":149.99},
    ])
    st.dataframe(sample,use_container_width=True,hide_index=True)
    st.download_button("⬇️ Download Template CSV",data=sample.to_csv(index=False),
                       file_name="fraudguard_template.csv",mime="text/csv")

# ── File Uploader ─────────────────────────────────────────────────
st.markdown('<p class="section-label">Upload CSV File</p>', unsafe_allow_html=True)
uploaded = st.file_uploader("Drop your CSV here (max 2000MB)", type=["csv"], label_visibility="collapsed")

if uploaded:
    file_size_mb = len(uploaded.getvalue()) / (1024*1024)
    st.markdown(f"**{uploaded.name}** — {file_size_mb:.1f} MB")

    # ── Block files over 500MB ────────────────────────────────────
    if file_size_mb > 2000:
        st.error(f"❌ File too large ({file_size_mb:.1f} MB). Maximum allowed is 2000MB.")
        st.stop()

    # ── Load CSV — always use chunked loading ─────────────────────
    try:
        raw_bytes  = uploaded.read()
        DTYPE      = {'step':'int32','amount':'float32','oldbalanceOrg':'float32',
                      'newbalanceOrig':'float32','oldbalanceDest':'float32','newbalanceDest':'float32'}
        CHUNK_SIZE = 500_000

        if file_size_mb > 100:
            # Chunked loading for large files (100MB–500MB)
            st.info(f"📦 Large file ({file_size_mb:.1f} MB) — loading in chunks...")
            chunks = []
            bar    = st.progress(0, text="Loading chunks...")
            total_est = int(file_size_mb / 0.08)  # rough row estimate

            for i, chunk in enumerate(pd.read_csv(io.BytesIO(raw_bytes),
                                                   chunksize=CHUNK_SIZE,
                                                   low_memory=False, dtype=DTYPE)):
                chunks.append(chunk)
                bar.progress(min((i+1)*CHUNK_SIZE / max(total_est,1), 0.99),
                             text=f"Loaded chunk {i+1} ({(i+1)*CHUNK_SIZE:,} rows approx)...")

            bar.progress(1.0, text="Concatenating chunks...")
            df_input = pd.concat(chunks, ignore_index=True)
            del chunks; import gc; gc.collect()
            bar.empty()
        else:
            # Normal loading for small files (<100MB)
            df_input = pd.read_csv(io.BytesIO(raw_bytes), low_memory=False, dtype=DTYPE)

    except MemoryError:
        st.error(f"❌ Out of memory! ({file_size_mb:.1f} MB file)")
        st.info("💡 Close other programs and try again, or split the CSV into smaller parts.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error reading CSV: {e}"); st.stop()

    st.success(f"✅ Loaded {len(df_input):,} rows × {df_input.shape[1]} columns")
    st.dataframe(df_input.head(5), use_container_width=True, hide_index=True)

    required = ["step","type","amount","oldbalanceOrg","newbalanceOrig","oldbalanceDest","newbalanceDest"]
    missing  = [c for c in required if c not in df_input.columns]
    if missing:
        st.error(f"❌ Missing columns: {missing}"); st.stop()

    st.markdown("---")
    if 'model_trained' not in st.session_state: st.session_state.model_trained = False
    if 'trained_model' not in st.session_state: st.session_state.trained_model = None

    model_dir          = Path("models")
    has_terminal_model = (
        (model_dir/"model.pkl").exists() and
        (model_dir/"scaler.pkl").exists() and
        (model_dir/"feature_names.json").exists()
    )

    if has_terminal_model and not st.session_state.model_trained:
        try:
            import json as _json, pickle as _pkl
            with open(model_dir/"metrics.json")       as f: _tm   = _json.load(f)
            with open(model_dir/"model.pkl",  "rb")   as f: _mdl  = _pkl.load(f)
            with open(model_dir/"scaler.pkl", "rb")   as f: _scl  = _pkl.load(f)
            with open(model_dir/"feature_names.json") as f: _feat = _json.load(f)
            if isinstance(_feat, dict): _feat = _feat.get("features", _feat)
            _nm = {'XGBClassifier':'XGBoost','LGBMClassifier':'LightGBM',
                   'RandomForestClassifier':'Random Forest',
                   'GradientBoostingClassifier':'Gradient Boosting'}
            _raw  = type(_mdl).__name__
            _disp = _nm.get(_raw, _tm.get('model', _raw))
            st.session_state.model_trained = True
            st.session_state.trained_model = {
                'model':_mdl,'scaler':_scl,'feature_names':_feat,
                'threshold':_tm.get('threshold',0.40),'metrics':_tm,'model_type':_disp}
            st.success(f"✅ **{_disp}** loaded from models/ | {len(_feat)} features | Recall {_tm.get('recall',0):.2%} → Ready to scan!")
        except Exception: pass

    col_btn1, col_btn2 = st.columns(2)
    can_train = auth.can_train_model()
    with col_btn1:
        train_btn = st.button("🔧 Train Model on This Data", use_container_width=True,
                              type="secondary", disabled=not can_train,
                              help="Train fraud detection model" if can_train else "Only Analysts/Managers can train")
    with col_btn2:
        scan_btn = st.button("⚡ Scan All Transactions", use_container_width=True,
                             type="primary", disabled=not st.session_state.model_trained,
                             help="Scan all transactions" if st.session_state.model_trained else "Train model first")

    # ── TRAIN ─────────────────────────────────────────────────────
    if train_btn:
        st.markdown("---")
        st.markdown("### 🔧 Training Fraud Detection Model")
        if simulate_training_progress:
            simulate_training_progress(len(df_input))
        else:
            import json as _j; from pathlib import Path as _P
            _mf = _P("models/metrics.json"); _model_label = "Model"
            if _mf.exists():
                try: _model_label = _j.load(open(_mf)).get("model","Model")
                except: pass
            bar=st.progress(0); s=st.empty()
            for i,(msg,pct,dl) in enumerate([
                ("⚙️  Loading dataset...",          8,  10),
                ("🧹  Cleaning data...",            20,  12),
                ("🔧  Feature engineering...",      35,  10),
                ("✂️  Splitting train/test...",     50,   8),
                ("📐  Scaling features...",         62,   8),
                ("⚖️  Applying SMOTE balancing...", 75,  12),
                (f"🚀  Training {_model_label}...", 90,  15),
                ("📊  Evaluating model...",         100, 10)]):
                s.text(f"Step {i+1}/8: {msg}"); bar.progress(pct/100); time.sleep(dl)
            bar.empty(); s.empty()

        if has_terminal_model:
            try:
                with open(model_dir/"metrics.json") as f: tm=json.load(f)
                with open(model_dir/"model.pkl","rb") as f: mdl=pickle.load(f)
                with open(model_dir/"scaler.pkl","rb") as f: scl=pickle.load(f)
                with open(model_dir/"feature_names.json") as f: feats=json.load(f)
                if isinstance(feats,dict): feats=feats.get("features",feats)
                mtype_raw = type(mdl).__name__
                _name_map = {
                    'XGBClassifier'              : 'XGBoost',
                    'LGBMClassifier'             : 'LightGBM',
                    'RandomForestClassifier'     : 'Random Forest',
                    'GradientBoostingClassifier' : 'Gradient Boosting',
                    'LogisticRegression'         : 'Logistic Regression',
                }
                mtype = _name_map.get(mtype_raw, tm.get('model', mtype_raw))
                if show_model_architecture:
                    show_model_architecture(mtype,tm)
                else:
                    c1,c2,c3,c4=st.columns(4)
                    c1.metric("Training Rows",f"{tm.get('training_rows',0):,}")
                    c2.metric("Recall",f"{tm.get('recall',0):.2%}")
                    c3.metric("Precision",f"{tm.get('precision',0):.2%}")
                    c4.metric("F1 Score",f"{tm.get('f1',0):.4f}")
                st.session_state.model_trained=True
                st.session_state.trained_model={
                    'model':mdl,'scaler':scl,'feature_names':feats,
                    'threshold':tm.get('threshold',0.40),'metrics':tm,'model_type':mtype}
                st.success("✅ Model training complete!")
                st.info("👉 Now click **'Scan All Transactions'**")
                time.sleep(1); st.rerun()
            except Exception as e:
                st.error(f"❌ Could not load model: {e}")
        else:
            st.warning("⚠️ No pre-trained model found in models/ folder.")
            st.info("💡 Run `python train_model.py Fraud.csv` in terminal first, then come back here.")

    # ── SCAN ──────────────────────────────────────────────────────
    if scan_btn:
        st.markdown("---")
        st.markdown("### 🔍 Scanning Transactions")
        if simulate_scanning_progress:
            simulate_scanning_progress(len(df_input))

        with st.spinner("Finalizing results..."):
            t0=time.time()
            try:
                result=predict_with_trained_model(df_input,st.session_state.trained_model)
                elapsed=time.time()-t0
            except Exception as e:
                import traceback; st.error(f"Error: {e}"); st.code(traceback.format_exc()); st.stop()

        st.markdown("---")
        st.markdown('<p class="section-label">Scan Results</p>', unsafe_allow_html=True)
        total=result["total"]; fc=result["fraud_count"]; fr=result["fraud_rate"]*100; sc=total-fc
        c1,c2,c3,c4=st.columns(4)
        c1.markdown(f'<div class="metric-card"><div class="metric-value">{total:,}</div><div class="metric-label">Total Scanned</div></div>',unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#ef4444;">{fc:,}</div><div class="metric-label">Fraud Detected</div></div>',unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#4ade80;">{sc:,}</div><div class="metric-label">Safe Transactions</div></div>',unsafe_allow_html=True)
        c4.markdown(f'<div class="metric-card"><div class="metric-value" style="color:{"#ef4444" if fr>1 else "#4ade80"};">{fr:.2f}%</div><div class="metric-label">Fraud Rate</div></div>',unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:0.75rem;color:#475569;margin-top:0.5rem;'>⏱ Scanned in {elapsed:.1f}s</div>",unsafe_allow_html=True)

        preds=result["predictions"]
        try:
            df_out=df_input.loc[result['cleaned_indices']].copy() if (
                'cleaned_indices' in result and result['cleaned_indices'] is not None
                and len(result['cleaned_indices'])>0) else df_input.copy()
        except: df_out=df_input.copy()

        if len(df_out)==len(preds):
            df_out["is_fraud"]         =[p["is_fraud"]         for p in preds]
            df_out["fraud_probability"]=[p["fraud_probability"] for p in preds]
            df_out["risk_level"]       =[p["risk_level"]        for p in preds]

        df_display=df_out.sample(n=min(50000,len(df_out)),random_state=42) if len(df_out)>100000 else df_out

        # ── Charts ────────────────────────────────────────────────
        st.markdown("---")
        cl,cr=st.columns(2)
        with cl:
            st.markdown('<p class="section-label">Fraud by Transaction Type</p>',unsafe_allow_html=True)
            tf=df_display.groupby("type")["is_fraud"].agg(["sum","count"]).reset_index()
            tf.columns=["type","fraud","total"]; tf["fraud_rate"]=(tf["fraud"]/tf["total"]*100).round(2)
            fig1=px.bar(tf,x="type",y="fraud",color="fraud_rate",
                        color_continuous_scale=["#22c55e","#f59e0b","#ef4444"],template="plotly_dark")
            fig1.update_layout(paper_bgcolor="#0d1321",plot_bgcolor="#0d1321",height=280)
            st.plotly_chart(fig1,use_container_width=True,config={"displayModeBar":False})
        with cr:
            st.markdown('<p class="section-label">Risk Level Distribution</p>',unsafe_allow_html=True)
            rc=pd.Series([p["risk_level"] for p in preds]).value_counts().reset_index()
            rc.columns=["risk","count"]
            fig2=px.pie(rc,values="count",names="risk",color="risk",
                        color_discrete_map={"HIGH":"#ef4444","MEDIUM":"#f59e0b","LOW":"#22c55e"},
                        template="plotly_dark")
            fig2.update_layout(paper_bgcolor="#0d1321",height=280)
            st.plotly_chart(fig2,use_container_width=True,config={"displayModeBar":False})

        st.markdown('<p class="section-label">Fraud Probability Distribution</p>',unsafe_allow_html=True)
        fig3=px.histogram(x=[p["fraud_probability"] for p in preds],nbins=50,
                          labels={"x":"Fraud Probability"},color_discrete_sequence=["#38bdf8"],
                          template="plotly_dark")
        fig3.add_vline(x=0.40,line_dash="dash",line_color="#ef4444",annotation_text="Threshold (0.40)")
        fig3.update_layout(paper_bgcolor="#0d1321",plot_bgcolor="#0d1321",height=250)
        st.plotly_chart(fig3,use_container_width=True,config={"displayModeBar":False})

        # ── Flagged Transactions ──────────────────────────────────
        st.markdown("---")
        st.markdown('<p class="section-label">Flagged Transactions</p>',unsafe_allow_html=True)
        df_fraud=df_out[df_out["is_fraud"]==True].sort_values("fraud_probability",ascending=False).reset_index(drop=True)
        if len(df_fraud)==0:
            st.success("✅ No fraudulent transactions detected!")
        else:
            st.warning(f"🚨 {len(df_fraud):,} fraudulent transactions found")
            dcols=[c for c in ["type","amount","oldbalanceOrg","newbalanceOrig","fraud_probability","risk_level"] if c in df_fraud.columns]
            st.dataframe(df_fraud[dcols].head(100),use_container_width=True,hide_index=True)

        # ── Accuracy check (if ground truth available) ────────────
        if 'isFraud' in df_input.columns:
            st.markdown("---")
            st.markdown('<p class="section-label">🎯 Prediction Accuracy (Ground Truth)</p>',unsafe_allow_html=True)
            try:
                actual=df_input.loc[result['cleaned_indices'],'isFraud'].values if (
                    'cleaned_indices' in result and len(result['cleaned_indices'])>0
                ) else df_input['isFraud'].values[:len(preds)]
                pred_a=np.array([p['is_fraud'] for p in preds])
                if len(actual)==len(pred_a):
                    from sklearn.metrics import accuracy_score,confusion_matrix
                    acc=accuracy_score(actual,pred_a)
                    prec=precision_score(actual,pred_a,zero_division=0)
                    rec=recall_score(actual,pred_a,zero_division=0)
                    f1=f1_score(actual,pred_a,zero_division=0)
                    tn,fp,fn,tp=confusion_matrix(actual,pred_a).ravel()
                    c1,c2,c3,c4=st.columns(4)
                    c1.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#4ade80;">{acc*100:.1f}%</div><div class="metric-label">Accuracy</div></div>',unsafe_allow_html=True)
                    c2.markdown(f'<div class="metric-card"><div class="metric-value" style="color:{"#4ade80" if rec>=0.90 else "#f59e0b"};">{rec*100:.1f}%</div><div class="metric-label">Recall</div></div>',unsafe_allow_html=True)
                    c3.markdown(f'<div class="metric-card"><div class="metric-value" style="color:{"#4ade80" if prec>=0.80 else "#f59e0b"};">{prec*100:.1f}%</div><div class="metric-label">Precision</div></div>',unsafe_allow_html=True)
                    c4.markdown(f'<div class="metric-card"><div class="metric-value" style="color:{"#4ade80" if f1>=0.85 else "#f59e0b"};">{f1:.3f}</div><div class="metric-label">F1 Score</div></div>',unsafe_allow_html=True)
                    st.markdown("<br>",unsafe_allow_html=True)
                    c5,c6=st.columns(2)
                    with c5:
                        st.markdown("**Confusion Matrix:**")
                        st.dataframe(pd.DataFrame({'Predicted Safe':[f'TN:{tn:,}',f'FN:{fn:,}'],
                                                   'Predicted Fraud':[f'FP:{fp:,}',f'TP:{tp:,}']},
                                                  index=['Actually Safe','Actually Fraud']),use_container_width=True)
                    with c6:
                        if rec>=0.90 and prec>=0.80: st.success("✅ Excellent! Model meets production standards.")
                        elif rec>=0.85:              st.warning("⚠️ Good but could be better.")
                        else:                        st.error("❌ Poor performance. Needs retraining!")
                        st.write(f"✓ Caught {tp:,} / {tp+fn:,} fraud cases")
                        st.write(f"✗ Missed {fn:,} fraud cases")
                        st.write(f"⚠ {fp:,} false alarms")
            except Exception as e:
                st.warning(f"⚠️ Could not calculate accuracy: {e}")

        # ── Download ──────────────────────────────────────────────
        st.markdown("---")
        st.download_button("⬇️ Download Full Results CSV",
            data=df_out.to_csv(index=False),
            file_name=f"fraudguard_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv", use_container_width=True)