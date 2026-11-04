from datetime import datetime
from zoneinfo import ZoneInfo
from app.oi_comparison import oi_session_comparison

IST = ZoneInfo("Asia/Kolkata")

def test_oi_change_uses_latest_two_sessions():
    rows = [
        {"time": "2026-11-02T15:39:00+05:30", "oi": 1000},
        {"time": "2026-11-03T15:39:00+05:30", "oi": 1100},
        {"time": "2026-11-04T15:39:00+05:30", "oi": 1210},
    ]
    result = oi_session_comparison(rows, datetime(2026, 11, 4, 18, tzinfo=IST))
    assert result["status"] == "AVAILABLE"
    assert result["oi_change_pct"] == 10.0
    assert result["previous_session"] == "2026-11-03"

def test_oi_requires_two_sessions():
    result = oi_session_comparison([{"time": "2026-11-04T15:39:00+05:30", "oi": 100}], datetime(2026, 11, 4, 18, tzinfo=IST))
    assert result["status"] == "INSUFFICIENT_SESSIONS"
