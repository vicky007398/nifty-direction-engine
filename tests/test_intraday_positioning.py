from datetime import datetime
from zoneinfo import ZoneInfo
from app.intraday_positioning import intraday_positioning

IST = ZoneInfo("Asia/Kolkata")

def test_short_covering_intraday():
    candles = [
        ["2026-11-04T15:29:00+05:30", 1, 1, 1, 100, 10],
        ["2026-11-05T10:54:00+05:30", 1, 1, 1, 102, 10],
    ]
    oi = [
        {"time": "2026-11-04T15:39:00+05:30", "oi": 1000},
        {"time": "2026-11-05T10:54:00+05:30", "oi": 900},
    ]
    result = intraday_positioning(candles, oi, datetime(2026, 11, 5, 10, 57, tzinfo=IST))
    assert result["classification"] == "SHORT_COVERING"
    assert result["validated_for_trading"] is False

def test_stale_oi_rejected():
    candles = [
        ["2026-11-04T15:29:00+05:30", 1, 1, 1, 100, 10],
        ["2026-11-05T10:54:00+05:30", 1, 1, 1, 102, 10],
    ]
    oi = [
        {"time": "2026-11-04T15:39:00+05:30", "oi": 1000},
        {"time": "2026-11-05T10:54:00+05:30", "oi": 900},
    ]
    result = intraday_positioning(candles, oi, datetime(2026, 11, 5, 11, 20, tzinfo=IST))
    assert result["reason"] == "STALE_CURRENT_OI"
