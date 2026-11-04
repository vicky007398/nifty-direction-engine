from dataclasses import dataclass
from enum import Enum

class Direction(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    SIDEWAYS = "SIDEWAYS"

@dataclass(frozen=True)
class Participation:
    rvol: float
    oi_change_pct: float
    price_change_pct: float
    strength: str
    regime: str

def classify_participation(rvol: float, oi_change_pct: float, price_change_pct: float) -> Participation:
    """Exploratory labels only; NOT validated trading signals."""
    if rvol < 0 or not all(map(lambda x: abs(x) < float("inf"), [rvol, oi_change_pct, price_change_pct])):
        raise ValueError("Inputs must be finite and RVOL nonnegative")
    oi = abs(oi_change_pct)
    strength = ("STRONG" if rvol >= 1.5 and oi >= 5 else
                "ELEVATED" if rvol >= 1.2 and oi >= 2 else
                "WEAK" if rvol < 0.8 and oi < 2 else "MIXED")
    if price_change_pct > 0.15 and oi_change_pct > 1:
        regime = "POSSIBLE_LONG_BUILDUP"
    elif price_change_pct < -0.15 and oi_change_pct > 1:
        regime = "POSSIBLE_SHORT_BUILDUP"
    elif price_change_pct > 0.15 and oi_change_pct < -1:
        regime = "POSSIBLE_SHORT_COVERING"
    elif price_change_pct < -0.15 and oi_change_pct < -1:
        regime = "POSSIBLE_LONG_UNWINDING"
    else:
        regime = "UNCLEAR"
    return Participation(rvol, oi_change_pct, price_change_pct, strength, regime)

def cumulative_rvol(current_cumulative_volume: float, historical_same_time_volumes: list[float]) -> float:
    """Compare volume to prior sessions at the same clock time and same contract basis."""
    if current_cumulative_volume < 0 or not historical_same_time_volumes:
        raise ValueError("Invalid volume or missing historical baseline")
    if any(v < 0 for v in historical_same_time_volumes):
        raise ValueError("Negative historical volume")
    baseline = sum(historical_same_time_volumes) / len(historical_same_time_volumes)
    if baseline <= 0:
        raise ValueError("Zero historical baseline")
    return current_cumulative_volume / baseline
