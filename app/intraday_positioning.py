"""Research-only intraday price/OI alignment; no trade recommendations."""
from datetime import datetime, time
from math import isfinite
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

def _dt(value):
    result = datetime.fromisoformat(str(value))
    return result.replace(tzinfo=IST) if result.tzinfo is None else result.astimezone(IST)

def intraday_positioning(candles, oi_rows, now):
    today = now.astimezone(IST).date()
    if not time(9, 18) <= now.astimezone(IST).time() < time(15, 45):
        return {"status": "OUTSIDE_INTRADAY_WINDOW"}
    sessions = {}
    for row in candles:
        if not isinstance(row, (list, tuple)) or len(row) < 5:
            continue
        try:
            stamp, close = _dt(row[0]), float(row[4])
            if isfinite(close) and close > 0 and time(9, 15) <= stamp.time() <= time(15, 29):
                sessions.setdefault(stamp.date(), []).append((stamp, close))
        except (ValueError, TypeError, OverflowError):
            continue
    prior_days = sorted(day for day in sessions if day < today)
    if not prior_days or today not in sessions:
        return {"status": "UNAVAILABLE", "reason": "MISSING_PRICE_SESSION"}
    previous_day = prior_days[-1]
    prior_prices = sorted(sessions[previous_day])
    if prior_prices[-1][0].time() < time(15, 29):
        return {"status": "UNAVAILABLE", "reason": "INCOMPLETE_PREVIOUS_CLOSE"}
    oi_by_day = {}
    for row in oi_rows:
        if not isinstance(row, dict) or "time" not in row or "oi" not in row:
            continue
        try:
            stamp, value = _dt(row["time"]), float(row["oi"])
            if isfinite(value) and value > 0 and stamp <= now:
                oi_by_day.setdefault(stamp.date(), []).append((stamp, value))
        except (ValueError, TypeError, OverflowError):
            continue
    if previous_day not in oi_by_day or today not in oi_by_day:
        return {"status": "UNAVAILABLE", "reason": "MISSING_OI_SESSION"}
    prev_oi_stamp, prev_oi = max(oi_by_day[previous_day])
    current_oi_stamp, current_oi = max(oi_by_day[today])
    if prev_oi_stamp.time() < time(15, 27):
        return {"status": "UNAVAILABLE", "reason": "INCOMPLETE_PREVIOUS_OI"}
    if (now - current_oi_stamp).total_seconds() > 600:
        return {"status": "UNAVAILABLE", "reason": "STALE_CURRENT_OI"}
    eligible = [(stamp, price) for stamp, price in sessions[today] if stamp <= current_oi_stamp]
    if not eligible:
        return {"status": "UNAVAILABLE", "reason": "NO_PRICE_AT_OI_TIME"}
    price_stamp, price = max(eligible)
    if (current_oi_stamp - price_stamp).total_seconds() > 240:
        return {"status": "UNAVAILABLE", "reason": "PRICE_OI_TIME_MISMATCH"}
    previous_close = prior_prices[-1][1]
    price_change_pct = 100 * (price / previous_close - 1)
    oi_change_pct = 100 * (current_oi / prev_oi - 1)
    if price_change_pct > 0 and oi_change_pct > 0:
        label = "LONG_BUILDUP"
    elif price_change_pct < 0 and oi_change_pct > 0:
        label = "SHORT_BUILDUP"
    elif price_change_pct > 0 and oi_change_pct < 0:
        label = "SHORT_COVERING"
    elif price_change_pct < 0 and oi_change_pct < 0:
        label = "LONG_UNWINDING"
    else:
        label = "INDETERMINATE"
    return {
        "status": "AVAILABLE", "comparison_type": "INTRADAY_VS_PREVIOUS_CLOSE",
        "previous_session": previous_day.isoformat(), "current_session": today.isoformat(),
        "previous_close_price": previous_close, "current_price": price,
        "price_timestamp": price_stamp.isoformat(),
        "previous_close_oi": prev_oi, "current_oi": current_oi,
        "oi_timestamp": current_oi_stamp.isoformat(),
        "price_change_pct": round(price_change_pct, 3),
        "oi_change_pct": round(oi_change_pct, 3),
        "classification": label, "direction_prediction": "NOT_TRAINED",
        "validated_for_trading": False,
    }
