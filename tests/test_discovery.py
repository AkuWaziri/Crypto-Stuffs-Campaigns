from discovery import parse_trader_candidates, select_smart_money


def test_parse_trader_candidates():
    payload = {
        "traders": [
            {"wallet": "WalletA", "name": "Trader A", "roi": 125.5, "winRate": 68.0},
            {"wallet": "WalletB", "roi": 20.0},
        ]
    }
    result = parse_trader_candidates(payload, source="test")
    assert result[0].wallet == "WalletA"
    assert result[0].roi_pct == 125.5
    assert result[0].label == "Trader A"


def test_select_smart_money_uses_roi():
    candidates = parse_trader_candidates(
        [
            {"address": "Winner", "roi": 100, "win_rate": 70},
            {"address": "Loser", "roi": 10, "win_rate": 90},
        ]
    )
    result = select_smart_money(candidates, min_roi_pct=50)
    assert [item.wallet for item in result] == ["Winner"]


def test_missing_roi_is_not_smart_money():
    candidates = parse_trader_candidates([{"address": "Unknown"}])
    assert select_smart_money(candidates) == []
