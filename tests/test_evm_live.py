from evm_live import _parse_trade


def test_bitquery_trading_trade_uses_actual_trader_and_token_address():
    row = {
        "Block": {"Time": "2026-09-14T18:00:00Z"},
        "Side": "Buy",
        "Trader": {"Address": "0xABC123"},
        "Amounts": {"Base": "425000", "Quote": "425500"},
        "AmountsInUsd": {"Base": "425000", "Quote": "425500"},
        "Pair": {
            "Token": {"Symbol": "TOKEN", "Id": "0xtoken"},
            "QuoteToken": {"Symbol": "USDC", "Id": "0xusdc"},
            "Market": {"Network": "Ethereum", "Protocol": "Uniswap"},
        },
        "TransactionHeader": {"Hash": "0xHASH"},
    }

    event = _parse_trade(row, "eth")

    assert event is not None
    assert event.entity == "0xABC123"
    assert event.action == "BUY"
    assert event.asset == "TOKEN"
    assert event.asset_address == "0xtoken"
    assert event.value_usd == 425500
    assert event.chain == "eth"
    assert event.tx_or_reference == "0xHASH"
    assert event.source == "bitquery_trading"
    assert "https://etherscan.io/tx/0xHASH" in event.evidence


def test_unknown_trader_side_is_not_reported_as_trade():
    row = {
        "Block": {"Time": "2026-09-14T18:00:00Z"},
        "Side": "Unknown",
        "Trader": {"Address": "0xABC123"},
        "AmountsInUsd": {"Quote": "425500"},
        "Pair": {"Token": {"Symbol": "TOKEN"}},
        "TransactionHeader": {"Hash": "0xHASH"},
    }

    assert _parse_trade(row, "eth") is None
