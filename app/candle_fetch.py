"""Resilient read-only candle collection. Missing sessions are never silently accepted."""
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
            if attempt == 0:
                time.sleep(2)
                continue
            return {"success": False, "category": "CANDLE_REQUEST_ERROR",
                    "exception_type": type(exc).__name__}
        if not isinstance(response, dict) or response.get("status") is False:
            if attempt == 0:
                time.sleep(2)
                continue
            return {"success": False, "category": "CANDLE_API_REJECTED"}
        rows = response.get("data") or []
        if not isinstance(rows, list):
            return {"success": False, "category": "INVALID_CANDLE_FORMAT"}
        return {"success": True, "data": rows}
    return {"success": False, "category": "CANDLE_REQUEST_ERROR"}

def fetch_candles_chunked(client, token, start, end, chunk_days=3):
    if start >= end:
        return {"success": False, "failure_category": "INVALID_DATE_RANGE"}
    combined, windows, failures = {}, [], []
    day = start.date()
    while day <= end.date():
        begin = start.replace(year=day.year, month=day.month, day=day.day,
                              hour=9, minute=15, second=0, microsecond=0)
        stop = begin.replace(hour=15, minute=29)
        if day == end.date():
            stop = min(stop, end.replace(second=0, microsecond=0))
        if stop < begin:
            day += timedelta(days=1)
            continue
        # Query individual days to avoid SDK DataException on multi-day windows.
        result = _request(client, token, begin, stop)
        detail = {"from": begin.strftime("%Y-%m-%d %H:%M"),
                  "to": stop.strftime("%Y-%m-%d %H:%M")}
        if result["success"]:
            for row in result["data"]:
                if isinstance(row, (list, tuple)) and row:
                    combined[str(row[0])] = row
            detail.update({"status": "OK", "bars": len(result["data"])})
        else:
            detail.update({"status": "FAILED", "exception_type": result.get("exception_type")})
            failures.append(day.isoformat())
        windows.append(detail)
        day += timedelta(days=1)
        if day <= end.date():
            time.sleep(1)
    return {"success": not failures and bool(combined),
            "partial_data": bool(failures) and bool(combined),
            "failure_category": "PARTIAL_CANDLE_HISTORY" if failures else ("EMPTY_CANDLE_HISTORY" if not combined else None),
            "failed_dates": failures,
            "data": [combined[k] for k in sorted(combined)],
            "request_windows": windows}
