"""Research-only aligned session-close price/OI positioning."""
from datetime import datetime, time
from math import isfinite
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

def _stamp(raw):
    dt = datetime.fromisoformat(str(raw))
    return dt.replace(tzinfo=IST) if dt.tzinfo is None else dt.astimezone(IST)

def classify_close_positioning(candles, oi_result):
    if oi_result.get("status") != "AVAILABLE":
        return {"status": "UNAVAILABLE", "reason": "OI_COMPARISON_MISSING"}
    previous = oi_result["previous_session"]
    latest = oi_result["latest_session"]
    closes = {}
    for row in candles:
        if not isinstance(row, (list, tuple)) or len(row) < 5:
            continue
        try:
            stamp = _stamp(row[0])
            price = float(row[4])
            if not isfinite(price) or price <= 0 or not time(9, 15) <= stamp.time() <= time(15, 29):
                continue
            day = stamp.date().isoformat()
            if day in (previous, latest) and (day not in closes or stamp > closes[day][0]):
                closes[day] = (stamp, price)
        except (ValueError, TypeError, OverflowError):
            continue
    if previous not in closes or latest not in closes:
        return {"status": "UNAVAILABLE", "reason": "MISSING_SESSION_PRICE"}
    prev_stamp, prev_price = closes[previous]
    last_stamp, last_price = closes[latest]
    if prev_stamp.time() < time(15, 29) or last_stamp.time() < time(15, 29):
        return {"status": "UNAVAILABLE", "reason": "INCOMPLETE_SESSION_PRICE"}
    price_pct = (last_price / prev_price - 1) * 100
    oi_pct = float(oi_result["oi_change_pct"])
    if price_pct > 0 and oi_pct > 0:
        label = "LONG_BUILDUP"
    elif price_pct < 0 and oi_pct > 0:
        label = "SHORT_BUILDUP"
    elif price_pct > 0 and oi_pct < 0:
        label = "SHORT_COVERING"
    elif price_pct < 0 and oi_pct < 0:
        label = "LONG_UNWINDING"
    else:
        label = "INDETERMINATE"
    return {
        "status": "AVAILABLE",
        "previous_session": previous, "latest_session": latest,
        "previous_price": prev_price, "latest_price": last_price,
        "previous_price_time": prev_stamp.isoformat(),
        "latest_price_time": last_stamp.isoformat(),
        "price_change_pct": round(price_pct, 3),
        "oi_change_pct": oi_pct,
        "classification": label,
        "direction_prediction": "NOT_TRAINED",
        "note": "Heuristic only; historical OI last print can be later than last regular-session price bar.",
    }
