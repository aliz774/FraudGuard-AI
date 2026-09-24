from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
import pandas as pd, json, io
from pathlib import Path
from model_service import fraud_model

router = APIRouter()

class TransactionInput(BaseModel):
    step          : int   = Field(..., ge=1, le=744)
    type          : str   = Field(..., example="TRANSFER")
    amount        : float = Field(..., gt=0)
    oldbalanceOrg : float = Field(..., ge=0)
    newbalanceOrig: float = Field(..., ge=0)
    oldbalanceDest: float = Field(..., ge=0)
    newbalanceDest: float = Field(..., ge=0)
    nameDest      : Optional[str] = "C_unknown"

    @validator("type")
    def type_must_be_valid(cls, v):
        valid = {"TRANSFER","CASH_OUT","CASH_IN","PAYMENT","DEBIT"}
        if v.upper() not in valid: raise ValueError(f"type must be one of {valid}")
        return v.upper()

class BatchRequest(BaseModel):
    transactions: List[TransactionInput]

@router.post("/predict")
def predict_single(tx: TransactionInput):
    try:
        r = fraud_model.predict_one(tx.dict())
        r["timestamp"] = datetime.utcnow().isoformat()+"Z"
        return r
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict/batch")
def predict_batch(req: BatchRequest):
    try:
        results = []
        for tx in req.transactions:
            r = fraud_model.predict_one(tx.dict())
            r["timestamp"] = datetime.utcnow().isoformat()+"Z"
            results.append(r)
        fc = sum(1 for r in results if r["is_fraud"])
        return {"total":len(results),"fraud_count":fc,"fraud_rate":round(fc/len(results),4),"predictions":results}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict/csv")
async def predict_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        required = ["step","type","amount","oldbalanceOrg","newbalanceOrig","oldbalanceDest","newbalanceDest"]
        missing  = [c for c in required if c not in df.columns]
        if missing: raise HTTPException(status_code=400, detail=f"Missing columns: {missing}")
        results = []
        for _, row in df.iterrows():
            r = fraud_model.predict_one(row.to_dict())
            r["timestamp"] = datetime.utcnow().isoformat()+"Z"
            results.append(r)
        fc = sum(1 for r in results if r["is_fraud"])
        return {"total":len(results),"fraud_count":fc,"fraud_rate":round(fc/len(results),4),"predictions":results}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
def health():
    return {"status":"healthy","model_loaded":fraud_model.model is not None,
            "model_type":fraud_model.model_type,"threshold":fraud_model.threshold,
            "n_features":len(fraud_model.features) if fraud_model.features else 0,
            "timestamp":datetime.utcnow().isoformat()+"Z"}

@router.get("/metrics")
def metrics():
    mp = Path("models/metrics.json")
    if not mp.exists(): raise HTTPException(status_code=404, detail="metrics.json not found")
    with open(mp) as f: return json.load(f)