from app.positioning import classify_close_positioning

def test_short_covering():
    candles = [
        ["2026-11-03T15:29:00+05:30", 1, 1, 1, 100, 100],
        ["2026-11-04T15:29:00+05:30", 1, 1, 1, 110, 100],
    ]
    oi = {"status": "AVAILABLE", "previous_session": "2026-11-03", "latest_session": "2026-11-04", "oi_change_pct": -4.339}
    result = classify_close_positioning(candles, oi)
    assert result["classification"] == "SHORT_COVERING"
    assert result["price_change_pct"] == 10.0

def test_missing_close_is_not_classified():
    candles = [
        ["2026-11-03T15:29:00+05:30", 1, 1, 1, 100, 100],
        ["2026-11-04T15:10:00+05:30", 1, 1, 1, 110, 100],
    ]
    oi = {"status": "AVAILABLE", "previous_session": "2026-11-03", "latest_session": "2026-11-04", "oi_change_pct": -4.339}
    assert classify_close_positioning(candles, oi)["status"] == "UNAVAILABLE"
