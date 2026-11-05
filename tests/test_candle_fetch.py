from datetime import datetime
from app.candle_fetch import fetch_candles_chunked

class FakeClient:
    def __init__(self):
        self.calls = []
    def getCandleData(self, params):
        self.calls.append(params)
        return {"status": True, "data": [[params["fromdate"], 1, 2, 1, 2, 10]]}

class FailingClient:
    def getCandleData(self, params):
        raise TimeoutError("private details must never be returned")

def test_chunking_and_deduplication():
    client = FakeClient()
    result = fetch_candles_chunked(client, "123", datetime(2026, 11, 1), datetime(2026, 11, 9))
    assert result["success"] is True
    assert len(client.calls) == 3
    assert len(result["data"]) == 3

def test_safe_error():
    result = fetch_candles_chunked(FailingClient(), "123", datetime(2026, 11, 1), datetime(2026, 11, 2))
    assert result["failure_category"] == "CANDLE_REQUEST_ERROR"
    assert result["request_windows"][0]["exception_type"] == "TimeoutError"
    assert "private details" not in str(result)
