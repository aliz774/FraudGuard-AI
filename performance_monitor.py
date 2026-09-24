# ─────────────────────────────────────────────────────────────────
# performance_monitor.py — Live Prediction Tracking & Model Drift
# ─────────────────────────────────────────────────────────────────

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
import random

DB_PATH = Path("alerts.db")

class PerformanceMonitor:
    """
    Tracks real-time predictions, analyst ground-truth feedback,
    and monitors model drift and statistical stability.
    """
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()
        self._seed_if_empty()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._get_connection()
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            transaction_id TEXT,
            is_fraud INTEGER NOT NULL,
            fraud_prob REAL NOT NULL,
            risk_level TEXT,
            payload TEXT,
            user_id TEXT,
            actual_outcome INTEGER DEFAULT NULL,
            feedback_at TEXT DEFAULT NULL
        )
        """)
        conn.commit()
        conn.close()

    def _seed_if_empty(self):
        conn = self._get_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM predictions")
        count = c.fetchone()[0]
        if count == 0:
            # Seed realistic historical demo predictions over past 7 days
            now = datetime.now()
            sample_tx_types = ["TRANSFER", "CASH_OUT", "PAYMENT", "CASH_IN", "DEBIT"]
            rows = []
            
            # Generate ~1,420 historical predictions
            total_seed = 1420
            for i in range(total_seed):
                # Spread out timestamps over the last 7 days
                hours_ago = random.uniform(0.1, 168.0)
                tx_time = now - timedelta(hours=hours_ago)
                
                # Realistic ~2.4% fraud rate
                is_fraud = 1 if random.random() < 0.024 else 0
                if is_fraud:
                    prob = random.uniform(0.72, 0.99)
                    risk = "CRITICAL" if prob > 0.85 else "HIGH"
                else:
                    prob = random.uniform(0.001, 0.28)
                    risk = "LOW" if prob < 0.15 else "MEDIUM"
                
                # ~82% of predictions have analyst feedback
                has_feedback = random.random() < 0.82
                actual = is_fraud if has_feedback else None
                fb_time = (tx_time + timedelta(minutes=random.uniform(2, 60))).isoformat() if has_feedback else None

                tx_id = f"TXN-{tx_time.strftime('%Y%m%d%H%M')}-{random.randint(100,999)}"
                payload = json.dumps({
                    "type": random.choice(sample_tx_types),
                    "amount": round(random.uniform(500, 250000), 2)
                })

                rows.append((
                    tx_time.isoformat(),
                    tx_id,
                    is_fraud,
                    round(prob, 4),
                    risk,
                    payload,
                    "analyst1",
                    actual,
                    fb_time
                ))

            c.executemany("""
            INSERT INTO predictions (
                created_at, transaction_id, is_fraud, fraud_prob,
                risk_level, payload, user_id, actual_outcome, feedback_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rows)
            conn.commit()

        conn.close()

    def log_prediction(self, is_fraud: bool, prob: float, risk_level: str,
                       transaction_id: str, payload: dict = None, user_id: str = None) -> int:
        """
        Logs a single inference prediction into the SQLite database.
        Returns the unique prediction ID (pid).
        """
        conn = self._get_connection()
        c = conn.cursor()
        now_str = datetime.now().isoformat()
        payload_str = json.dumps(payload) if payload else "{}"
        
        c.execute("""
        INSERT INTO predictions (
            created_at, transaction_id, is_fraud, fraud_prob,
            risk_level, payload, user_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            now_str,
            transaction_id,
            1 if is_fraud else 0,
            float(prob),
            str(risk_level),
            payload_str,
            str(user_id or "system")
        ))
        pid = c.lastrowid
        conn.commit()
        conn.close()
        return pid

    def record_actual_outcome(self, pid: int, actual_is_fraud: bool):
        """
        Records ground-truth analyst feedback on whether the transaction
        was genuinely fraudulent or safe.
        """
        conn = self._get_connection()
        c = conn.cursor()
        c.execute("""
        UPDATE predictions
        SET actual_outcome = ?, feedback_at = ?
        WHERE id = ?
        """, (1 if actual_is_fraud else 0, datetime.now().isoformat(), pid))
        conn.commit()
        conn.close()

    def get_summary_stats(self) -> dict:
        """
        Calculates total predictions, 24h throughput, 7-day fraud rate,
        and feedback coverage.
        """
        conn = self._get_connection()
        c = conn.cursor()

        now = datetime.now()
        yesterday_str = (now - timedelta(days=1)).isoformat()
        seven_days_ago_str = (now - timedelta(days=7)).isoformat()

        # Total predictions
        c.execute("SELECT COUNT(*) FROM predictions")
        total = c.fetchone()[0] or 0

        # Predictions in last 24h
        c.execute("SELECT COUNT(*) FROM predictions WHERE created_at >= ?", (yesterday_str,))
        pred_24h = c.fetchone()[0] or 0

        # Current fraud rate in last 7 days
        c.execute("""
        SELECT COUNT(*), SUM(is_fraud)
        FROM predictions
        WHERE created_at >= ?
        """, (seven_days_ago_str,))
        row_7d = c.fetchone()
        count_7d = row_7d[0] or 0
        fraud_7d = row_7d[1] or 0
        current_fraud_rate = (fraud_7d / count_7d) if count_7d > 0 else 0.024

        # Feedback coverage
        c.execute("SELECT COUNT(*) FROM predictions WHERE actual_outcome IS NOT NULL")
        feedback_count = c.fetchone()[0] or 0
        feedback_coverage = (feedback_count / total) if total > 0 else 0.0

        conn.close()

        return {
            "total_predictions": total,
            "predictions_24h": pred_24h,
            "current_fraud_rate": round(current_fraud_rate, 4),
            "feedback_coverage": round(feedback_coverage, 4)
        }

    def get_model_drift_indicators(self) -> dict:
        """
        Evaluates prediction drift by comparing recent 7-day predicted fraud rate
        against baseline distribution.
        """
        stats = self.get_summary_stats()
        current_rate = stats.get("current_fraud_rate", 0.024)
        baseline_rate = 0.020  # Standard expected ~2.0% baseline
        
        # Drift threshold: if fraud rate swings above 6% or drops below 0.5%
        drift_detected = (current_rate > 0.06 or current_rate < 0.005)

        return {
            "drift_detected": drift_detected,
            "baseline_fraud_rate": baseline_rate,
            "current_fraud_rate": current_rate,
            "status": "DRIFT_ALERT" if drift_detected else "STABLE"
        }
