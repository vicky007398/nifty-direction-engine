"""Angel One historical candle adapter. Never log credentials or tokens."""
from datetime import datetime
from typing import Any

def fetch_candles(client: Any, exchange: str, token: str, interval: str,
                  start: datetime, end: datetime) -> list[dict]:
    """Caller must use authenticated SmartConnect and API-compliant date windows."""
    if start >= end:
        raise ValueError("start must precede end")
    result = client.getCandleData({
        "exchange": exchange, "symboltoken": token, "interval": interval,
        "fromdate": start.strftime("%Y-%m-%d %H:%M"),
        "todate": end.strftime("%Y-%m-%d %H:%M"),
    })
    if not isinstance(result, dict) or not result.get("status"):
        raise RuntimeError("Angel candle request failed; inspect API status securely")
    columns = ["timestamp", "open", "high", "low", "close", "volume"]
    return [dict(zip(columns, row)) for row in (result.get("data") or [])]
