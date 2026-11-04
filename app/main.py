from fastapi import FastAPI, Header
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

@app.get("/diagnostics/config")
def config_diagnostics():
    """Public safe configuration check; never returns values or authenticates."""
    import os
    required = ("ANGEL_API_KEY", "ANGEL_CLIENT_CODE", "ANGEL_PIN", "ANGEL_TOTP_SECRET")
    configured = all(bool(os.getenv(name, "").strip()) for name in required)
    return {
        "angel_environment": "CONFIGURED" if configured else "INCOMPLETE",
        "angel_authenticated": "NOT_TESTED",
        "market_data": "NOT_TESTED",
        "model": "NOT_TRAINED",
    }

@app.get("/diagnostics/angel")
def angel_diagnostics(x_diagnostic_key: str | None = Header(default=None)):
    """Protected, on-demand Angel login check. Never returns credentials or tokens."""
    import os
    import secrets
    from fastapi import HTTPException
    configured_key = os.getenv("DIAGNOSTIC_KEY", "").strip()
    if not configured_key or not x_diagnostic_key or not secrets.compare_digest(
        x_diagnostic_key, configured_key
    ):
        raise HTTPException(status_code=404, detail="Not Found")
    from app.auth import connect_from_environment
    try:
        client = connect_from_environment()
    except Exception as exc:
        from app.auth import AngelAuthenticationError
        category = exc.category if isinstance(exc, AngelAuthenticationError) else "UNKNOWN_ERROR"
        return {"angel_authenticated": False, "failure_category": category, "market_data": "NOT_TESTED"}
    finally:
        # Do not log sensitive SDK responses or access tokens.
        pass
    try:
        client.terminateSession(os.environ["ANGEL_CLIENT_CODE"])
    except Exception:
        pass
    return {"angel_authenticated": True, "market_data": "NOT_TESTED"}

@app.get("/diagnostics/nifty-futures")
def nifty_futures_diagnostics(x_diagnostic_key: str | None = Header(default=None)):
    """Protected, read-only quote check; no order placement."""
    import os
    import secrets
    from fastapi import HTTPException
    expected = os.getenv("DIAGNOSTIC_KEY", "").strip()
    if not expected or not x_diagnostic_key or not secrets.compare_digest(x_diagnostic_key, expected):
        raise HTTPException(status_code=404, detail="Not Found")
    from app.market_diagnostics import check_futures_quote
    return check_futures_quote()
