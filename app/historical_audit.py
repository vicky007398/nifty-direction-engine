"""On-demand historical futures baseline audit. No persistence or orders."""
from collections import defaultdict
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from app.auth import connect_from_environment, AngelAuthenticationError
from app.instruments import load_master, nifty_futures_contracts
from app.data_validation import market_cutoff, oi_sample, volume_consistency
from app.oi_comparison import oi_session_comparison
from app.positioning import classify_close_positioning
from app.candle_fetch import fetch_candles_chunked

IST = ZoneInfo("Asia/Kolkata")

def _parse_candles(rows):
    grouped = defaultdict(list)
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) < 6:
            continue
        try:
            stamp = datetime.fromisoformat(str(row[0]))
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=IST)
            stamp = stamp.astimezone(IST)
            volume = float(row[5])
        except (ValueError, TypeError):
            continue
        if time(9,15) <= stamp.time().replace(tzinfo=None) <= time(15,29) and volume >= 0:
            grouped[stamp.date()].append((stamp, volume, float(row[4])))
    return {day: sorted(items) for day, items in grouped.items()}

def _baseline(rows, now):
    sessions = _parse_candles(rows)
    # Use only the last completed minute; avoid partial current minute.
    cutoff_time = market_cutoff(now)
    if cutoff_time is None:
        return {'rvol_status': 'OUTSIDE_COMPARABLE_WINDOW', 'historical_rvol': None, 'comparison_time_ist': None}
    cutoff = datetime.combine(now.date(), cutoff_time, tzinfo=IST)
    historical = []
    for day, candles in sorted(sessions.items()):
        if day >= now.date():
            continue
        upto = [c for c in candles if c[0].time().replace(tzinfo=None) <= cutoff_time]
        if upto:
            historical.append({"date": day.isoformat(), "volume": int(sum(x[1] for x in upto)), "bars": len(upto)})
    historical = historical[-5:]
    current = [c for c in sessions.get(now.date(), []) if c[0] <= cutoff]
    baseline = sum(x["volume"] for x in historical) / len(historical) if historical else None
    current_volume = sum(x[1] for x in current) if current else None
    return {
        "comparison_time_ist": cutoff_time.strftime("%H:%M"),
        "historical_sessions": historical,
        "current_completed_bar_volume": int(current_volume) if current_volume is not None else None,
        "historical_average_volume": round(baseline, 2) if baseline else None,
        "historical_rvol": round(current_volume / baseline, 3) if baseline and current_volume is not None else None,
        "rvol_status": "AVAILABLE" if baseline and current_volume is not None and len(historical) >= 3 else "INSUFFICIENT_BASELINE",
    }

def audit_historical():
    now = datetime.now(IST)
    try:
        contracts = nifty_futures_contracts(load_master(), now.date())
    except Exception:
        return {"success": False, "failure_category": "MASTER_UNAVAILABLE"}
    if not contracts:
        return {"success": False, "failure_category": "NO_ACTIVE_CONTRACT"}
    contract = contracts[0]
    try:
        client = connect_from_environment()
    except AngelAuthenticationError as exc:
        return {"success": False, "failure_category": exc.category}
    try:
        start_time = now - timedelta(days=12)
        candle_result = fetch_candles_chunked(
            client, contract["token"], start_time, now, chunk_days=3
        )
        if not candle_result["success"]:
            return {"success": False, "stage": "CANDLES",
                    "failure_category": candle_result["failure_category"],
                    "request_windows": candle_result.get("request_windows", [])}
        candles = candle_result["data"]
        params = {"exchange": "NFO", "symboltoken": str(contract["token"]),
                  "interval": "THREE_MINUTE",
                  "fromdate": start_time.strftime("%Y-%m-%d %H:%M"),
                  "todate": now.strftime("%Y-%m-%d %H:%M")}
        summary = _baseline(candles, now)
        # Angel historical OI availability must be checked independently.
        oi_status = "UNAVAILABLE"
        oi_points = 0
        oi_inspection = {'status': 'NOT_TESTED'}
        oi_comparison = {'status': 'NOT_TESTED'}
        try:
            if hasattr(client, "getOIData"):
                oi_result = client.getOIData({**params, "interval": "THREE_MINUTE"})
                if isinstance(oi_result, dict) and oi_result.get("status") is not False:
                    oi_rows = oi_result.get("data") or []
                    if isinstance(oi_rows, list):
                        oi_points = len(oi_rows)
                        oi_status = "AVAILABLE" if oi_points else "EMPTY"
                        oi_inspection = oi_sample(oi_rows)
                        oi_comparison = oi_session_comparison(oi_rows, now)
                else:
                    oi_status = "API_REJECTED"
            else:
                oi_status = "SDK_METHOD_MISSING"
        except Exception:
            oi_status = "REQUEST_ERROR"
        quote_check = {"status": "NOT_TESTED"}
        try:
            quote_response = client.getMarketData("FULL", {"NFO": [str(contract["token"])]})
            fetched = (quote_response.get("data") or {}).get("fetched") or [] if isinstance(quote_response, dict) else []
            if fetched:
                quote = fetched[0]
                quote_check = volume_consistency(quote.get("tradeVolume"), summary.get("current_completed_bar_volume"))
                quote_check["quote_exchange_feed_time"] = quote.get("exchFeedTime")
                quote_check["quote_exchange_trade_time"] = quote.get("exchTradeTime")
                quote_check["raw_quote_volume"] = quote.get("tradeVolume")
                quote_check["raw_quote_oi"] = quote.get("opnInterest")
        except Exception:
            quote_check = {"status": "QUOTE_CHECK_ERROR"}
        return {"success": True, "symbol": contract["symbol"],
                "expiry": contract["expiry_date"], "candle_count": len(candles),
                "candle_request_windows": candle_result["request_windows"],
                "historical_oi_status": oi_status, "historical_oi_points": oi_points,
                "historical_oi_inspection": oi_inspection, "historical_oi_comparison": oi_comparison,
                "session_positioning": classify_close_positioning(candles, oi_comparison),
                "volume_unit_check": quote_check,
                **summary,
                "warning": "Single-contract history only. No rollover-adjusted baseline; do not use for live signals yet."}
    finally:
        try:
            import os
            client.terminateSession(os.environ["ANGEL_CLIENT_CODE"])
        except Exception:
            pass
