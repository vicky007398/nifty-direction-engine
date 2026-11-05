"""Bounded historical candle fetching with safe, non-sensitive diagnostics."""
from datetime import datetime, timedelta

def fetch_candles_chunked(client, token, start, end, chunk_days=3):
    if start >= end:
        return {"success": False, "failure_category": "INVALID_DATE_RANGE"}
    cursor = start
    combined = {}
    attempts = []
    while cursor < end:
        finish = min(cursor + timedelta(days=chunk_days), end)
        params = {
            "exchange": "NFO",
            "symboltoken": str(token),
            "interval": "ONE_MINUTE",
            "fromdate": cursor.strftime("%Y-%m-%d %H:%M"),
            "todate": finish.strftime("%Y-%m-%d %H:%M"),
        }
        try:
            response = client.getCandleData(params)
        except Exception as exc:
            # Only expose exception class, not message, headers, URLs, or credentials.
            attempts.append({"from": params["fromdate"], "to": params["todate"],
                             "status": "EXCEPTION", "exception_type": type(exc).__name__})
            return {"success": False, "failure_category": "CANDLE_REQUEST_ERROR",
                    "request_windows": attempts}
        if not isinstance(response, dict) or response.get("status") is False:
            code = response.get("errorcode") if isinstance(response, dict) else None
            safe_code = str(code) if str(code) in {"AG8001","AG8002","AG8003","AG8004","AG8005"} else None
            attempts.append({"from": params["fromdate"], "to": params["todate"],
                             "status": "API_REJECTED", "safe_error_code": safe_code})
            return {"success": False, "failure_category": "CANDLE_API_REJECTED",
                    "request_windows": attempts}
        data = response.get("data") or []
        if not isinstance(data, list):
            return {"success": False, "failure_category": "INVALID_CANDLE_FORMAT"}
        for item in data:
            if isinstance(item, (list, tuple)) and item:
                combined[str(item[0])] = item
        attempts.append({"from": params["fromdate"], "to": params["todate"],
                         "status": "OK", "bars": len(data)})
        cursor = finish
    return {"success": True, "data": [combined[key] for key in sorted(combined)],
            "request_windows": attempts}
