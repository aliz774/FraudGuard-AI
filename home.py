# ─────────────────────────────────────────────────────────────────
# Home.py — Main entry point with authentication
# Run:  streamlit run Home.py
# ─────────────────────────────────────────────────────────────────

import streamlit as st
import auth

st.set_page_config(
    page_title="FraudGuard AI",
    page_icon="🛡️",
    layout="wide"
)

auth.require_auth()
st.switch_page("pages/1_manual_input.py")