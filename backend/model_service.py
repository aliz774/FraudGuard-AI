import pickle, json, time
import numpy as np
import pandas as pd
from pathlib import Path

MODELS_DIR = Path("models")

class FraudModel:
    def __init__(self):
        self.model      = None
        self.scaler     = None
        self.features   = None
        self.threshold  = 0.40
        self.model_type = "LightGBM"

    def load(self):
        # Load model and scaler (supports both pickle and joblib)
        try:
            import joblib
            self.model  = joblib.load(MODELS_DIR / "model.pkl")
            self.scaler = joblib.load(MODELS_DIR / "scaler.pkl")
        except Exception:
            with open(MODELS_DIR / "model.pkl",  "rb") as f: self.model  = pickle.load(f)
            with open(MODELS_DIR / "scaler.pkl", "rb") as f: self.scaler = pickle.load(f)

        # Load feature names (handles both plain list and dict formats)
        with open(MODELS_DIR / "feature_names.json") as f:
            config = json.load(f)
        self.features = config if isinstance(config, list) else config.get("features", config)

        # Load threshold & model type from metrics.json
        mp = MODELS_DIR / "metrics.json"
        if mp.exists():
            with open(mp) as f: m = json.load(f)
            self.threshold  = m.get("threshold",  self.threshold)
            self.model_type = m.get("model_type", self.model_type)

        print(f"   Model     : {self.model_type}")
        print(f"   Features  : {len(self.features)}")
        print(f"   Threshold : {self.threshold}")

    def _build_features(self, data: dict) -> pd.DataFrame:
        amount   = data["amount"]
        old_orig = data["oldbalanceOrg"]
        new_orig = data["newbalanceOrig"]
        old_dest = data["oldbalanceDest"]
        new_dest = data["newbalanceDest"]
        tx_type  = data["type"]

        row = {
            "step"                 : data["step"],
            "amount"               : amount,
            "oldbalanceOrg"        : old_orig,
            "newbalanceOrig"       : new_orig,
            "oldbalanceDest"       : old_dest,
            "newbalanceDest"       : new_dest,
            "balance_error_orig"   : old_orig - amount - new_orig,
            "balance_error_dest"   : old_dest + amount - new_dest,
            "amount_to_orig_ratio" : amount/(old_orig+1e-9) if old_orig>0 else 0.0,
            "new_orig_zero"        : int(new_orig == 0),
            "log_amount"           : np.log1p(amount),
            "dest_is_customer"     : int(data.get("nameDest","C")[:1]=="C"),
            "type_CASH_OUT"        : int(tx_type=="CASH_OUT"),
            "type_DEBIT"           : int(tx_type=="DEBIT"),
            "type_PAYMENT"         : int(tx_type=="PAYMENT"),
            "type_TRANSFER"        : int(tx_type=="TRANSFER"),
        }
        df = pd.DataFrame([row])
        for col in self.features:
            if col not in df.columns: df[col] = 0
        return df[self.features]

    def predict_one(self, data: dict) -> dict:
        t0       = time.time()
        feat_df  = self._build_features(data)
        scaled   = self.scaler.transform(feat_df)
        prob     = float(self.model.predict_proba(scaled)[0][1])
        is_fraud = prob >= self.threshold
        risk     = "HIGH" if prob>=0.80 else ("MEDIUM" if prob>=0.40 else "LOW")
        return {
            "is_fraud"         : bool(is_fraud),
            "fraud_probability": round(prob, 4),
            "risk_level"       : risk,
            "confidence"       : round(abs(prob-0.5)*2, 4),
            "threshold_used"   : self.threshold,
            "model_version"    : self.model_type,
            "inference_ms"     : round((time.time()-t0)*1000, 2),
        }

    def predict_batch(self, records: list) -> list:
        return [self.predict_one(r) for r in records]

fraud_model = FraudModel()

