"""Contract discovery. Never hardcode NIFTY futures tokens across expiries."""
from datetime import datetime, date
import requests

MASTER_URL = "https://margincalculator.angelone.in/OpenAPI_File/files/OpenAPIScripMaster.json"

def nifty_futures_contracts(master: list[dict], as_of: date | None = None) -> list[dict]:
    today = as_of or date.today()
    contracts = []
    for instrument in master:
        if instrument.get("exch_seg") != "NFO" or instrument.get("name", "").upper() != "NIFTY":
            continue
        symbol = str(instrument.get("symbol", "")).upper()
        if not symbol.endswith("FUT"):
            continue
        try:
            expiry = datetime.strptime(instrument["expiry"], "%d%b%Y").date()
        except (ValueError, KeyError, TypeError):
            continue
        if expiry >= today:
            contracts.append({**instrument, "expiry_date": expiry.isoformat()})
    return sorted(contracts, key=lambda x: x["expiry_date"])

def load_master(timeout: int = 15) -> list[dict]:
    response = requests.get(MASTER_URL, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list):
        raise ValueError("Unexpected instrument master format")
    return data
