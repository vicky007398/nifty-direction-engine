# NIFTY Direction Engine

Research-first, low-latency NIFTY intraday direction platform (15/30/60 minutes).

## Status
**Stage 1 scaffold only. No trained model, live feed, or validated directional predictions yet. No trading orders.**

## Quick start
```bash
python -m venv .venv
pip install -r requirements.txt
uvicorn app.main:app --reload
pytest -q
```
Open http://127.0.0.1:8000/docs

## Planned milestones
1. Audit SmartAPI availability, entitlements, rate limits and historical retention.
2. Implement authenticated collector, instrument master, futures expiry mapping, WebSocket and REST gap recovery.
3. Persist timestamped 1-minute Spot/Futures bars and OI snapshots in PostgreSQL.
4. Compute same-time RVOL, contract-consistent OI, basis, VWAP and volatility features.
5. Walk-forward backtest UP/DOWN/SIDEWAYS outcomes for 15/30/60 minutes.
6. Deploy calibrated models and live dashboard, with stale-feed suppression and paper-trading logs.

## Security
Put Angel credentials in environment variables only; never commit .env or TOTP secret.

## Important
High volume or OI does not guarantee direction. Research heuristics are deliberately marked unvalidated. Historical expired-contract OI availability must be verified before relying on it.
