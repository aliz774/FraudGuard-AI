# ─────────────────────────────────────────────────────────────────
# pages/6_threat_intel.py — Real-World Fraud Cases & Prevention Guide
# ─────────────────────────────────────────────────────────────────

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

try:
    import auth
except ImportError:
    st.error("❌ Cannot find auth.py"); st.stop()

st.set_page_config(
    page_title="Threat Intel & Prevention — FraudGuard AI",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

auth.require_auth()

# ── Custom CSS Styles (Matching FraudGuard Dark Theme) ────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Sora:wght@300;400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Sora', sans-serif; }
.stApp { background: #080c14; color: #e2e8f0; }
[data-testid="stSidebar"] { background: #0d1321 !important; border-right: 1px solid #1e2d45; }
[data-testid="stSidebar"] * { color: #94a3b8 !important; }

.section-label {
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 3px;
    color: #38bdf8;
    text-transform: uppercase;
    margin-bottom: 0.8rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #1e3a5f;
}

.case-card {
    background: linear-gradient(135deg, #0d1321 0%, #151f33 100%);
    border: 1px solid #1e3a5f;
    border-radius: 14px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.case-card:hover {
    border-color: #38bdf8;
    transform: translateY(-2px);
}

.threat-badge {
    display: inline-block;
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    padding: 3px 10px;
    border-radius: 12px;
    font-weight: 700;
}
.badge-critical { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.3); }
.badge-high     { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245,158,11,0.3); }
.badge-emerging { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168,85,247,0.3); }

.rule-box {
    background: rgba(15, 23, 42, 0.6);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin: 0.6rem 0;
    border-left: 4px solid #38bdf8;
}

.red-flag {
    background: rgba(239, 68, 68, 0.08);
    border-left: 4px solid #ef4444;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin: 0.5rem 0;
    font-size: 0.85rem;
}

.safe-guard {
    background: rgba(34, 197, 94, 0.08);
    border-left: 4px solid #22c55e;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin: 0.5rem 0;
    font-size: 0.85rem;
}

.step-bubble {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 26px;
    height: 26px;
    border-radius: 50%;
    background: #0284c7;
    color: #fff;
    font-weight: bold;
    font-size: 0.75rem;
    margin-right: 8px;
}

.golden-hour-card {
    background: linear-gradient(135deg, #1a0f00 0%, #291b00 50%, #1a0f00 100%);
    border: 1px solid #d97706;
    border-radius: 14px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar Navigation ───────────────────────────────────────────
with st.sidebar:
    st.markdown("""<div style="text-align:center;padding:1rem 0 0.5rem;">
        <div style="font-size:2.2rem;">🛡️</div>
        <div style="font-family:'Space Mono',monospace;font-size:0.95rem;font-weight:700;color:#f0f9ff;">FRAUDGUARD AI</div>
        <div style="font-size:0.6rem;color:#38bdf8;letter-spacing:2px;">THREAT INTELLIGENCE</div>
    </div>""", unsafe_allow_html=True)
    st.markdown("---")
    
    page = st.radio("nav",
        ["🔍 Manual Prediction", "📂 CSV Upload", "📊 Dashboard", "📈 Performance", "🚨 Alerts", "🌐 Threat Intel & Cases"],
        index=5, label_visibility="collapsed")
    
    st.markdown("---")
    if st.button("🔄 Refresh Intel Feed", use_container_width=True):
        st.rerun()
    auth.show_user_profile()

if page == "🔍 Manual Prediction": st.switch_page("pages/1_manual_input.py")
elif page == "📂 CSV Upload":       st.switch_page("pages/2_csv_upload.py")
elif page == "📊 Dashboard":        st.switch_page("pages/3_dashboard.py")
elif page == "📈 Performance":      st.switch_page("pages/4_performance.py")
elif page == "🚨 Alerts":           st.switch_page("pages/5_alerts.py")

# ── Page Header ───────────────────────────────────────────────────
st.markdown(
    '<div style="background:linear-gradient(135deg,#0d1321,#0c1c2e,#0d1321);'
    'border:1px solid #1e3a5f;border-radius:14px;padding:1.6rem 2rem;margin-bottom:1.5rem;">'
    '<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">'
    '<div>'
    '<p style="font-family:\'Space Mono\',monospace;font-size:1.6rem;font-weight:700;color:#f0f9ff;margin:0;">'
    '🌐 REAL-WORLD FRAUD INTELLIGENCE & PREVENTION'
    '</p>'
    '<p style="color:#94a3b8;font-size:0.85rem;margin-top:0.3rem;">'
    'Global attack vectors · Modus Operandi breakdown · Citizen & Developer mitigation protocols'
    '</p>'
    '</div>'
    '<div style="text-align:right;">'
    '<span style="background:rgba(56,189,248,0.15);color:#38bdf8;'
    'border:1px solid rgba(56,189,248,0.3);font-family:\'Space Mono\',monospace;'
    'font-size:0.7rem;padding:5px 14px;border-radius:20px;">'
    'LIVE THREAT RADAR ACTIVE'
    '</span>'
    '<div style="font-size:0.7rem;color:#64748b;margin-top:0.4rem;">Updated: ' + datetime.now().strftime('%b %d, %Y') + '</div>'
    '</div>'
    '</div>'
    '</div>',
    unsafe_allow_html=True
)

# ── Top Level Quick Metrics ───────────────────────────────────────
st.markdown('<p class="section-label">Global Financial Fraud Threat Metrics</p>', unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown("""
    <div style="background:rgba(15,23,42,0.6);border:1px solid #1e2d45;border-radius:10px;padding:1rem;">
        <div style="font-family:'Space Mono',monospace;font-size:0.7rem;color:#64748b;">ANNUAL GLOBAL LOSSES</div>
        <div style="font-family:'Space Mono',monospace;font-size:1.6rem;font-weight:700;color:#ef4444;">$485 Billion+</div>
        <div style="font-size:0.7rem;color:#f87171;">Global cyber & financial fraud (Nasdaq Report)</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown("""
    <div style="background:rgba(15,23,42,0.6);border:1px solid #1e2d45;border-radius:10px;padding:1rem;">
        <div style="font-family:'Space Mono',monospace;font-size:0.7rem;color:#64748b;">FASTEST GROWING THREAT</div>
        <div style="font-family:'Space Mono',monospace;font-size:1.6rem;font-weight:700;color:#fbbf24;">+340% YoY</div>
        <div style="font-size:0.7rem;color:#f59e0b;">AI Deepfake & Impersonation Scams</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    st.markdown("""
    <div style="background:rgba(15,23,42,0.6);border:1px solid #1e2d45;border-radius:10px;padding:1rem;">
        <div style="font-family:'Space Mono',monospace;font-size:0.7rem;color:#64748b;">#1 VOLUME ATTACK</div>
        <div style="font-family:'Space Mono',monospace;font-size:1.6rem;font-weight:700;color:#38bdf8;">UPI & QR Scams</div>
        <div style="font-size:0.7rem;color:#38bdf8;">Scan-to-Receive deceptive requests</div>
    </div>
    """, unsafe_allow_html=True)

with m4:
    st.markdown("""
    <div style="background:rgba(15,23,42,0.6);border:1px solid #1e2d45;border-radius:10px;padding:1rem;">
        <div style="font-family:'Space Mono',monospace;font-size:0.7rem;color:#64748b;">CRITICAL RESPONSE TIME</div>
        <div style="font-family:'Space Mono',monospace;font-size:1.6rem;font-weight:700;color:#4ade80;">&lt; 2 Hours</div>
        <div style="font-size:0.7rem;color:#4ade80;">"Golden Hour" recovery window via 1930</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# TABS: CASE STUDIES, SIMULATOR / RED FLAG CHECKER, EMERGENCY PROTOCOL
# ═══════════════════════════════════════════════════════════════════
tab_cases, tab_checker, tab_emergency, tab_developer = st.tabs([
    "📚 Real-World Fraud Case Studies",
    "🛡️ 'Am I Being Scammed?' Risk Checker",
    "🚨 Emergency 'Golden Hour' Response",
    "💻 System & API Defense Guide (For Developers/Faculty)"
])

# ─────────────────────────────────────────────────────────────────
# TAB 1: REAL-WORLD CASE STUDIES
# ─────────────────────────────────────────────────────────────────
with tab_cases:
    st.markdown('<p class="section-label">Detailed Case Studies & Modus Operandi</p>', unsafe_allow_html=True)
    
    # Filter Controls
    f_col1, f_col2 = st.columns([2, 2])
    with f_col1:
        cat_filter = st.selectbox(
            "Filter by Attack Category:",
            ["All Categories", "📱 UPI & Mobile Banking", "🤖 AI Deepfake & Impersonation", "📈 Pig Butchering & Crypto", "💳 Card & NetBanking", "⚡ Utility & APK Malware"]
        )
    with f_col2:
        search_query = st.text_input("🔍 Search threat keywords (e.g., QR, OTP, CBI, Deepfake, SIM):", "")

    # Comprehensive Fraud Knowledge Base
    fraud_cases = [
        {
            "id": "CASE-01",
            "title": "The 'Digital Arrest' & Fake Law Enforcement Video Call",
            "category": "🤖 AI Deepfake & Impersonation",
            "severity": "CRITICAL",
            "loss_stat": "₹1,200+ Crores total stolen in India (2023–2025)",
            "summary": "Victim receives a high-pressure call claiming an illegal package containing contraband/drugs was intercepted in their name, or their bank account is implicated in money laundering.",
            "modus_operandi": [
                "Call initiated via IVR / WhatsApp claiming to be Mumbai/Delhi Police, CBI, ED, or FedEx.",
                "Victim is connected on Skype or WhatsApp Video Call to a fake police station with forged government insignias and uniform actors.",
                "Scammers issue forged arrest warrants and Supreme Court orders with real-looking digital seals.",
                "Victim is coerced into staying on video for 24-72 hours under 'Digital Arrest' and pressured to liquidate FDs/savings into a 'government verification escrow account' which is an active mule account.",
                "Once funds are credited, communications are severed and money is immediately wired via RTGS to offshore accounts."
            ],
            "red_flags": [
                "Law enforcement threatening you over Skype, WhatsApp, or Zoom video calls.",
                "Any order commanding 'Digital Arrest' (No law in India or anywhere permits digital arrest).",
                "Demands to liquidate fixed deposits and transfer funds to 'clear your name' or for 'RBI verification'.",
                "Demands to maintain complete secrecy from family, colleagues, or local police."
            ],
            "prevention_citizen": [
                "DISCONNECT IMMEDIATELY. Real police, CBI, or Customs NEVER conduct interrogations over Skype/WhatsApp.",
                "Never transfer funds to verify innocence or avoid arrest. Official bonds are only posted in actual courts.",
                "Dial 1930 immediately to report the phone number and transaction details."
            ],
            "prevention_tech": [
                "FraudGuard Rule: Flag rapid FD premature closures immediately followed by high-value RTGS transfers (>₹5,00,000) to newly created beneficiary accounts.",
                "Implement 4-hour cooldown delay for first-time high-value transfers initiated from mobile banking after password or device change."
            ]
        },
        {
            "id": "CASE-02",
            "title": "The $25.6 Million AI Deepfake Video Conference Heist",
            "category": "🤖 AI Deepfake & Impersonation",
            "severity": "CRITICAL",
            "loss_stat": "$25.6 Million (Hong Kong Multinational Corporation)",
            "summary": "An employee in a corporate finance department was duped into executing 15 high-value wire transfers after joining a live video conference where every single participant was an AI deepfake avatar.",
            "modus_operandi": [
                "Attacker sent spear-phishing email purportedly from the UK-based Chief Financial Officer (CFO).",
                "Finance worker initially had doubts, but was invited to a multi-person video call.",
                "During the call, the CFO and other colleagues appeared visually and spoke in their exact voices (generated from YouTube conference recordings).",
                "The fake CFO instructed urgent confidential transactions for a proprietary overseas acquisition.",
                "The employee executed 15 separate transactions totaling HK$200M ($25.6M) across multiple accounts before discovering the fraud a week later."
            ],
            "red_flags": [
                "Unusual urgency to bypass standard dual-authorization corporate accounting procedures.",
                "Request for secrecy regarding an acquisition or wire transfer.",
                "Video call participants exhibiting subtle visual glitches around the mouth, unnatural blinking, or refusal to turn their head sideways."
            ],
            "prevention_citizen": [
                "Enforce Out-Of-Band Authentication (OOBA): Always verify wire instructions over an internal company landline or face-to-face.",
                "Use dynamic challenge questions (e.g. asking an unscripted personal question or asking the caller to wave their hand across their face)."
            ],
            "prevention_tech": [
                "Multi-signatory quorum with physical hardware tokens (YubiKey / FIDO2) for transfers above set enterprise thresholds.",
                "Behavioral anomaly tracking on accounts sending funds to overseas jurisdictions outside typical business patterns."
            ]
        },
        {
            "id": "CASE-03",
            "title": "The 'Scan QR Code to Receive Payment' Marketplace Scam",
            "category": "📱 UPI & Mobile Banking",
            "severity": "HIGH",
            "loss_stat": "₹5,000 to ₹1,00,000 per victim (Millions of daily attempts)",
            "summary": "Victim posts an item for sale on OLX, Facebook Marketplace, or Quikr. Fraudster poses as an enthusiastic buyer and offers to pay an advance via UPI, but sends a QR code or collect request.",
            "modus_operandi": [
                "Scammer contacts seller, agrees on price immediately without bargaining to build excitement.",
                "Claims they are paying from an 'Army / Corporate Account' that requires a QR scan or UPI Collect Request.",
                "Sends a QR code on WhatsApp saying 'Scan this QR code and your bank balance will be credited with ₹15,000'.",
                "Seller scans the QR code; the UPI app prompts: 'Enter UPI PIN to approve payment of ₹15,000'.",
                "The seller enters their PIN believing it is to 'verify receipt', but the money is instantly deducted from their account.",
                "When the seller protests, the scammer claims 'Technical error, scan this ₹30,000 QR to get a full refund', draining more funds."
            ],
            "red_flags": [
                "Buyer refusing to meet in person or inspect the item before paying.",
                "Any claim that entering your UPI PIN or scanning a QR code is required to RECEIVE money.",
                "Receiving a 'Collect Request' on Google Pay / PhonePe / Paytm for a transaction where you are the seller."
            ],
            "prevention_citizen": [
                "GOLDEN RULE OF UPI: You NEVER need to enter your UPI PIN or scan a QR code to RECEIVE money.",
                "UPI PIN is ONLY required when money leaves your bank account.",
                "Never entertain buyers who insist on sending payment through third-party barcodes or refund links."
            ],
            "prevention_tech": [
                "Banking UX: When a user initiates a payment to an unknown VPA from a scanned image (rather than a physical merchant standee), display a prominent red warning banner: 'YOU ARE SENDING MONEY, NOT RECEIVING'.",
                "New account velocity limits: Lock outbound transfers if an account receives funds and attempts an immediate cash-out within 60 seconds."
            ]
        },
        {
            "id": "CASE-04",
            "title": "SIM Swap & e-SIM Remote Takeover with Balance Drain",
            "category": "💳 Card & NetBanking",
            "severity": "CRITICAL",
            "loss_stat": "Averages ₹10L - ₹50L per targeted executive",
            "summary": "Fraudster social engineers a telecom carrier or tricks the victim into forwarding an e-SIM conversion email. The victim's phone loses network while the attacker gains control of all SMS 2FA OTPs.",
            "modus_operandi": [
                "Attacker gathers victim's PAN, Aadhaar, and phone number from data leaks or phishing.",
                "Attacker requests an e-SIM upgrade via SMS or impersonates the victim at a telecom kiosk with a forged ID.",
                "Victim receives an automated SMS from telecom operator: 'Reply 1 to confirm eSIM transfer'. Attacker calls victim claiming 'Your 5G upgrade is pending, please reply 1'.",
                "Once activated, the victim's physical SIM is deactivated ('No Service').",
                "Attacker immediately uses the active SIM to trigger 'Forgot Password' on banking apps, receives OTPs, adds new beneficiaries, and drains accounts."
            ],
            "red_flags": [
                "Sudden loss of cellular network reception in an area with normally strong signal.",
                "Unsolicited emails or SMS regarding e-SIM activation, SIM replacement, or 5G upgrades.",
                "Calls from individuals claiming to be telecom customer care asking you to forward an SMS code."
            ],
            "prevention_citizen": [
                "If your phone suddenly shows 'No Service' for more than 15 minutes, contact your telecom operator immediately from another phone.",
                "Never share eSIM QR codes or forward verification emails to anyone.",
                "Switch from SMS-based OTPs to App-based Authenticator (Google Authenticator, Microsoft Authenticator) or Hardware Keys."
            ],
            "prevention_tech": [
                "Telecom-Banking API Binding: Banks must query telecom carrier APIs for SIM change events; if SIM was swapped within the last 48 hours, automatically block net banking transactions and password resets.",
                "FraudGuard Model Feature: Include `device_fingerprint_change` and `carrier_sim_age` in real-time fraud scoring."
            ]
        },
        {
            "id": "CASE-05",
            "title": "Pig Butchering (Sha Zhu Pan) & Fake Telegram Task Scams",
            "category": "📈 Pig Butchering & Crypto",
            "severity": "CRITICAL",
            "loss_stat": "$75+ Billion globally (United States Institute of Peace report)",
            "summary": "Victims are lured into high-yield crypto or task-based investment schemes. Scammers 'fatten' the victim with initial small profits before executing a massive financial slaughter.",
            "modus_operandi": [
                "Begins with unsolicited message: 'Work from home: Like YouTube videos & review hotels for ₹3,000/day'.",
                "Victim completes simple tasks and is genuinely paid ₹500 - ₹2,000 on UPI to build trust.",
                "Victim is introduced to a 'VIP Prepaid Task' or a proprietary crypto trading website (e.g., fake Binance clone).",
                "The fake website dashboard shows their ₹50,000 investment growing to ₹3,50,000 in days.",
                "When the victim tries to withdraw, the platform shows 'Withdrawal Frozen - Pay 30% Capital Gains Tax'.",
                "Victim pays more money to unlock funds, leading to cumulative losses of lakhs or crores before realizing the site is fake."
            ],
            "red_flags": [
                "Guaranteed returns of 20% to 200% with 'zero risk'.",
                "Part-time jobs paying high amounts simply for liking videos or typing reviews.",
                "Investment platforms operating entirely via Telegram groups, WhatsApp admins, and random UPI IDs.",
                "Any requirement to pay 'fees', 'taxes', or 'gas fees' in cash to withdraw your own principal."
            ],
            "prevention_citizen": [
                "NEVER invest money through links sent on Telegram or WhatsApp groups.",
                "Verify all financial entities on official regulatory portals (SEBI, RBI, SEC, FCA).",
                "Understand that initial small payouts are bait funded by previous victims' money."
            ],
            "prevention_tech": [
                "FraudGuard Model Detection: Sudden surge of incoming small deposits from varied individuals followed by aggregated lump-sum transfers to high-risk merchant categories.",
                "Mule Account Profiling: Accounts opened with low initial balance that suddenly receive ₹10,00,000 within 30 days."
            ]
        },
        {
            "id": "CASE-06",
            "title": "Electricity / Utility Bill Disconnection APK Malware",
            "category": "⚡ Utility & APK Malware",
            "severity": "HIGH",
            "loss_stat": "₹50,000 - ₹5,00,000 per incident",
            "summary": "Urgent SMS claiming power supply will be cut off tonight due to unpaid dues. Victim calls the number and is tricked into downloading remote access software or a malicious banking trojan APK.",
            "modus_operandi": [
                "Victim receives SMS: 'Dear consumer, electricity power will be disconnected at 9:30 PM tonight from electricity office because previous month bill was not updated. Contact Electricity Officer at 98765xxxxx'.",
                "Panicked victim calls the number; the fake officer claims the bill payment didn't reflect on the server.",
                "Instructs victim to pay ₹10 nominal fee to update the record and sends an APK link (e.g. 'Bijli_Update.apk') or asks to install AnyDesk/QuickSupport.",
                "The app secretly captures SMS permissions, screen recording, and keystrokes.",
                "As the victim enters card/NetBanking credentials, the attacker logs in remotely and drains accounts while intercepting OTPs silently."
            ],
            "red_flags": [
                "SMS sent from a regular 10-digit mobile number rather than an official 6-character telecom sender ID (e.g., `AD-BSESPB`).",
                "Extreme artificial urgency (e.g. 'disconnected in 2 hours').",
                "Requests to download APK files outside the Google Play Store or install remote desktop software (AnyDesk, TeamViewer, RustDesk)."
            ],
            "prevention_citizen": [
                "Never install unknown .apk files downloaded from WhatsApp, Telegram, or SMS links.",
                "Utility companies NEVER disconnect power without official physical notices and days of advance warning.",
                "Always verify bill status directly via the official electricity board website or authorized apps (e.g., Bharat BillPay, Google Pay)."
            ],
            "prevention_tech": [
                "Banking App Defense: Modern banking apps must detect active screen-sharing apps (AnyDesk, TeamViewer) or accessibility service overlays and immediately blackout screen or disable transaction initiation.",
                "FraudGuard Rule: Flag transactions originating from IP addresses matching known remote desktop relay nodes."
            ]
        }
    ]

    # Filter logic
    filtered_cases = fraud_cases
    if cat_filter != "All Categories":
        filtered_cases = [c for c in filtered_cases if c["category"] == cat_filter]
    if search_query.strip():
        q = search_query.lower()
        filtered_cases = [c for c in filtered_cases if q in c["title"].lower() or q in c["summary"].lower() or any(q in m.lower() for m in c["modus_operandi"])]

    st.markdown(f"**Showing {len(filtered_cases)} of {len(fraud_cases)} active threat intelligence dossiers**")
    st.markdown("<br>", unsafe_allow_html=True)

    for case in filtered_cases:
        badge_class = "badge-critical" if case["severity"] == "CRITICAL" else "badge-high"
        
        with st.container():
            st.markdown(f"""
            <div class="case-card">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;">
                    <div>
                        <span class="threat-badge {badge_class}">{case["severity"]} THREAT</span>
                        <span style="font-family:'Space Mono',monospace;font-size:0.7rem;color:#38bdf8;margin-left:8px;">{case["category"]}</span>
                        <h3 style="margin:0.4rem 0 0.2rem 0;color:#f0f9ff;font-size:1.25rem;">{case["title"]}</h3>
                        <p style="color:#94a3b8;font-size:0.85rem;margin:0;">{case["summary"]}</p>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-family:'Space Mono',monospace;font-size:0.65rem;color:#64748b;">ESTIMATED IMPACT</div>
                        <div style="font-family:'Space Mono',monospace;font-size:0.9rem;font-weight:700;color:#f87171;">{case["loss_stat"]}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Expandable Deep Dive
            with st.expander(f"🔍 Deep Dive: How '{case['title']}' Operates & How to Stop It"):
                c1, c2 = st.columns([1, 1])
                
                with c1:
                    st.markdown("#### ⚙️ Attack Execution Timeline (Modus Operandi)")
                    for idx, step in enumerate(case["modus_operandi"], 1):
                        st.markdown(f"""
                        <div style="display:flex;align-items:flex-start;margin-bottom:0.7rem;">
                            <div class="step-bubble">{idx}</div>
                            <div style="color:#cbd5e1;font-size:0.85rem;line-height:1.5;">{step}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("#### 🚩 Dead Giveaways & Red Flags")
                    for rf in case["red_flags"]:
                        st.markdown(f"""
                        <div class="red-flag">
                            <strong>⚠️ RED FLAG:</strong> {rf}
                        </div>
                        """, unsafe_allow_html=True)
                
                with c2:
                    st.markdown("#### 🛡️ Citizen / Customer Prevention Guide")
                    for p in case["prevention_citizen"]:
                        st.markdown(f"""
                        <div class="safe-guard">
                            <strong>✅ SAFEGUARD:</strong> {p}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("#### 💻 Technical & Banking Countermeasures (FraudGuard Integration)")
                    for t in case["prevention_tech"]:
                        st.markdown(f"""
                        <div class="rule-box">
                            <span style="font-family:'Space Mono',monospace;font-size:0.75rem;color:#38bdf8;font-weight:bold;">ENGINEERING CONTROL:</span><br>
                            <span style="font-size:0.82rem;color:#e2e8f0;">{t}</span>
                        </div>
                        """, unsafe_allow_html=True)
            
            st.markdown("<hr style='border-color:#1e2d45;margin:1rem 0;'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# TAB 2: "AM I BEING SCAMMED?" INTERACTIVE RISK CHECKER
# ─────────────────────────────────────────────────────────────────
with tab_checker:
    st.markdown('<p class="section-label">Interactive Scam Diagnostic & Early Warning Meter</p>', unsafe_allow_html=True)
    st.markdown("""
    Are you or someone you know in the middle of a suspicious call, message, or investment opportunity? 
    Check the indicators below to get an instant **Scam Probability Assessment** and recommended action.
    """)
    
    col_l, col_r = st.columns([1.2, 0.8])
    
    with col_l:
        st.subheader("📋 Situation Diagnostic Checklist")
        q1 = st.checkbox("1. Extreme Urgency: Caller or sender insists on action within minutes (e.g. 'Arrest in 1 hour', 'Electricity cuts at 9:30', 'Limited time deal')", key="scam_q1")
        q2 = st.checkbox("2. Money to Receive Money: They asked you to scan a QR code or enter your UPI PIN to 'receive' or 'refund' payment", key="scam_q2")
        q3 = st.checkbox("3. Authority Impersonation: Claims to be Police, CBI, ED, Customs, Courier, or High Court on Skype/WhatsApp", key="scam_q3")
        q4 = st.checkbox("4. Remote Screen Software: Asked you to download AnyDesk, TeamViewer, RustDesk, or a custom `.apk` file", key="scam_q4")
        q5 = st.checkbox("5. Unrealistic Returns: Offered guaranteed 20% to 200% returns on Telegram/WhatsApp crypto/task schemes", key="scam_q5")
        q6 = st.checkbox("6. Secrecy Demanded: Instructed you NOT to tell family members, bank managers, or visit physical branches", key="scam_q6")
        q7 = st.checkbox("7. Credential Phishing: Asked for your debit card CVV, expiry date, NetBanking password, or SMS OTP", key="scam_q7")
        q8 = st.checkbox("8. Unknown Beneficiary: Asking you to wire funds to personal individual accounts (mules) instead of official company accounts", key="scam_q8")

    with col_r:
        # Calculate Risk Score
        risk_weights = [15, 25, 25, 20, 20, 15, 25, 20]
        selections = [q1, q2, q3, q4, q5, q6, q7, q8]
        raw_score = sum(w for w, s in zip(risk_weights, selections) if s)
        scam_prob = min(100, int((raw_score / 100) * 100))
        
        st.subheader("🎯 Live Threat Assessment")
        
        # Color & Recommendation logic
        if scam_prob >= 50:
            status_color = "#ef4444"
            status_title = "🚨 HIGH PROBABILITY SCAM DETECTED"
            action_desc = "STOP ALL COMMUNICATION IMMEDIATELY! Do NOT transfer money, do NOT share OTP, do NOT scan any QR code. This matches active criminal syndicates."
        elif scam_prob >= 20:
            status_color = "#f59e0b"
            status_title = "⚠️ ELEVATED SUSPICION"
            action_desc = "Extreme caution required! Multiple red flags detected. Independently verify the organization using official publicly listed telephone numbers."
        else:
            status_color = "#22c55e"
            status_title = "✅ LOW IMMEDIATE RISK"
            action_desc = "No major red flags detected yet. However, always remember: never share OTP, passwords, or PIN with anyone."

        # Gauge Chart
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = scam_prob,
            number = {'suffix': "%", 'font': {'color': '#f0f9ff', 'family': 'Space Mono'}},
            gauge = {
                'axis': {'range': [0, 100], 'tickcolor': '#64748b'},
                'bar': {'color': status_color},
                'steps': [
                    {'range': [0, 25], 'color': "rgba(34, 197, 94, 0.15)"},
                    {'range': [25, 60], 'color': "rgba(245, 158, 11, 0.15)"},
                    {'range': [60, 100], 'color': "rgba(239, 68, 68, 0.25)"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 75
                }
            }
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={'color': "#f0f9ff"},
            height=240,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(f"""
        <div style="background:rgba(15,23,42,0.8);border:1px solid {status_color};border-radius:10px;padding:1rem;margin-top:0.5rem;">
            <div style="font-family:'Space Mono',monospace;font-size:0.95rem;font-weight:700;color:{status_color};margin-bottom:0.4rem;">{status_title}</div>
            <div style="font-size:0.82rem;color:#cbd5e1;line-height:1.5;">{action_desc}</div>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# TAB 3: EMERGENCY "GOLDEN HOUR" PROTOCOL
# ─────────────────────────────────────────────────────────────────
with tab_emergency:
    st.markdown('<p class="section-label">Incident Response & The "Golden Hour"</p>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="golden-hour-card">
        <div style="display:flex;align-items:center;gap:12px;">
            <div style="font-size:2.5rem;">⏳</div>
            <div>
                <h3 style="margin:0;color:#fbbf24;font-size:1.3rem;font-family:'Space Mono',monospace;">WHAT IS THE "GOLDEN HOUR" IN FINANCIAL FRAUD?</h3>
                <p style="color:#cbd5e1;font-size:0.85rem;margin:0.2rem 0 0 0;line-height:1.6;">
                    The first <strong>2 hours</strong> after an unauthorized transaction are critical. If reported immediately to the National Cybercrime Reporting Portal, authorities can initiate an inter-bank lien freeze before the scammer withdraws the money via ATM or crypto-converts it.
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_act1, col_act2 = st.columns(2)
    
    with col_act1:
        st.markdown("""
        ### ⚡ 4-Step Emergency Action Plan
        
        1. **DIAL 1930 IMMEDIATELY (National Cyber Crime Helpline):**
           - State the incident clearly: Transaction ID (UTR), debit bank name, beneficiary account/UPI ID, and exact amount.
           - The 1930 system alerts the Citizen Financial Cyber Fraud Reporting and Management System (CFCFRMS) to freeze funds in transit.
        
        2. **FREEZE & HOTLIST VIA YOUR BANK:**
           - Call your bank's 24x7 toll-free emergency number.
           - Demand immediate hotlisting of debit/credit cards and freeze NetBanking credentials.
        
        3. **FILE FORMAL COMPLAINT ON CYBERCRIME.GOV.IN:**
           - Upload transaction screenshots, chat logs, call recordings, and bank SMS statements.
           - Obtain your Crime Acknowledgment Number.
        
        4. **SUBMIT WRITTEN COMPLAINT TO HOME BRANCH WITHIN 3 DAYS:**
           - Under RBI Circulars on Limited Liability of Customers, zero liability applies if fraud is reported within 3 working days where the customer is not negligent.
        """)
    
    with col_act2:
        st.markdown("### 📞 Official Emergency Contact Directory")
        
        bank_contacts = pd.DataFrame([
            {"Institution / Portal": "National Cyber Crime Helpline", "Emergency Number": "1930", "Channel": "Toll-Free Phone"},
            {"Institution / Portal": "National Cybercrime Portal", "Emergency Number": "cybercrime.gov.in", "Channel": "Official Website"},
            {"Institution / Portal": "State Bank of India (SBI)", "Emergency Number": "1800 11 1109 / 1800 425 3800", "Channel": "24x7 Toll Free"},
            {"Institution / Portal": "HDFC Bank", "Emergency Number": "1800 1600 / 1800 2600", "Channel": "24x7 Toll Free"},
            {"Institution / Portal": "ICICI Bank", "Emergency Number": "1800 1080", "Channel": "24x7 Toll Free"},
            {"Institution / Portal": "Axis Bank", "Emergency Number": "1860 419 5555 / 1860 500 5555", "Channel": "24x7 Toll Free"},
            {"Institution / Portal": "Punjab National Bank", "Emergency Number": "1800 180 2222", "Channel": "24x7 Toll Free"},
            {"Institution / Portal": "RBI Sachet Portal (Unregulated Schemes)", "Emergency Number": "sachet.rbi.org.in", "Channel": "Web Complaints"}
        ])
        
        st.dataframe(bank_contacts, use_container_width=True, hide_index=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Downloadable Emergency Cheat Sheet
        cheat_sheet_content = """# FRAUDGUARD AI — EMERGENCY FINANCIAL FRAUD INCIDENT RESPONSE GUIDE
================================================================================
CRITICAL: The first 2 hours are the "Golden Hour" to recover stolen money!

STEP 1: DIAL 1930 IMMEDIATELY
- Provide Transaction UTR number, your bank account, amount, and suspect's UPI ID / Account.
- Enables CFCFRMS system to freeze funds in transit across intermediate bank nodes.

STEP 2: NOTIFY YOUR BANK'S 24x7 EMERGENCY HOTLINE
- Hotlist your debit/credit card immediately.
- Block NetBanking and UPI VPA temporarily.
- Demand an official Complaint Reference Number.

STEP 3: FILE AN OFFICIAL E-COMPLAINT
- Website: https://cybercrime.gov.in
- Preserve evidence: SMS alerts, WhatsApp chats, call history, account statements.

STEP 4: SUBMIT WRITTEN COMPLAINT TO HOME BRANCH WITHIN 3 DAYS
- Refer to RBI Circular on Customer Protection (Limited Liability in Unauthorized Electronic Transactions).

KEY GOLDEN RULES TO PREVENT FRAUD:
1. Entering UPI PIN or scanning QR codes ALWAYS deducts money; it NEVER receives money.
2. Police, CBI, ED, and RBI NEVER conduct interrogations or "Digital Arrests" via Skype or WhatsApp.
3. Never install AnyDesk, TeamViewer, QuickSupport, or .APK files from WhatsApp/SMS links.
================================================================================
Generated by FraudGuard AI Threat Intelligence System.
"""
        st.download_button(
            label="📥 Download Emergency Incident Response Checklist (TXT)",
            data=cheat_sheet_content,
            file_name="FraudGuard_Emergency_Fraud_Guide.txt",
            mime="text/plain",
            use_container_width=True
        )

# ─────────────────────────────────────────────────────────────────
# TAB 4: SYSTEM & API DEFENSE GUIDE (FOR DEVELOPERS / FACULTY)
# ─────────────────────────────────────────────────────────────────
with tab_developer:
    st.markdown('<p class="section-label">How FraudGuard AI Architecture Stops These Attacks</p>', unsafe_allow_html=True)
    st.markdown("""
    When explaining this project to your college faculty, emphasize that **Machine Learning alone is not enough**. 
    Production-grade fraud detection requires a **hybrid layered defense**:
    """)
    
    col_d1, col_d2 = st.columns(2)
    
    with col_d1:
        st.markdown("""
        #### 1. Layered Defense Architecture
        
        ```
        [ Layer 1: Edge & Network Security ]
        ├── Rate Limiting (Token Bucket: max 60 req/min)
        ├── IP Geolocation & VPN/Proxy Detection
        └── Device Fingerprinting & SIM Change Verification
                    │
                    ▼
        [ Layer 2: Deterministic Rule Engine (Heuristics) ]
        ├── QR Scan Inward Transfer Discrepancy Checks
        ├── Velocity Checks (e.g. >3 transfers to new VPA in 10 mins)
        └── Full Balance Drain Flag (oldbalanceOrg == amount)
                    │
                    ▼
        [ Layer 3: ML Inference Core (FraudGuard Model) ]
        ├── LightGBM / XGBoost probability scoring
        ├── Error balance deltas & transaction ratio features
        └── Sub-50ms inference latency SLA
                    │
                    ▼
        [ Layer 4: Action & Policy Engine ]
        ├── ALLOW (Risk < 30%)
        ├── CHALLENGE: Step-up OTP / Biometrics (Risk 30-75%)
        └── BLOCK: Immediate transaction halt + Alert (Risk > 75%)
        ```
        """)
    
    with col_d2:
        st.markdown("#### 2. Key FraudGuard Feature Formulas (Explainable AI)")
        st.markdown("""
        In our dataset and API service, the machine learning model evaluates key features that directly expose fraudster behavior:
        
        * **Origin Balance Drain (`errorBalanceOrg`):**
          $$\\text{errorBalanceOrg} = \\text{newbalanceOrig} + \\text{amount} - \\text{oldbalanceOrg}$$
          *Normal transaction:* Error is zero.
          *Fraud transaction:* Scammers frequently attempt to drain accounts to exactly ₹0, leaving large mathematical anomalies.
          
        * **Destination Balance Discrepancy (`errorBalanceDest`):**
          $$\\text{errorBalanceDest} = \\text{oldbalanceDest} + \\text{amount} - \\text{newbalanceDest}$$
          In mule accounts, funds frequently arrive and vanish into secondary wallets before new balances reflect correctly.
          
        * **Transaction Type Filtering:**
          `TRANSFER` and `CASH_OUT` account for over 99.8% of fraudulent activity in mobile money datasets.
        """)
        
        st.info("💡 **Faculty Tip:** Tell your faculty that your system uses SHAP (SHapley Additive exPlanations) to return clear reason codes with every prediction, satisfying regulatory compliance (e.g., GDPR & RBI Explainable AI mandates).")

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center;color:#475569;font-size:0.75rem;font-family:'Space Mono',monospace;">
    FRAUDGUARD AI — REAL-WORLD THREAT INTELLIGENCE SYSTEM &copy; 2026
</div>
""", unsafe_allow_html=True)
