from stock_monitor import parse_13f_position


def test_13f_position_change_is_normalized():
    event = parse_13f_position({"entity": "Fund", "ticker": "AAPL", "action": "BUY", "value_usd": 500000})
    assert event is not None
    assert event.action == "BUY"
    assert event.chain == "public-disclosure"


def test_invalid_stock_direction_becomes_unknown():
    event = parse_13f_position({"entity": "Fund", "ticker": "AAPL", "action": "EXECUTED"})
    assert event is not None
    assert event.action == "UNKNOWN"
