from datetime import datetime
from app.candle_fetch import fetch_candles_chunked

class WeekdayClient:
    def __init__(self):
        self.calls = []
    def getCandleData(self, params):
        self.calls.append(params)
        return {"status": True, "data": [[params["fromdate"], 1, 1, 1, 1, 10]]}

def test_weekend_skipped():
    client = WeekdayClient()
    result = fetch_candles_chunked(client, "123", datetime(2026, 10, 24, 10), datetime(2026, 10, 27, 10))
    assert result["success"]
    assert len(client.calls) == 2
    assert len([w for w in result["request_windows"] if w["status"] == "SKIPPED_WEEKEND"]) == 2
