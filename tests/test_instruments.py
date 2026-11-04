from datetime import date
from app.instruments import nifty_futures_contracts

def test_selects_only_unexpired_nifty_futures():
    master = [
        {"exch_seg":"NFO","name":"NIFTY","symbol":"NIFTY26NOVFUT","expiry":"26NOV2026","token":"1"},
        {"exch_seg":"NFO","name":"NIFTY","symbol":"NIFTY26OCTFUT","expiry":"29OCT2026","token":"2"},
        {"exch_seg":"NFO","name":"BANKNIFTY","symbol":"BANKNIFTY26NOVFUT","expiry":"26NOV2026","token":"3"},
    ]
    found = nifty_futures_contracts(master, date(2026,11,4))
    assert len(found) == 1
    assert found[0]["token"] == "1"
