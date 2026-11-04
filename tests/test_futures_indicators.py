import pytest
from app.futures_indicators import calculate_futures_indicators

def test_long_buildup():
    r = calculate_futures_indicators(200, [100, 100], 1100, 1000, 110, 100)
    assert r["rvol"] == 2.0
    assert r["oi_change_pct"] == 10.0
    assert r["classification"] == "LONG_BUILDUP"
    assert r["validated"] is False

def test_short_buildup():
    r = calculate_futures_indicators(100, [100], 1100, 1000, 90, 100)
    assert r["classification"] == "SHORT_BUILDUP"

def test_zero_baseline_rejected():
    with pytest.raises(ValueError):
        calculate_futures_indicators(100, [0, 0], 1100, 1000, 110, 100)

def test_missing_history_rejected():
    with pytest.raises(ValueError):
        calculate_futures_indicators(100, [], 1100, 1000, 110, 100)

def test_no_change_indeterminate():
    r = calculate_futures_indicators(100, [100], 1000, 1000, 100, 100)
    assert r["classification"] == "INDETERMINATE"
