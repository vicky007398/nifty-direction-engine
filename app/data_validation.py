"""Read-only market data consistency diagnostics. Never issue trade signals."""
from datetime import datetime, time, timedelta
from math import isfinite
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

def market_cutoff(now):
    local = now.astimezone(IST)
    if local.time() < time(9, 16):
        return None
    if local.time() >= time(15, 30):
        return time(15, 29)
    return (local.replace(second=0, microsecond=0) - timedelta(minutes=1)).time()

def oi_sample(rows):
    if not isinstance(rows, list):
        return {"status": "INVALID_FORMAT"}
    records = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        date_field = next((k for k in ("time", "timestamp", "date", "datetime") if k in item), None)
        oi_field = next((k for k in ("oi", "openInterest", "opnInterest") if k in item), None)
        if date_field and oi_field:
            try:
                value = float(item[oi_field])
                if isfinite(value) and value >= 0:
                    records.append({"timestamp": str(item[date_field]), "oi": value})
            except (ValueError, TypeError):
                pass
    return {
        "status": "PARSED" if records else "UNRECOGNIZED_SCHEMA",
        "record_count": len(rows),
        "field_names": sorted(str(k) for k in rows[0].keys()) if rows and isinstance(rows[0], dict) else [],
        "first": records[0] if records else None,
        "last": records[-1] if records else None,
    }

def volume_consistency(quote_volume, candle_volume):
    try:
        q, c = float(quote_volume), float(candle_volume)
        if not all(isfinite(x) for x in (q, c)) or q < 0 or c <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return {"status": "NOT_COMPARABLE"}
    ratio = q / c
    return {
        "status": "UNVERIFIED_UNITS",
        "quote_to_candle_ratio": round(ratio, 4),
        "possible_lot_size_factor": round(ratio),
        "note": "A numerical ratio does not establish units. Confirm contract lot size and timestamp alignment.",
    }
