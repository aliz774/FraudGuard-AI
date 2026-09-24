# ═══════════════════════════════════════════════════════════════════
# FILE 1: backend/main.py
# Run: uvicorn main:app --reload --host 0.0.0.0 --port 8000
# ═══════════════════════════════════════════════════════════════════

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from model_service import fraud_model
from routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    fraud_model.load()
    print("[OK] Model loaded and ready")
    yield
    print("[INFO] Shutting down")

app = FastAPI(
    title="FraudGuard AI",
    description="Real-time fraud detection API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router, prefix="/api/v1")

@app.get("/")
def root():
    return {"status":"healthy","model":"LightGBM","version":"1.0.0"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
