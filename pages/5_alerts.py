# ─────────────────────────────────────────────────────────────────
# pages/5_alerts.py — Alert Management System
# ─────────────────────────────────────────────────────────────────

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

try:
    import auth
except ImportError:
    st.error("❌ Cannot find auth.py"); st.stop()

st.set_page_config(page_title="Alert Management — FraudGuard AI",
                   page_icon="🚨", layout="wide")
auth.require_auth()

# ─────────────────────────────────────────────────────────────────
# ALERT DATABASE
# ─────────────────────────────────────────────────────────────────
ALERTS_DB = Path("alerts.db")

def init_alerts_db():
    conn = sqlite3.connect(ALERTS_DB)
    c    = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at    TEXT NOT NULL,
        transaction_id TEXT,
        amount        REAL,
        tx_type       TEXT,
        fraud_prob    REAL NOT NULL,
        risk_level    TEXT NOT NULL,
        priority      TEXT NOT NULL,
        status        TEXT DEFAULT 'OPEN',
        assigned_to   TEXT,
        notes         TEXT,
        resolved_at   TEXT,
        resolved_by   TEXT,
        old_balance   REAL,
        new_balance   REAL
    )""")
    conn.commit()
    conn.close()

def get_all_alerts() -> pd.DataFrame:
    conn = sqlite3.connect(ALERTS_DB)
    df   = pd.read_sql_query("SELECT * FROM alerts ORDER BY created_at DESC", conn)
    conn.close()
    return df

def get_filtered_alerts_paginated(priority: str, status: str, tx_type: str, sort_by: str, limit: int, offset: int) -> tuple[pd.DataFrame, int]:
    conn = sqlite3.connect(ALERTS_DB)
    where_clauses = []
    params = []
    
    if priority != "ALL":
        where_clauses.append("priority = ?")
        params.append(priority)
    if status != "ALL":
        where_clauses.append("status = ?")
        params.append(status)
    if tx_type != "ALL":
        where_clauses.append("tx_type = ?")
        params.append(tx_type)

    where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
    
    # Get total matching count
    c = conn.cursor()
    c.execute(f"SELECT COUNT(*) FROM alerts{where_sql}", params)
    total_filtered = c.fetchone()[0] or 0
    
    # Sort order
    order_sql = " ORDER BY created_at DESC"
    if sort_by == "Highest Amount":
        order_sql = " ORDER BY amount DESC"
    elif sort_by == "Highest Probability":
        order_sql = " ORDER BY fraud_prob DESC"

    query_sql = f"SELECT * FROM alerts{where_sql}{order_sql} LIMIT ? OFFSET ?"
    df = pd.read_sql_query(query_sql, conn, params=params + [limit, offset])
    conn.close()
    return df, total_filtered

def get_alert_by_id(alert_id: int) -> dict:
    conn = sqlite3.connect(ALERTS_DB)
    c    = conn.cursor()
    c.execute("SELECT * FROM alerts WHERE id=?", (alert_id,))
    row  = c.fetchone()
    cols = [d[0] for d in c.description]
    conn.close()
    return dict(zip(cols, row)) if row else {}

def add_alert(data: dict) -> int:
    conn = sqlite3.connect(ALERTS_DB)
    c    = conn.cursor()
    c.execute("""
    INSERT INTO alerts (created_at, transaction_id, amount, tx_type,
                        fraud_prob, risk_level, priority, status,
                        old_balance, new_balance)
    VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (
        datetime.now().isoformat(),
        data.get('transaction_id', f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
        data.get('amount', 0),
        data.get('tx_type', 'UNKNOWN'),
        data.get('fraud_prob', 0),
        data.get('risk_level', 'HIGH'),
        data.get('priority', 'HIGH'),
        'OPEN',
        data.get('old_balance', 0),
        data.get('new_balance', 0),
    ))
    alert_id = c.lastrowid
    conn.commit(); conn.close()
    return alert_id

def update_alert_status(alert_id: int, status: str, user: str, notes: str = ""):
    conn = sqlite3.connect(ALERTS_DB)
    c    = conn.cursor()
    resolved_at = datetime.now().isoformat() if status in ("RESOLVED","DISMISSED") else None
    c.execute("""
    UPDATE alerts SET status=?, resolved_by=?, resolved_at=?, notes=?
    WHERE id=?
    """, (status, user, resolved_at, notes, alert_id))
    conn.commit(); conn.close()

def assign_alert(alert_id: int, assigned_to: str):
    conn = sqlite3.connect(ALERTS_DB)
    c    = conn.cursor()
    c.execute("UPDATE alerts SET assigned_to=?, status='INVESTIGATING' WHERE id=?",
              (assigned_to, alert_id))
    conn.commit(); conn.close()

def clear_all_alerts():
    conn = sqlite3.connect(ALERTS_DB)
    c    = conn.cursor()
    c.execute("DELETE FROM alerts")
    conn.commit()
    conn.close()

def get_alert_stats() -> dict:
    conn = sqlite3.connect(ALERTS_DB)
    c    = conn.cursor()
    c.execute("""
    SELECT 
        COUNT(*),
        SUM(CASE WHEN status='OPEN' THEN 1 ELSE 0 END),
        SUM(CASE WHEN status='INVESTIGATING' THEN 1 ELSE 0 END),
        SUM(CASE WHEN status='RESOLVED' THEN 1 ELSE 0 END),
        SUM(CASE WHEN status='DISMISSED' THEN 1 ELSE 0 END),
        SUM(CASE WHEN priority='CRITICAL' THEN 1 ELSE 0 END),
        SUM(CASE WHEN priority='HIGH' THEN 1 ELSE 0 END),
        SUM(CASE WHEN priority='MEDIUM' THEN 1 ELSE 0 END)
    FROM alerts
    """)
    row = c.fetchone()
    conn.close()
    if not row or row[0] is None:
        return {"total":0,"open":0,"investigating":0,"resolved":0,"dismissed":0,"critical":0,"high":0,"medium":0}
    return {
        "total": row[0] or 0,
        "open": row[1] or 0,
        "investigating": row[2] or 0,
        "resolved": row[3] or 0,
        "dismissed": row[4] or 0,
        "critical": row[5] or 0,
        "high": row[6] or 0,
        "medium": row[7] or 0
    }

def seed_sample_alerts():
    conn = sqlite3.connect(ALERTS_DB)
    c    = conn.cursor()
    c.execute("SELECT COUNT(*) FROM alerts")
    if c.fetchone()[0] == 0:
        samples = [
            ("TXN-001", 450000, "TRANSFER", 0.9821, "HIGH",   "CRITICAL", "OPEN",          120000, 0),
            ("TXN-002", 380000, "CASH_OUT", 0.9654, "HIGH",   "CRITICAL", "INVESTIGATING",  95000,  0),
            ("TXN-003", 210000, "TRANSFER", 0.8932, "HIGH",   "HIGH",     "OPEN",           210000, 0),
            ("TXN-004", 175000, "CASH_OUT", 0.8541, "HIGH",   "HIGH",     "RESOLVED",       175000, 0),
            ("TXN-005", 95000,  "TRANSFER", 0.7823, "MEDIUM", "HIGH",     "OPEN",           95000,  0),
            ("TXN-006", 67000,  "CASH_OUT", 0.6512, "MEDIUM", "MEDIUM",   "OPEN",           67000,  0),
            ("TXN-007", 43000,  "TRANSFER", 0.5934, "MEDIUM", "MEDIUM",   "DISMISSED",      43000,  0),
            ("TXN-008", 320000, "CASH_OUT", 0.9123, "HIGH",   "CRITICAL", "OPEN",           320000, 0),
        ]
        base_time = datetime.now()
        for i, (tid,amt,typ,prob,risk,pri,status,ob,nb) in enumerate(samples):
            ts = (base_time - timedelta(hours=i*3)).isoformat()
            c.execute("""INSERT INTO alerts
                (created_at,transaction_id,amount,tx_type,fraud_prob,
                 risk_level,priority,status,old_balance,new_balance)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (ts,tid,amt,typ,prob,risk,pri,status,ob,nb))
        conn.commit()
    conn.close()

# ── Init ──────────────────────────────────────────────────────────
init_alerts_db()
seed_sample_alerts()

# ─────────────────────────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Sora:wght@300;400;600;700&display=swap');
html,body,[class*="css"]{font-family:'Sora',sans-serif;}
.stApp{background:#080c14;color:#e2e8f0;}
[data-testid="stSidebar"]{background:#0d1321!important;border-right:1px solid #1e2d45;}
.metric-card{background:linear-gradient(145deg, rgba(13, 19, 33, 0.9), rgba(17, 34, 64, 0.8));border:1px solid #1e3a5f;border-radius:12px;padding:1.2rem 1.5rem;text-align:center;box-shadow: 0 4px 15px rgba(0,0,0,0.3);}
.metric-value{font-family:'Space Mono',monospace;font-size:1.8rem;font-weight:700;color:#f0f9ff;}
.metric-label{font-size:0.68rem;color:#64748b;letter-spacing:1px;text-transform:uppercase;margin-top:0.3rem;}
.section-label{font-family:'Space Mono',monospace;font-size:0.7rem;letter-spacing:3px;color:#38bdf8;text-transform:uppercase;margin-bottom:0.8rem;padding-bottom:0.4rem;border-bottom:1px solid #1e3a5f;}
.alert-card-critical{background:linear-gradient(135deg,rgba(26,5,5,0.85),rgba(32,10,10,0.95));backdrop-filter:blur(10px);border:1px solid rgba(239,68,68,0.5);border-left:5px solid #ef4444;border-radius:12px;padding:1.1rem 1.4rem;margin-bottom:0.8rem;box-shadow: 0 5px 20px rgba(239,68,68,0.15);}
.alert-card-high{background:linear-gradient(135deg,rgba(26,15,5,0.85),rgba(32,20,5,0.95));backdrop-filter:blur(10px);border:1px solid rgba(245,158,11,0.4);border-left:5px solid #f59e0b;border-radius:12px;padding:1.1rem 1.4rem;margin-bottom:0.8rem;box-shadow: 0 5px 20px rgba(245,158,11,0.15);}
.alert-card-medium{background:linear-gradient(135deg,rgba(5,16,26,0.85),rgba(10,21,32,0.95));backdrop-filter:blur(10px);border:1px solid rgba(56,189,248,0.3);border-left:5px solid #38bdf8;border-radius:12px;padding:1.1rem 1.4rem;margin-bottom:0.8rem;box-shadow: 0 5px 20px rgba(56,189,248,0.15);}
.badge-critical{background:rgba(239,68,68,0.2);color:#f87171;border:1px solid rgba(239,68,68,0.4);padding:3px 10px;border-radius:12px;font-size:0.65rem;font-family:'Space Mono',monospace;}
.badge-high{background:rgba(245,158,11,0.2);color:#fbbf24;border:1px solid rgba(245,158,11,0.4);padding:3px 10px;border-radius:12px;font-size:0.65rem;font-family:'Space Mono',monospace;}
.badge-medium{background:rgba(56,189,248,0.15);color:#38bdf8;border:1px solid rgba(56,189,248,0.3);padding:3px 10px;border-radius:12px;font-size:0.65rem;font-family:'Space Mono',monospace;}
.badge-open{background:rgba(239,68,68,0.15);color:#f87171;border:1px solid rgba(239,68,68,0.3);padding:3px 8px;border-radius:8px;font-size:0.6rem;font-family:'Space Mono',monospace;}
.badge-investigating{background:rgba(251,191,36,0.15);color:#fbbf24;border:1px solid rgba(251,191,36,0.3);padding:3px 8px;border-radius:8px;font-size:0.6rem;font-family:'Space Mono',monospace;}
.badge-resolved{background:rgba(34,197,94,0.15);color:#4ade80;border:1px solid rgba(34,197,94,0.3);padding:3px 8px;border-radius:8px;font-size:0.6rem;font-family:'Space Mono',monospace;}
.badge-dismissed{background:rgba(100,116,139,0.15);color:#64748b;border:1px solid rgba(100,116,139,0.3);padding:3px 8px;border-radius:8px;font-size:0.6rem;font-family:'Space Mono',monospace;}
.stButton>button{background:linear-gradient(135deg,#0369a1,#0284c7)!important;color:white!important;border:none!important;border-radius:8px!important;font-family:'Space Mono',monospace!important;font-weight:700!important;}
.pagination-container{background:rgba(13,19,33,0.8);border:1px solid #1e3a5f;border-radius:12px;padding:0.8rem 1.2rem;display:flex;align-items:center;justify-content:space-between;margin:1rem 0;}
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
    page = st.radio("nav",
        ["🔍 Manual Prediction", "📂 CSV Upload", "📊 Dashboard", "📈 Performance", "🚨 Alerts", "🌐 Threat Intel & Cases"],
        index=4, label_visibility="collapsed")
    st.markdown("---")
    if st.button("🔄 Refresh", use_container_width=True): st.rerun()
    if st.button("🗑️ Clear All Alerts", use_container_width=True, type="secondary"):
        st.session_state['confirm_clear'] = True
    auth.show_user_profile()

if page == "🔍 Manual Prediction": st.switch_page("pages/1_manual_input.py")
elif page == "📂 CSV Upload"      : st.switch_page("pages/2_csv_upload.py")
elif page == "📊 Dashboard"       : st.switch_page("pages/3_dashboard.py")
elif page == "📈 Performance"     : st.switch_page("pages/4_performance.py")
elif page == "🌐 Threat Intel & Cases": st.switch_page("pages/6_threat_intel.py")

# ── Page Header ───────────────────────────────────────────────────
stats = get_alert_stats()

open_count_str = str(stats['open'])
now_str        = datetime.now().strftime('%Y-%m-%d  %H:%M')

st.markdown(
    '<div style="background:linear-gradient(135deg,#0d1321,#1a0a0a,#0d1321);'
    'border:1px solid #3a1e1e;border-radius:14px;padding:1.5rem 2rem;margin-bottom:1.5rem;">'
    '<div style="display:flex;justify-content:space-between;align-items:center;">'
    '<div>'
    '<p style="font-family:\'Space Mono\',monospace;font-size:1.5rem;font-weight:700;color:#f0f9ff;margin:0;">'
    '🚨 ALERT MANAGEMENT'
    '</p>'
    '<p style="color:#64748b;font-size:0.82rem;margin-top:0.3rem;">'
    'Fraud alert tracking · Batch SQL Pagination · Investigation workflow'
    '</p>'
    '</div>'
    '<div style="text-align:right;">'
    '<span style="background:rgba(239,68,68,0.15);color:#f87171;'
    'border:1px solid rgba(239,68,68,0.3);font-family:\'Space Mono\',monospace;'
    'font-size:0.65rem;padding:4px 12px;border-radius:20px;">'
    '🔴 ' + open_count_str + ' OPEN ALERTS'
    '</span>'
    '<div style="font-size:0.65rem;color:#475569;margin-top:0.4rem;">' + now_str + '</div>'
    '</div>'
    '</div>'
    '</div>',
    unsafe_allow_html=True
)

# ── Clear All Confirmation ───────────────────────────────────────
if st.session_state.get('confirm_clear'):
    st.warning("⚠️ Are you sure you want to delete ALL alerts? This cannot be undone.")
    cc1, cc2, cc3 = st.columns([1, 1, 4])
    with cc1:
        if st.button("✅ Yes, Clear All", type="primary", use_container_width=True):
            clear_all_alerts()
            st.session_state['confirm_clear'] = False
            st.success("🗑️ All alerts cleared!")
            st.rerun()
    with cc2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state['confirm_clear'] = False
            st.rerun()

# ═══════════════════════════════════════════════════════════════════
# SECTION 1 — SUMMARY METRICS
# ═══════════════════════════════════════════════════════════════════
st.markdown('<p class="section-label">Alert Overview</p>', unsafe_allow_html=True)

c1,c2,c3,c4,c5,c6 = st.columns(6)
for col, val, label, color in [
    (c1, stats['total'],        'Total Alerts',  '#f0f9ff'),
    (c2, stats['open'],         'Open',          '#f87171'),
    (c3, stats['investigating'],'Investigating', '#fbbf24'),
    (c4, stats['resolved'],     'Resolved',      '#4ade80'),
    (c5, stats['critical'],     'Critical',      '#ef4444'),
    (c6, stats['high'],         'High Priority', '#f59e0b'),
]:
    col.markdown(
        '<div class="metric-card">'
        '<div class="metric-value" style="color:' + color + ';">' + str(val) + '</div>'
        '<div class="metric-label">' + label + '</div>'
        '</div>',
        unsafe_allow_html=True
    )

# ═══════════════════════════════════════════════════════════════════
# SECTION 2 — CHARTS
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
ch1, ch2 = st.columns(2)

with ch1:
    st.markdown('<p class="section-label">Alerts by Priority</p>', unsafe_allow_html=True)
    fig_pri = go.Figure(go.Bar(
        x=["CRITICAL", "HIGH", "MEDIUM"],
        y=[stats['critical'], stats['high'], stats['medium']],
        marker_color=["#ef4444", "#f59e0b", "#38bdf8"],
        text=[stats['critical'], stats['high'], stats['medium']],
        textposition="outside",
        textfont=dict(color="#94a3b8", family="Space Mono"),
    ))
    fig_pri.update_layout(
        height=260, paper_bgcolor="#0d1321", plot_bgcolor="#0d1321",
        xaxis=dict(tickfont=dict(color="#94a3b8")),
        yaxis=dict(tickfont=dict(color="#94a3b8"), gridcolor="#1e2d45"),
        showlegend=False, margin=dict(t=20,b=20,l=20,r=20)
    )
    st.plotly_chart(fig_pri, use_container_width=True, config={"displayModeBar":False})

with ch2:
    st.markdown('<p class="section-label">Alerts by Status</p>', unsafe_allow_html=True)
    fig_status = go.Figure(go.Pie(
        values=[stats['open'], stats['investigating'], stats['resolved'], stats['dismissed']],
        labels=["Open", "Investigating", "Resolved", "Dismissed"],
        hole=0.55,
        marker_colors=["#ef4444", "#f59e0b", "#4ade80", "#475569"],
        textinfo="percent+label",
        textfont=dict(size=11),
    ))
    fig_status.update_layout(
        height=260, paper_bgcolor="#0d1321",
        showlegend=False, margin=dict(t=20,b=20,l=20,r=20)
    )
    st.plotly_chart(fig_status, use_container_width=True, config={"displayModeBar":False})

# ═══════════════════════════════════════════════════════════════════
# SECTION 3 — ADD NEW ALERT MANUALLY
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
with st.expander("➕ Add New Alert Manually"):
    with st.form("add_alert_form"):
        st.markdown('<p class="section-label">New Alert Details</p>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            new_txn_id  = st.text_input("Transaction ID", placeholder="TXN-123456")
            new_amount  = st.number_input("Amount ($)", min_value=0.0, value=100000.0, step=1000.0)
        with col2:
            new_type    = st.selectbox("Transaction Type", ["TRANSFER","CASH_OUT","PAYMENT","DEBIT","CASH_IN"])
            new_prob    = st.slider("Fraud Probability", 0.0, 1.0, 0.85, 0.01)
        with col3:
            new_priority = st.selectbox("Priority", ["CRITICAL","HIGH","MEDIUM"])
            new_ob      = st.number_input("Original Balance ($)", min_value=0.0, value=100000.0)

        submitted = st.form_submit_button("🚨 Create Alert", use_container_width=True, type="primary")
        if submitted:
            risk = "HIGH" if new_prob >= 0.80 else ("MEDIUM" if new_prob >= 0.40 else "LOW")
            add_alert({
                "transaction_id": new_txn_id or f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "amount"        : new_amount,
                "tx_type"       : new_type,
                "fraud_prob"    : new_prob,
                "risk_level"    : risk,
                "priority"      : new_priority,
                "old_balance"   : new_ob,
                "new_balance"   : 0.0,
            })
            st.success("✅ Alert created successfully!")
            st.rerun()

# ═══════════════════════════════════════════════════════════════════
# SECTION 4 — ALERT QUEUE WITH SQL PAGINATION & FILTERS
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<p class="section-label">Alert Queue & Investigation Batch</p>', unsafe_allow_html=True)

# Filters & Controls
f1, f2, f3, f4, f5 = st.columns([1.2, 1.2, 1.2, 1.4, 1.0])
with f1: filter_priority = st.selectbox("Priority", ["ALL","CRITICAL","HIGH","MEDIUM"])
with f2: filter_status   = st.selectbox("Status",   ["ALL","OPEN","INVESTIGATING","RESOLVED","DISMISSED"])
with f3: filter_type     = st.selectbox("Type",     ["ALL","TRANSFER","CASH_OUT","PAYMENT","DEBIT","CASH_IN"])
with f4: sort_by         = st.selectbox("Sort By",  ["Newest First","Highest Amount","Highest Probability"])
with f5: page_size       = st.selectbox("Per Page", [10, 25, 50, 100], index=0)

# Initialize Pagination State
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1

# Reset page to 1 when filters change
filter_key = f"{filter_priority}_{filter_status}_{filter_type}_{sort_by}_{page_size}"
if st.session_state.get('prev_filter_key') != filter_key:
    st.session_state.current_page = 1
    st.session_state.prev_filter_key = filter_key

current_page = st.session_state.current_page
offset = (current_page - 1) * page_size

# Efficient Paginated SQL Query
df_alerts, total_filtered = get_filtered_alerts_paginated(
    filter_priority, filter_status, filter_type, sort_by, limit=page_size, offset=offset
)

total_pages = max(int(np.ceil(total_filtered / page_size)), 1)
if current_page > total_pages:
    st.session_state.current_page = total_pages
    current_page = total_pages

# Top Pagination Bar
p_col1, p_col2, p_col3 = st.columns([2, 3, 2])
with p_col1:
    st.markdown(f"Showing **{len(df_alerts)}** of **{total_filtered:,}** matching alerts")

with p_col2:
    btn_prev, btn_page, btn_next = st.columns([1, 2, 1])
    with btn_prev:
        if st.button("◀ Prev", disabled=(current_page <= 1), use_container_width=True):
            st.session_state.current_page -= 1
            st.rerun()
    with btn_page:
        st.markdown(f"<div style='text-align:center;font-family:Space Mono;padding-top:6px;'>Page <strong>{current_page}</strong> / {total_pages}</div>", unsafe_allow_html=True)
    with btn_next:
        if st.button("Next ▶", disabled=(current_page >= total_pages), use_container_width=True):
            st.session_state.current_page += 1
            st.rerun()

st.markdown("<div style='margin-bottom:0.5rem;'></div>", unsafe_allow_html=True)

if not df_alerts.empty:
    for _, alert in df_alerts.iterrows():
        priority = str(alert['priority'])
        status   = str(alert['status'])
        card_cls = "alert-card-" + priority.lower()
        pri_cls  = "badge-" + priority.lower()
        sts_cls  = "badge-" + status.lower().replace(' ','')

        pri_icon = "🔴" if priority=="CRITICAL" else ("🟠" if priority=="HIGH" else "🔵")
        sts_icon = "🔓" if status=="OPEN" else ("🔍" if status=="INVESTIGATING" else ("✅" if status=="RESOLVED" else "🚫"))

        txn_id_str   = str(alert['transaction_id']) if alert['transaction_id'] else f"ALERT-{alert['id']}"
        tx_type_str  = str(alert['tx_type'])
        amount_str   = f"${float(alert['amount']):,.0f}"
        prob_str     = f"{float(alert['fraud_prob']):.2%}"
        time_str     = str(alert['created_at'])[:16].replace('T', ' ')
        assigned_str = str(alert['assigned_to']) if alert['assigned_to'] and str(alert['assigned_to']) not in ('None','nan','') else 'Unassigned'

        notes_val  = str(alert['notes']) if alert['notes'] else ''
        has_notes  = notes_val.strip() not in ('', 'None', 'nan')
        notes_html = ('<span>📝 ' + notes_val[:40] + '</span>') if has_notes else ''

        with st.container():
            st.markdown(
                '<div class="' + card_cls + '">'
                '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.6rem;">'
                '<div style="display:flex;align-items:center;gap:0.8rem;">'
                '<span style="font-size:1.4rem;">' + pri_icon + '</span>'
                '<div>'
                '<span style="font-family:\'Space Mono\',monospace;font-size:0.85rem;font-weight:700;color:#f0f9ff;">'
                + txn_id_str +
                '</span>'
                '<span style="margin-left:0.5rem;font-size:0.72rem;color:#64748b;">'
                + tx_type_str + ' · ' + amount_str +
                '</span>'
                '</div>'
                '</div>'
                '<div style="display:flex;gap:0.5rem;align-items:center;">'
                '<span class="' + pri_cls + '">' + priority + '</span>'
                '<span class="' + sts_cls + '">' + sts_icon + ' ' + status + '</span>'
                '</div>'
                '</div>'
                '<div style="display:flex;gap:2rem;font-size:0.75rem;color:#64748b;">'
                '<span>🎯 Fraud Prob: <strong style="color:#f87171;">' + prob_str + '</strong></span>'
                '<span>⏰ ' + time_str + '</span>'
                '<span>👤 ' + assigned_str + '</span>'
                + notes_html +
                '</div>'
                '</div>',
                unsafe_allow_html=True
            )

            if status not in ("RESOLVED", "DISMISSED"):
                btn1, btn2, btn3, btn4, _ = st.columns([1,1,1,1.5,2.5])
                with btn1:
                    if st.button("🔍 Investigate", key=f"inv_{alert['id']}", use_container_width=True):
                        assign_alert(alert['id'], st.session_state.username)
                        st.success(f"✅ Assigned to {st.session_state.username}")
                        st.rerun()
                with btn2:
                    if st.button("✅ Resolve", key=f"res_{alert['id']}", use_container_width=True):
                        update_alert_status(alert['id'], "RESOLVED", st.session_state.username, "Confirmed fraud - resolved")
                        st.success("✅ Alert resolved!")
                        st.rerun()
                with btn3:
                    if st.button("🚫 Dismiss", key=f"dis_{alert['id']}", use_container_width=True):
                        update_alert_status(alert['id'], "DISMISSED", st.session_state.username, "False positive - dismissed")
                        st.warning("Alert dismissed.")
                        st.rerun()
                with btn4:
                    note = st.text_input("Add note", key=f"note_{alert['id']}", placeholder="Type note...", label_visibility="collapsed")
                    if note:
                        update_alert_status(alert['id'], status, st.session_state.username, note)
                        st.rerun()

            st.markdown("<div style='margin-bottom:0.3rem;'></div>", unsafe_allow_html=True)

    # Bottom Pagination Controls
    b_col1, b_col2, b_col3 = st.columns([2, 3, 2])
    with b_col2:
        b_prev, b_page, b_next = st.columns([1, 2, 1])
        with b_prev:
            if st.button("◀ Prev Page", key="b_prev", disabled=(current_page <= 1), use_container_width=True):
                st.session_state.current_page -= 1
                st.rerun()
        with b_page:
            st.markdown(f"<div style='text-align:center;font-family:Space Mono;padding-top:6px;'>Page <strong>{current_page}</strong> of {total_pages}</div>", unsafe_allow_html=True)
        with b_next:
            if st.button("Next Page ▶", key="b_next", disabled=(current_page >= total_pages), use_container_width=True):
                st.session_state.current_page += 1
                st.rerun()

else:
    st.info("✅ No alerts found matching your filters.")


# ═══════════════════════════════════════════════════════════════════
# SECTION 5 — IMPORT ALERTS FROM CSV SCAN
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<p class="section-label">Import Alerts from CSV Scan Results</p>', unsafe_allow_html=True)

# ── Tab 1: Upload file  |  Tab 2: Load from local folder ─────────
tab1, tab2 = st.tabs(["📤 Upload CSV File", "📁 Load from Local Folder"])

with tab2:
    st.markdown("**Automatically find result files saved on your computer**")
    st.markdown("Looks for `fraudguard_fraud_only_*.csv` or `fraudguard_results_*.csv` in your project folder.")

    import glob, os
    # Search common locations
    search_paths = [
        "fraudguard_fraud_only_*.csv",
        "fraudguard_results_*.csv",
        "results/*.csv",
        "output/*.csv",
    ]
    found_files = []
    for pattern in search_paths:
        found_files.extend(glob.glob(pattern))

    if found_files:
        selected_file = st.selectbox("Select results file:", found_files)
        file_size_mb  = os.path.getsize(selected_file) / (1024*1024)
        st.info(f"📦 File: `{selected_file}` — {file_size_mb:.1f} MB")

        if st.button("🔍 Preview & Count Fraud Rows", use_container_width=True):
            import io, gc
            DTYPE_RES  = {'amount':'float32','oldbalanceOrg':'float32',
                          'newbalanceOrig':'float32','fraud_probability':'float32'}
            fraud_total = 0
            has_col     = False
            for chunk in pd.read_csv(selected_file, chunksize=100_000, low_memory=False, dtype=DTYPE_RES):
                if 'is_fraud' in chunk.columns:
                    has_col = True
                    fraud_total += int(chunk['is_fraud'].sum())
                gc.collect()
            if has_col:
                st.success(f"✅ Found **{fraud_total:,}** fraud transactions")
                st.session_state['local_file']       = selected_file
                st.session_state['local_fraud_count'] = fraud_total
            else:
                st.error("❌ File missing 'is_fraud' column")

        if st.session_state.get('local_file') and st.session_state.get('local_fraud_count', 0) > 0:
            fraud_total = st.session_state['local_fraud_count']
            if st.button(f"🚨 Create {fraud_total:,} Alerts from Local File", type="primary", use_container_width=True):
                import gc
                created  = 0
                prog_bar = st.progress(0, text="Importing alerts...")
                DTYPE_RES = {'amount':'float32','oldbalanceOrg':'float32',
                             'newbalanceOrig':'float32','fraud_probability':'float32'}
                for chunk in pd.read_csv(st.session_state['local_file'], chunksize=100_000,
                                          low_memory=False, dtype=DTYPE_RES):
                    fraud_chunk = chunk[chunk['is_fraud'] == True]
                    for _, row in fraud_chunk.iterrows():
                        prob     = float(row.get('fraud_probability', 0.5))
                        amt      = float(row.get('amount', 0))
                        priority = "CRITICAL" if prob >= 0.90 else ("HIGH" if prob >= 0.70 else "MEDIUM")
                        add_alert({
                            "transaction_id": f"CSV-{created+1:04d}",
                            "amount"        : amt,
                            "tx_type"       : str(row.get('type', 'UNKNOWN')),
                            "fraud_prob"    : prob,
                            "risk_level"    : str(row.get('risk_level', 'HIGH')),
                            "priority"      : priority,
                            "old_balance"   : float(row.get('oldbalanceOrg', 0)),
                            "new_balance"   : float(row.get('newbalanceOrig', 0)),
                        })
                        created += 1
                    prog = min(created / max(fraud_total, 1), 0.99)
                    prog_bar.progress(prog, text=f"Imported {created:,} / {fraud_total:,}...")
                    del chunk, fraud_chunk; gc.collect()
                prog_bar.progress(1.0, text="Done!")
                st.success(f"✅ Created {created:,} alerts!")
                st.session_state.pop('local_file', None)
                st.session_state.pop('local_fraud_count', None)
                st.rerun()
    else:
        st.warning("⚠️ No result CSV files found in project folder.")
        st.info("Run a scan from CSV Upload page first, then download **Fraud Rows Only** CSV.")

with tab1:
    st.markdown(
        '<div style="background:rgba(56,189,248,0.05);border:1px solid rgba(56,189,248,0.15);'
        'border-radius:8px;padding:1rem;font-size:0.8rem;color:#94a3b8;margin-bottom:1rem;">'
        '💡 Upload the <strong>Fraud Rows Only</strong> CSV (small file ~1-2MB) downloaded from CSV Upload page. '
        'Do NOT upload the full 600MB results file.'
        '</div>',
        unsafe_allow_html=True
    )

uploaded_results = st.file_uploader("Upload fraudguard_fraud_only_*.csv", type=["csv"],
                                     key="results_upload", label_visibility="collapsed")
if uploaded_results:
    import io, gc

    raw_bytes     = uploaded_results.read()
    file_size_mb  = len(raw_bytes) / (1024 * 1024)
    st.info(f"📦 File size: {file_size_mb:.1f} MB — using chunked reading to save RAM...")

    # ── Count fraud rows without loading full file into RAM ───────
    DTYPE_RES = {
        'amount'         : 'float32',
        'oldbalanceOrg'  : 'float32',
        'newbalanceOrig' : 'float32',
        'fraud_probability': 'float32',
    }
    CHUNK_SIZE = 100_000

    # First pass — just count fraud rows
    fraud_count_total = 0
    has_col = False
    try:
        for chunk in pd.read_csv(io.BytesIO(raw_bytes), chunksize=CHUNK_SIZE,
                                  low_memory=False, dtype=DTYPE_RES):
            if 'is_fraud' in chunk.columns:
                has_col = True
                fraud_count_total += int(chunk['is_fraud'].sum())
        gc.collect()
    except Exception as e:
        st.error(f"❌ Could not read file: {e}")
        st.stop()

    if not has_col:
        st.error("❌ File must contain 'is_fraud' column. Download results from CSV Upload page first.")
    else:
        st.info(f"Found **{fraud_count_total:,}** fraud transactions in results file.")

        if st.button(f"🚨 Create {fraud_count_total:,} Alerts", type="primary", use_container_width=True):
            created  = 0
            prog_bar = st.progress(0, text="Importing alerts...")

            # Second pass — process chunk by chunk, only fraud rows
            chunk_num = 0
            total_chunks = max(int(file_size_mb / (CHUNK_SIZE * 0.08 / 1024)), 1)

            for chunk in pd.read_csv(io.BytesIO(raw_bytes), chunksize=CHUNK_SIZE,
                                      low_memory=False, dtype=DTYPE_RES):
                chunk_num += 1
                fraud_chunk = chunk[chunk['is_fraud'] == True]

                for _, row in fraud_chunk.iterrows():
                    prob     = float(row.get('fraud_probability', 0.5))
                    amt      = float(row.get('amount', 0))
                    priority = "CRITICAL" if prob >= 0.90 else ("HIGH" if prob >= 0.70 else "MEDIUM")
                    add_alert({
                        "transaction_id": f"CSV-{created+1:04d}",
                        "amount"        : amt,
                        "tx_type"       : str(row.get('type', 'UNKNOWN')),
                        "fraud_prob"    : prob,
                        "risk_level"    : str(row.get('risk_level', 'HIGH')),
                        "priority"      : priority,
                        "old_balance"   : float(row.get('oldbalanceOrg', 0)),
                        "new_balance"   : float(row.get('newbalanceOrig', 0)),
                    })
                    created += 1

                prog_bar.progress(
                    min(chunk_num / max(total_chunks, 1), 0.99),
                    text=f"Processed {created:,} alerts so far..."
                )
                del chunk, fraud_chunk; gc.collect()

            prog_bar.progress(1.0, text="Done!")
            st.success(f"✅ Created {created:,} alerts successfully!")
            st.rerun()

# ── Footer ────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div style="text-align:center;font-size:0.7rem;color:#475569;">FraudGuard AI · Alert Management · '
    + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '</div>',
    unsafe_allow_html=True
)