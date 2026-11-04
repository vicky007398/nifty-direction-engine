import pytest
from app.analytics import classify_participation, cumulative_rvol

def test_rvol():
    assert cumulative_rvol(150, [100, 100, 100]) == 1.5

def test_strong_bearish_is_not_bullish():
    result = classify_participation(1.8, 7, -0.8)
    assert result.strength == "STRONG"
    assert result.regime == "POSSIBLE_SHORT_BUILDUP"

def test_zero_baseline():
    with pytest.raises(ValueError):
        cumulative_rvol(10, [0, 0])
