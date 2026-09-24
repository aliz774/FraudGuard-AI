# ─────────────────────────────────────────────────────────────────
# auth.py — Enterprise Authentication System for FraudGuard AI
# ─────────────────────────────────────────────────────────────────

import streamlit as st
import hashlib
import hmac
import secrets
import json
import re
from pathlib import Path
from datetime import datetime, timedelta

USERS_FILE = Path("users.json")
SESSIONS_FILE = Path("sessions.json")
SESSION_EXPIRY_DAYS = 7

# ── Password Hashing & Security ───────────────────────────────────

def hash_password(password: str, salt: str = None) -> str:
    """
    Hashes a password using PBKDF2-HMAC-SHA256 with 100,000 iterations and a unique salt.
    Format: pbkdf2:sha256:100000$<salt>$<hash>
    """
    if salt is None:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"pbkdf2:sha256:100000${salt}${key.hex()}"

def verify_password(stored_hash: str, password: str) -> tuple[bool, bool]:
    """
    Verifies a password against the stored hash.
    Supports both modern salted PBKDF2 and legacy unsalted SHA-256 for backward compatibility.
    Returns (is_valid, needs_upgrade).
    """
    if not stored_hash or not password:
        return False, False

    # Check if modern PBKDF2 hash
    if stored_hash.startswith("pbkdf2:sha256:"):
        try:
            parts = stored_hash.split("$")
            if len(parts) == 3:
                iterations = int(parts[0].split(":")[-1])
                salt = parts[1]
                expected_hash = parts[2]
                computed = hashlib.pbkdf2_hmac(
                    "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
                ).hex()
                return hmac.compare_digest(computed, expected_hash), False
        except Exception:
            return False, False

    # Check legacy unsalted SHA-256 hash (64 hex characters)
    legacy_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    if hmac.compare_digest(legacy_hash, stored_hash):
        return True, True  # Valid, but should be upgraded to salted PBKDF2

    return False, False

# ── Storage Management (Safe JSON I/O) ───────────────────────────

def load_users() -> dict:
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_users(users: dict):
    temp_file = USERS_FILE.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)
    temp_file.replace(USERS_FILE)

def load_sessions() -> dict:
    if SESSIONS_FILE.exists():
        try:
            with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_sessions(sessions: dict):
    try:
        temp_file = SESSIONS_FILE.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(sessions, f, indent=2)
        temp_file.replace(SESSIONS_FILE)
    except Exception:
        pass

# ── Validation & Search Helpers ───────────────────────────────────

def find_user_key(users: dict, username: str) -> str:
    """Finds a user in the dictionary case-insensitively."""
    if not username:
        return None
    target = username.strip().lower()
    for key in users:
        if key.strip().lower() == target:
            return key
    return None

def validate_username(username: str) -> tuple[bool, str]:
    if not username:
        return False, "Username cannot be empty"
    username = username.strip()
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    if len(username) > 30:
        return False, "Username cannot exceed 30 characters"
    if not re.match(r"^[a-zA-Z0-9_.-]+$", username):
        return False, "Username can only contain letters, numbers, underscores, dots, and hyphens"
    return True, ""

def validate_email(email: str) -> tuple[bool, str]:
    if not email:
        return False, "Email cannot be empty"
    email = email.strip()
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, email):
        return False, "Please enter a valid email address (e.g. name@company.com)"
    return True, ""

# ── User Account Lifecycle ────────────────────────────────────────

def create_user(username: str, password: str, email: str, role: str = "fraud_analyst") -> tuple[bool, str]:
    ok, err = validate_username(username)
    if not ok:
        return False, err
    ok, err = validate_email(email)
    if not ok:
        return False, err
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters"

    users = load_users()
    canonical = username.strip()
    if find_user_key(users, canonical):
        return False, "Username already exists"

    users[canonical] = {
        "password_hash": hash_password(password),
        "email": email.strip(),
        "role": role,
        "created_at": datetime.now().isoformat(),
        "last_login": None,
    }
    save_users(users)
    return True, "User registered successfully"

def verify_user(username: str, password: str) -> bool:
    if not username or not password:
        return False
    users = load_users()
    key = find_user_key(users, username)
    if not key:
        return False

    user_record = users[key]
    stored_hash = user_record.get("password_hash", "")
    is_valid, needs_upgrade = verify_password(stored_hash, password)

    if not is_valid:
        return False

    # Transparently upgrade legacy SHA-256 to PBKDF2 on successful login
    if needs_upgrade:
        user_record["password_hash"] = hash_password(password)

    user_record["last_login"] = datetime.now().isoformat()
    save_users(users)
    return True

def get_user_info(username: str) -> dict:
    if not username:
        return None
    users = load_users()
    key = find_user_key(users, username)
    if key and key in users:
        info = users[key].copy()
        info.pop("password_hash", None)
        info["username"] = key
        return info
    return None

def change_password(username: str, old_password: str, new_password: str) -> tuple[bool, str]:
    if not new_password or len(new_password) < 6:
        return False, "New password must be at least 6 characters"
    users = load_users()
    key = find_user_key(users, username)
    if not key:
        return False, "User not found"

    stored_hash = users[key].get("password_hash", "")
    is_valid, _ = verify_password(stored_hash, old_password)
    if not is_valid:
        return False, "Current password is incorrect"

    users[key]["password_hash"] = hash_password(new_password)
    save_users(users)
    return True, "Password updated successfully"

# ── Session State & Persistence Management ────────────────────────

def init_session():
    """Initializes session state and restores session from query params if valid and not expired."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "user_role" not in st.session_state:
        st.session_state.user_role = None

    # Restore session from query parameters on browser reload
    if not st.session_state.authenticated:
        qp_user = st.query_params.get("user")
        qp_token = st.query_params.get("token")
        if qp_user and qp_token:
            sessions = load_sessions()
            user_session = sessions.get(qp_user)
            if user_session and user_session.get("token") == qp_token:
                # Check expiration
                created_str = user_session.get("created_at")
                is_expired = False
                if created_str:
                    try:
                        created_time = datetime.fromisoformat(created_str)
                        if datetime.now() - created_time > timedelta(days=SESSION_EXPIRY_DAYS):
                            is_expired = True
                    except Exception:
                        is_expired = True

                if not is_expired:
                    user_info = get_user_info(qp_user)
                    if user_info:
                        st.session_state.authenticated = True
                        st.session_state.username = user_info["username"]
                        st.session_state.user_role = user_info.get("role", "fraud_analyst")
                        return

            # If invalid or expired, clear stale query params
            st.query_params.clear()

def login_user(username: str, remember: bool = True):
    user_info = get_user_info(username)
    canonical = user_info["username"] if user_info else username.strip()

    st.session_state.authenticated = True
    st.session_state.username = canonical
    st.session_state.user_role = user_info.get("role", "fraud_analyst") if user_info else "fraud_analyst"

    if remember:
        token = secrets.token_hex(24)
        sessions = load_sessions()
        sessions[canonical] = {
            "token": token,
            "created_at": datetime.now().isoformat()
        }
        save_sessions(sessions)
        st.query_params["user"] = canonical
        st.query_params["token"] = token
    else:
        st.query_params.clear()

def logout_user():
    username = st.session_state.get("username")
    if username:
        sessions = load_sessions()
        sessions.pop(username, None)
        save_sessions(sessions)
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.user_role = None
    st.query_params.clear()

def require_auth():
    init_session()
    if not st.session_state.authenticated:
        show_login_page()
        st.stop()

# ── Role-Based Access Control (RBAC) ──────────────────────────────

def is_admin() -> bool:
    return st.session_state.get("user_role") == "admin"

def is_manager() -> bool:
    return st.session_state.get("user_role") in ["manager", "admin"]

def is_fraud_analyst() -> bool:
    return st.session_state.get("user_role") in ["fraud_analyst", "manager", "admin"]

def can_train_model() -> bool:
    return st.session_state.get("user_role") in ["fraud_analyst", "manager", "admin"]

def can_view_dashboard() -> bool:
    return st.session_state.get("user_role") in ["manager", "admin"]

def can_download_reports() -> bool:
    return st.session_state.get("user_role") in ["manager", "admin"]

def get_role_display_name(role: str) -> str:
    return {
        "fraud_analyst": "🔍 Fraud Analyst",
        "manager": "👔 Manager",
        "admin": "⚙️ Administrator",
    }.get(role, "👤 User")

def list_all_users() -> list:
    if not is_admin():
        return []
    users = load_users()
    return [
        {
            "username": u,
            "email": i.get("email", ""),
            "role": i.get("role", "fraud_analyst"),
            "created_at": i.get("created_at", ""),
            "last_login": i.get("last_login", "Never")
        }
        for u, i in users.items()
    ]

# ── UI Components ─────────────────────────────────────────────────

def show_login_page():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Sora:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; }
    .stApp { background: #080c14; color: #e2e8f0; }

    .stTextInput input, .stSelectbox select {
        background: rgba(13, 19, 33, 0.8) !important;
        border: 1px solid #1e3a5f !important;
        color: #f0f9ff !important;
        border-radius: 8px !important;
    }
    .stTextInput input:focus {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.3) !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'Space Mono', monospace !important;
        font-weight: 700 !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.5) !important;
        transform: translateY(-1px) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2.2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center; padding: 2rem 0 1rem 0;">
            <div style="font-size:3.5rem; margin-bottom:0.5rem; filter: drop-shadow(0 0 15px rgba(56,189,248,0.4));">🛡️</div>
            <div style="font-family:'Space Mono',monospace; font-size:2rem; font-weight:700; color:#f0f9ff; letter-spacing: 2px;">
                FRAUDGUARD <span style="color:#38bdf8;">AI</span>
            </div>
            <div style="font-size:0.85rem; color:#64748b; margin-top:0.5rem;">
                Enterprise Fraud Detection & Real-time Threat Analytics
            </div>
        </div>
        """, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["🔐 Secure Login", "📝 Create Account"])
        with tab1:
            show_login_form()
        with tab2:
            show_signup_form()

        st.markdown("---")
        st.markdown("""
        <div style="text-align:center; font-size:0.75rem; color:#475569; margin-top:1.5rem;">
            🔒 Session Persistence Enabled • Protected by PBKDF2-SHA256 Encryption<br>
            FraudGuard AI v1.0.0
        </div>
        """, unsafe_allow_html=True)

def show_login_form():
    st.markdown("### Welcome Back")
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        remember = st.checkbox("Remember session across page refreshes", value=True)
        submit = st.form_submit_button("🔓 Log In to Dashboard", use_container_width=True, type="primary")

        if submit:
            username_clean = username.strip() if username else ""
            if not username_clean or not password:
                st.error("❌ Please enter both username and password")
            elif verify_user(username_clean, password):
                login_user(username_clean, remember=remember)
                st.success(f"✅ Welcome back, {username_clean}!")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

    st.info("💡 **Demo Accounts:**\n\n"
            "🔍 **Analyst:** `analyst1` / `analyst123` (Manual Input, CSV Upload, Alerts, Threat Intel)\n\n"
            "👔 **Manager:** `manager` / `manager123` (Full Access including Executive Dashboard & Performance Monitor)\n\n"
            "⚙️ **Admin:** `admin` / `admin123` (Administrator Access)")

def show_signup_form():
    st.markdown("### Create New Account")
    with st.form("signup_form", clear_on_submit=False):
        new_username = st.text_input("Username", placeholder="Choose a username (letters, numbers, underscore)")
        new_email = st.text_input("Email", placeholder="your.email@example.com")
        new_password = st.text_input("Password", type="password", placeholder="Choose a strong password (min 6 chars)")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
        new_role = st.selectbox(
            "Select Role",
            options=["fraud_analyst", "manager"],
            format_func=lambda x: "🔍 Fraud Analyst" if x == "fraud_analyst" else "👔 Manager"
        )
        agree = st.checkbox("I agree to the Terms of Service and Security Policy")
        submit = st.form_submit_button("📝 Register Account", use_container_width=True, type="primary")

        if submit:
            if not new_username or not new_email or not new_password:
                st.error("❌ Please fill in all fields")
            elif new_password != confirm_password:
                st.error("❌ Passwords do not match")
            elif not agree:
                st.error("❌ Please agree to the Security Policy")
            else:
                ok, msg = create_user(new_username, new_password, new_email, new_role)
                if ok:
                    st.success(f"✅ Account created successfully! Welcome, {new_username.strip()}!")
                    login_user(new_username.strip(), remember=True)
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

def show_user_profile():
    if st.session_state.get("authenticated"):
        user_info = get_user_info(st.session_state.username)
        role_display = get_role_display_name(st.session_state.user_role)
        st.markdown("---")
        st.markdown("""
        <div style="font-family:'Space Mono',monospace; font-size:0.6rem;
                    letter-spacing:2px; color:#38bdf8; margin-bottom:0.5rem;">
            ACTIVE USER SESSION
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:rgba(13, 19, 33, 0.8); border:1px solid #1e3a5f; border-radius:10px; padding:0.8rem;">
            <div style="font-weight:600; color:#f0f9ff; margin-bottom:0.3rem;">
                👤 {st.session_state.username}
            </div>
            <div style="font-size:0.7rem; color:#64748b;">
                {user_info['email'] if user_info else 'No email registered'}
            </div>
            <div style="font-size:0.65rem; color:#475569; margin-top:0.4rem;">
                Role: <span style="color:#38bdf8; font-family:'Space Mono',monospace;">{role_display}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='margin-top:0.5rem;'></div>", unsafe_allow_html=True)

        with st.expander("🔑 Change Password"):
            with st.form("change_pwd_form", clear_on_submit=True):
                curr_p = st.text_input("Current Password", type="password")
                new_p = st.text_input("New Password (min 6 chars)", type="password")
                conf_p = st.text_input("Confirm New Password", type="password")
                chg_submit = st.form_submit_button("Update Password", use_container_width=True)
                if chg_submit:
                    if not curr_p or not new_p:
                        st.error("Please fill all password fields")
                    elif new_p != conf_p:
                        st.error("New passwords do not match")
                    elif len(new_p) < 6:
                        st.error("New password must be at least 6 characters")
                    else:
                        ok, msg = change_password(st.session_state.username, curr_p, new_p)
                        if ok:
                            st.success("✅ Password updated successfully!")
                        else:
                            st.error(f"❌ {msg}")

        if st.button("🚪 Log Out", use_container_width=True, type="secondary"):
            logout_user()
            st.rerun()

# ── Initialization ────────────────────────────────────────────────

def init_default_users():
    users = load_users()
    if not users:
        create_user("analyst1", "analyst123", "analyst1@fraudguard.ai", "fraud_analyst")
        create_user("analyst2", "analyst123", "analyst2@fraudguard.ai", "fraud_analyst")
        create_user("manager",  "manager123", "manager@fraudguard.ai",  "manager")
        create_user("admin",    "admin123",   "admin@fraudguard.ai",    "admin")

init_default_users()