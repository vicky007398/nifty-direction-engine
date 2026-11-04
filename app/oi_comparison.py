"""OI comparisons using exchange-timestamped Angel history. Research only."""
from datetime import datetime, time
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

def _parse_stamp(value):
    dt = datetime.fromisoformat(str(value))
    return dt.replace(tzinfo=IST) if dt.tzinfo is None else dt.astimezone(IST)

def oi_session_comparison(rows, as_of):
    """Compare last OI of most recent two sessions, never infer missing days."""
    sessions = {}
    for item in rows:
        if not isinstance(item, dict) or "time" not in item or "oi" not in item:
            continue
        try:
            dt = _parse_stamp(item["time"])
            oi = float(item["oi"])
            if oi < 0 or not (time(9,15) <= dt.time() <= time(15,45)):
                continue
            if dt.date() <= as_of.astimezone(IST).date():
                sessions.setdefault(dt.date(), []).append((dt, oi))
        except (ValueError, TypeError, OverflowError):
            continue
    dates = sorted(sessions)
    if len(dates) < 2:
        return {"status": "INSUFFICIENT_SESSIONS"}
    prior, latest = dates[-2:]
    old = max(sessions[prior])[1]
    new = max(sessions[latest])[1]
    if old <= 0:
        return {"status": "INVALID_PREVIOUS_OI"}
    return {
        "status": "AVAILABLE",
        "previous_session": prior.isoformat(),
        "latest_session": latest.isoformat(),
        "previous_close_oi": old,
        "latest_close_oi": new,
        "oi_change": new-old,
        "oi_change_pct": round(100*(new-old)/old, 3),
        "note": "Raw OI comparison; requires contract continuity and timestamp validation.",
    }
