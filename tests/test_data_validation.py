from datetime import datetime
from zoneinfo import ZoneInfo
from app.data_validation import market_cutoff, oi_sample, volume_consistency

IST = ZoneInfo("Asia/Kolkata")

def test_after_close_cutoff():
    assert market_cutoff(datetime(2026, 11, 4, 18, 16, tzinfo=IST)).strftime("%H:%M") == "15:29"

def test_during_market_cutoff():
    assert market_cutoff(datetime(2026, 11, 4, 10, 0, tzinfo=IST)).strftime("%H:%M") == "09:59"

def test_before_open_cutoff():
    assert market_cutoff(datetime(2026, 11, 4, 8, 0, tzinfo=IST)) is None

def test_oi_schema():
    result = oi_sample([{"time": "2026-11-04T15:27:00+05:30", "oi": 1234}])
    assert result["status"] == "PARSED"
    assert result["last"]["oi"] == 1234

def test_volume_mismatch_not_automatically_normalized():
    result = volume_consistency(4798495, 71522)
    assert result["status"] == "UNVERIFIED_UNITS"
