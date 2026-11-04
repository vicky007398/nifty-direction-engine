from fastapi import FastAPI
from pydantic import BaseModel, Field
from app.analytics import classify_participation

app = FastAPI(title="NIFTY Direction Engine", version="0.1.0")

class ParticipationRequest(BaseModel):
    rvol: float = Field(ge=0)
    oi_change_pct: float
    price_change_pct: float

@app.get("/health")
def health():
    return {"status": "ok", "model": "NOT_TRAINED", "trading_enabled": False}

@app.post("/research/participation")
def participation(payload: ParticipationRequest):
    return {**classify_participation(**payload.model_dump()).__dict__,
            "direction": "UNAVAILABLE", "validated": False,
            "note": "Research heuristic only; not an options trade recommendation"}
