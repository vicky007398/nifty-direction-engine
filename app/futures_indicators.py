"""Research-only NIFTY futures indicators. No trading signals."""
from math import isfinite

def _number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return float(value)

def calculate_futures_indicators(
    current_cumulative_volume: float,
    previous_same_time_volumes: list[float],
    current_oi: float,
    previous_close_oi: float,
    current_price: float,
    previous_close_price: float,
):
    volume = _number(current_cumulative_volume, "current_cumulative_volume")
    oi = _number(current_oi, "current_oi")
    prior_oi = _number(previous_close_oi, "previous_close_oi")
    price = _number(current_price, "current_price")
    prior_price = _number(previous_close_price, "previous_close_price")
    baseline = [_number(v, "previous_same_time_volume") for v in previous_same_time_volumes]
    if min(volume, oi, prior_oi, price, prior_price) < 0 or any(v < 0 for v in baseline):
        raise ValueError("Volumes, OI, and prices cannot be negative")
    if not baseline or sum(baseline) == 0 or prior_oi == 0 or prior_price == 0:
        raise ValueError("Nonzero historical volume, previous OI and previous price are required")
    rvol = volume / (sum(baseline) / len(baseline))
    oi_change_pct = (oi / prior_oi - 1) * 100
    price_change_pct = (price / prior_price - 1) * 100
    if oi_change_pct > 0 and price_change_pct > 0:
        classification = "LONG_BUILDUP"
    elif oi_change_pct > 0 and price_change_pct < 0:
        classification = "SHORT_BUILDUP"
    elif oi_change_pct < 0 and price_change_pct > 0:
        classification = "SHORT_COVERING"
    elif oi_change_pct < 0 and price_change_pct < 0:
        classification = "LONG_UNWINDING"
    else:
        classification = "INDETERMINATE"
    return {
        "rvol": round(rvol, 3),
        "oi_change_pct": round(oi_change_pct, 3),
        "price_change_pct": round(price_change_pct, 3),
        "classification": classification,
        "baseline_sessions": len(baseline),
        "direction_prediction": "NOT_TRAINED",
        "validated": False,
    }
