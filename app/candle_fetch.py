"""Historical candle fetching with conservative rate limiting and safe diagnostics."""
from datetime import timedelta
import time

def _request(client, token, start, end):
    params = {"exchange": "NFO", "symboltoken": str(token), "interval": "ONE_MINUTE",
              "fromdate": start.strftime("%Y-%m-%d %H:%M"),
              "todate": end.strftime("%Y-%m-%d %H:%M")}
    for attempt in range(2):
        try:
            response = client.getCandleData(params)
        except Exception as exc:
            if attempt == 0 and type(exc).__name__ in {"DataException", "Timeout", "TimeoutError", "ConnectionError"}:
                time.sleep(2)
                continue
            return {"success": False, "category": "CANDLE_REQUEST_ERROR",
                    "exception_type": type(exc).__name__}
        if not isinstance(response, dict) or response.get("status") is False:
            return {"success": False, "category": "CANDLE_API_REJECTED"}
        rows = response.get("data") or []
        if not isinstance(rows, list):
            return {"success": False, "category": "INVALID_CANDLE_FORMAT"}
        return {"success": True, "data": rows}
    return {"success": False, "category": "CANDLE_REQUEST_ERROR"}

def fetch_candles_chunked(client, token, start, end, chunk_days=3):
    if start >= end:
        return {"success": False, "failure_category": "INVALID_DATE_RANGE"}
    combined, windows = {}, []
    cursor = start
    while cursor < end:
        finish = min(cursor + timedelta(days=chunk_days), end)
        # All requests use valid NSE session clock times; never use the current clock
        # on the first historical date (which previously started at 10:25).
        begin = cursor.replace(hour=9, minute=15, second=0, microsecond=0)
        stop = finish.replace(hour=15, minute=29, second=0, microsecond=0)
        if finish.date() == end.date():
            stop = min(stop, end.replace(second=0, microsecond=0))
        result = _request(client, token, begin, stop)
        detail = {"from": begin.strftime("%Y-%m-%d %H:%M"),
                  "to": stop.strftime("%Y-%m-%d %H:%M")}
        if not result["success"]:
            detail.update({"status": "FAILED", "exception_type": result.get("exception_type")})
            windows.append(detail)
            return {"success": False, "failure_category": result["category"],
                    "request_windows": windows}
        for row in result["data"]:
            if isinstance(row, (list, tuple)) and row:
                combined[str(row[0])] = row
        detail.update({"status": "OK", "bars": len(result["data"])})
        windows.append(detail)
        cursor = finish + timedelta(days=1)
        if cursor < end:
            time.sleep(1)
    return {"success": True, "data": [combined[k] for k in sorted(combined)],
            "request_windows": windows}
