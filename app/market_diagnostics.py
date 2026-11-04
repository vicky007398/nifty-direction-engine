"""On-demand, read-only NIFTY futures quote diagnostic."""
from datetime import datetime
from zoneinfo import ZoneInfo
from app.instruments import load_master, nifty_futures_contracts
from app.auth import connect_from_environment, AngelAuthenticationError

def check_futures_quote():
    stage = "INSTRUMENT_MASTER"
    try:
        contracts = nifty_futures_contracts(load_master(), datetime.now(ZoneInfo("Asia/Kolkata")).date())
    except Exception:
        return {"success": False, "stage": stage, "failure_category": "MASTER_UNAVAILABLE"}
    if not contracts:
        return {"success": False, "stage": stage, "failure_category": "NO_ACTIVE_CONTRACT"}
    contract = contracts[0]
    stage = "ANGEL_AUTH"
    try:
        client = connect_from_environment()
    except AngelAuthenticationError as exc:
        return {"success": False, "stage": stage, "failure_category": exc.category}
    except Exception:
        return {"success": False, "stage": stage, "failure_category": "AUTH_UNKNOWN_ERROR"}
    try:
        stage = "MARKET_DATA"
        result = client.getMarketData("FULL", {"NFO": [str(contract["token"])]})
        if not isinstance(result, dict) or result.get("status") is False:
            return {"success": False, "stage": stage, "failure_category": "QUOTE_REJECTED"}
        fetched = (result.get("data") or {}).get("fetched") or []
        if not fetched:
            return {"success": False, "stage": stage, "failure_category": "EMPTY_QUOTE"}
        quote = fetched[0]
        # Broker values may be scaled; report raw values without assuming units.
        fields = ("ltp", "tradeVolume", "opnInterest", "openInterest", "netChange", "percentChange")
        return {
            "success": True,
            "symbol": contract["symbol"],
            "expiry": contract["expiry_date"],
            "exchange": "NFO",
            "data_source": "ANGEL_FULL_QUOTE",
            "raw_quote_fields": {name: quote.get(name) for name in fields},
            "field_names": sorted(str(k) for k in quote.keys()),
            "note": "Raw broker fields only; verify price scale, OI availability and exchange timestamps before calculations.",
        }
    except Exception:
        return {"success": False, "stage": stage, "failure_category": "QUOTE_EXCEPTION"}
    finally:
        try:
            client.terminateSession(__import__("os").environ["ANGEL_CLIENT_CODE"])
        except Exception:
            pass
