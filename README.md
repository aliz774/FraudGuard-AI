# 🛡️ FraudGuard AI — Enterprise Real-Time Financial Fraud Detection & Threat Intelligence

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg)](https://streamlit.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com)
[![Machine Learning](https://img.shields.io/badge/Model-LightGBM%20%7C%20XGBoost-success.svg)](https://lightgbm.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Security](https://img.shields.io/badge/Auth-Salted%20PBKDF2--SHA256-green.svg)](auth.py)

> **An end-to-end intelligent fraud prevention ecosystem that combines Machine Learning inference, high-throughput REST APIs, human-in-the-loop alert investigations, and real-world citizen threat intelligence.**

---

## 📌 Table of Contents
- [Project Overview](#-project-overview)
- [Key Features & Modules](#-key-features--modules)
- [System Architecture](#-system-architecture)
- [Machine Learning & Performance Benchmarks](#-machine-learning--performance-benchmarks)
- [Pre-Configured Demo Accounts (RBAC)](#-pre-configured-demo-accounts-rbac)
- [Installation & Quickstart](#-installation--quickstart)
- [Repository Structure](#-repository-structure)
- [Deployment Guide](#-deployment-guide)
- [License](#-license)

---

## 📖 Project Overview

Digital payment systems (UPI, NetBanking, Credit/Debit cards, Digital Wallets) process billions of transactions daily. However, modern financial fraud is evolving rapidly—from synthetic identity theft and account takeovers to generative AI deepfakes and deceptive QR codes. Traditional rule-based engines fail to detect nuanced balance-drain anomalies and adapt to adversarial tactics.

**FraudGuard AI** solves this by providing:
1. **Machine Learning Core**: Sub-50ms probability scoring using calibrated gradient-boosted decision trees (LightGBM/XGBoost).
2. **Explainable AI (XAI)**: Immediate anomaly factor breakdowns so analysts understand *why* a transaction was flagged.
3. **Investigation Workflow**: SQLite-backed case management system with status lifecycles (`OPEN` → `INVESTIGATING` → `RESOLVED` / `DISMISSED`).
4. **Model Drift Monitoring**: Real-time tracking of rolling 7-day fraud rates and statistical distribution shifts.
5. **Citizen Threat Hub**: Educational threat intelligence with interactive scam diagnostics and National Cyber Crime 1930 emergency protocols.

---

## ✨ Key Features & Modules

### 1. 🔐 Enterprise Authentication & RBAC (`auth.py`)
* Multi-tiered **Role-Based Access Control** (`fraud_analyst`, `manager`, `admin`).
* High-security **PBKDF2-HMAC-SHA256** (100,000 iterations + per-user 16-byte random salt).
* **7-Day Session Persistence**: Seamless session recovery across browser reloads via cryptographically secure URL tokens.
* In-app profile drawer with **Change Password** support.

### 2. 🔍 Real-Time Manual Transaction Evaluator (`1_manual_input.py`)
* Instant risk scoring (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) with visual gauge meters.
* Quick demo presets (*"🔴 Suspicious Cash-Out"*, *"🟢 Small Normal Payment"*, etc.).
* **Human-in-the-Loop Feedback Loop**: Analysts vote on outcomes (*"Yes, Fraud"* / *"No, Safe"*) to generate verified ground-truth retraining data.

### 3. 📂 Batch CSV Scanner & Auditor (`2_csv_upload.py`)
* Bulk scanning of thousands of transaction records within seconds.
* Interactive filtering by risk category and one-click export of audited CSV reports.

### 4. 📊 Executive Analytics Dashboard (`3_dashboard.py`)
* High-level managerial visibility restricted to **Managers** and **Admins**.
* KPI cards: Total volume scrutinized, fraud detection rate, financial loss prevented, and transaction category splits.

### 5. 📈 Model Performance & Statistical Drift Engine (`4_performance.py` + `performance_monitor.py`)
* Live evaluation benchmarks: Confusion Matrix, ROC-AUC curve, PR-AUC curve, and False Positive Rate metrics.
* **Live Prediction Telemetry**: Real-time throughput (last 24 hours), analyst feedback coverage, and automated **Model Drift Detection**.

### 6. 🚨 Alert Management & Audit Trail (`5_alerts.py`)
* Relational SQLite database (`alerts.db`) storing flagged transactions.
* Full investigation workflow: assign auditor, update statuses, attach resolution notes, and export compliance logs.

### 7. 🌐 Real-World Threat Intelligence & Prevention Hub (`6_threat_intel.py`)
* Comprehensive real-life case studies:
  * *The ₹1,200 Cr "Digital Arrest" & Fake Police Video Call Scam*
  * *The $25.6 Million AI Deepfake CFO Multi-Executive Conference Heist*
  * *The "Scan QR to Receive Money" Marketplace Trap*
  * *SIM Swap & Remote e-SIM Takeover*
  * *Pig Butchering (Sha Zhu Pan) & Fake Telegram Investment Tasks*
* **Interactive "Am I Being Scammed?" Diagnostic**: 8-point live probability meter.
* **Emergency "Golden Hour" Protocol**: 4-step crisis response with National Helpline **1930** and 24x7 bank hotlines.

### 8. ⚡ Fraud-as-a-Service (FaaS) REST API (`backend/`)
* High-performance FastAPI microservice (`/api/v1/predict`, `/batch`, `/csv`, `/health`, `/metrics`).
* Interactive OpenAPI/Swagger documentation at `/docs` ready for merchant checkout integration.

---

## 🏛️ System Architecture

```
[ External Client / Web Portal ]
           │
           ├── (Streamlit Multi-Page UI :8501)
           │          │
           │          ├── Manual Input & Feedback Loop
           │          ├── Batch CSV Scanner
           │          ├── Executive Dashboard (RBAC Protected)
           │          ├── Performance & Drift Telemetry
           │          ├── Alert Management Workflow (SQLite alerts.db)
           │          └── Real-World Threat Intel & Scam Diagnostic
           │
           └── (FastAPI REST API Microservice :8000)
                      │
                      ▼
           [ Feature Engineering & Transformer ]
           ├── Balance delta errors (errorBalanceOrg, errorBalanceDest)
           ├── Amount-to-balance ratio & zero-balance flags
           └── One-hot transaction encoding
                      │
                      ▼
           [ LightGBM / XGBoost Inference Core ]
           └── Calibrated Probability Scoring (Sub-50ms SLA)
                      │
                      ▼
           [ 3-Tier Policy Engine ]
           ├── ALLOW     (Risk < 30%)
           ├── CHALLENGE (Risk 30% - 75% -> Step-up OTP/2FA)
           └── BLOCK     (Risk > 75% -> Immediate Decline + Alert Log)
```

---

## 📊 Machine Learning & Performance Benchmarks

Trained on financial mobile money data (~6.3 million records) with calibrated decision thresholds to minimize customer friction:

| Metric | Score | Industry Standard | Status |
|---|---|---|---|
| **Recall (Fraud Caught)** | **93.0%** | > 85.0% | 🟢 Exceptional |
| **Precision** | **87.1%** | > 80.0% | 🟢 High Confidence |
| **ROC-AUC** | **0.990** | > 0.950 | 🟢 State-of-the-Art |
| **PR-AUC** | **0.912** | > 0.850 | 🟢 Robust to Imbalance |
| **False Positive Rate (FPR)** | **0.08%** | < 0.50% | 🟢 Minimal Legitimate Blockage |
| **Inference Latency** | **~12 - 45 ms** | < 100 ms | 🟢 Real-Time Ready |

### Key Mathematical Anomaly Features
* **Origin Balance Drain Error:**
  $$\text{errorBalanceOrg} = \text{newbalanceOrig} + \text{amount} - \text{oldbalanceOrg}$$
* **Destination Influx Discrepancy:**
  $$\text{errorBalanceDest} = \text{oldbalanceDest} + \text{amount} - \text{newbalanceDest}$$

---

## 👥 Pre-Configured Demo Accounts (RBAC)

Use these accounts to test role-based permissions:

| Role | Username | Password | Access Rights |
|---|---|---|---|
| **🔍 Fraud Analyst** | `analyst1` | `analyst123` | Manual Prediction, CSV Batch, Alerts, Threat Intel, Feedback |
| **👔 Manager** | `manager` | `manager123` | **Full Access** + Executive Analytics Dashboard & Performance Monitor |
| **⚙️ Administrator** | `admin` | `admin123` | **Full Access** + User Administration |

---

## 🚀 Installation & Quickstart

### Prerequisites
* Python 3.10, 3.11, or 3.12
* Git

### 1. Clone the Repository
```bash
git clone https://github.com/aliz774/FraudGuard-AI.git
cd FraudGuard-AI
```

### 2. Create & Activate Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Launch the Applications

#### Launch Streamlit Frontend:
```bash
streamlit run home.py
```
*Access in browser at:* **`http://localhost:8501`**

#### Launch FastAPI Microservice Backend (Optional):
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```
*Interactive Swagger API Docs at:* **`http://localhost:8000/docs`**

---

## 📂 Repository Structure

```
FraudGuard-AI/
├── home.py                    # Main application entry point & router
├── auth.py                    # PBKDF2 authentication & RBAC engine
├── performance_monitor.py     # Live prediction tracking & model drift engine
├── requirements.txt           # Production dependencies
├── alerts.db                  # SQLite database (alerts & live predictions)
├── users.json                 # Document store for user credentials
├── sessions.json              # Document store for persistent session tokens
│
├── pages/                     # Streamlit multi-page views
│   ├── 1_manual_input.py      # Real-time transaction evaluator & feedback loop
│   ├── 2_csv_upload.py        # Bulk CSV scanning & auditing
│   ├── 3_dashboard.py         # Executive KPI analytics (Manager/Admin only)
│   ├── 4_performance.py       # Model health, confusion matrix & drift monitor
│   ├── 5_alerts.py            # Case investigation & alert resolution system
│   └── 6_threat_intel.py      # Threat intelligence, scam diagnostic & golden hour
│
├── models/                    # Model serialization artifacts
│   ├── model.pkl              # Pre-trained LightGBM classifier (~2.8 MB)
│   ├── scaler.pkl             # StandardScaler artifact
│   ├── feature_names.json     # Feature alignment configuration
│   └── metrics.json           # Evaluation benchmarks
│
└── backend/                   # FastAPI microservice
    ├── main.py                # FastAPI app initialization & CORS
    ├── routes.py              # REST API endpoints (/predict, /batch, /csv)
    ├── model_service.py       # Model inference handler
    └── models/                # Backend model mirror
```

---

## ☁️ Deployment Guide

### Deploying to Streamlit Community Cloud (Free)
1. Fork or push this repository to your GitHub account.
2. Sign in to **[share.streamlit.io](https://share.streamlit.io)** using GitHub.
3. Click **"New app"** → Select your repository (`FraudGuard-AI`) and branch (`main`).
4. Set **Main file path** to: `home.py`.
5. Click **"Deploy"** — your live application will be available at `https://<your-app-name>.streamlit.app`.

---

## 📜 License

This project is licensed under the **MIT License** — feel free to use and adapt it for academic and commercial projects.
