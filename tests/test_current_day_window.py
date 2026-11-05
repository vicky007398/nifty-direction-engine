from datetime import datetime
from app.candle_fetch import fetch_candles_chunked

class FakeClient:
    def __init__(self):
        self.calls = []
    def getCandleData(self, params):
        self.calls.append(params)
        return {"status": True, "data": [[params["fromdate"], 1, 2, 1, 2, 10]]}

def test_current_day_included_when_start_end_clock_same():
    client = FakeClient()
    result = fetch_candles_chunked(
        client, "123",
        datetime(2026, 10, 24, 10, 25),
        datetime(2026, 11, 5, 10, 25),
        chunk_days=3,
    )
    assert result["success"]
    assert any(x["from"].startswith("2026-11-05") for x in result["request_windows"])
    assert result["request_windows"][-1]["to"] == "2026-11-05 10:25"
