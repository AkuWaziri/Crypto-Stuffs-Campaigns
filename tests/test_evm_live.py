from evm_live import _parse_trade


def test_parse_large_evm_buy_includes_full_address():
    row = {
        "Block": {"Time": "2026-09-14T17:00:00Z"},
        "Transaction": {
            "From": "0x1111111111111111111111111111111111111111",
            "Hash": "0xabc",
        },
        "Trade": {
            "Sender": "0x1111111111111111111111111111111111111111",
            "Buy": {
                "Buyer": "0x1111111111111111111111111111111111111111",
                "AmountInUSD": "250000",
                "Currency": {
                    "Name": "Example Token",
                    "Symbol": "EXT",
                    "SmartContract": "0x2222222222222222222222222222222222222222",
                },
            },
            "Sell": {
                "Seller": "0x1111111111111111111111111111111111111111",
                "AmountInUSD": "250000",
                "Currency": {"Name": "USD Coin", "Symbol": "USDC"},
            },
            "Dex": {"ProtocolName": "Uniswap"},
        },
    }

    event = _parse_trade(row, "eth")

    assert event is not None
    assert event.action == "BUY"
    assert event.entity == "0x1111111111111111111111111111111111111111"
    assert event.value_usd == 250000
    assert event.asset == "EXT"
    assert event.chain == "eth"
    assert event.tx_or_reference == "0xabc"


def test_small_evm_trade_is_filtered():
    row = {
        "Block": {"Time": "2026-09-14T17:00:00Z"},
        "Transaction": {
            "From": "0x1111111111111111111111111111111111111111",
            "Hash": "0xsmall",
        },
        "Trade": {
            "Sender": "0x1111111111111111111111111111111111111111",
            "Buy": {
                "Buyer": "0x1111111111111111111111111111111111111111",
                "AmountInUSD": "500",
                "Currency": {"Symbol": "EXT"},
            },
            "Sell": {
                "Seller": "0x1111111111111111111111111111111111111111",
                "AmountInUSD": "500",
                "Currency": {"Symbol": "USDC"},
            },
        },
    }

    assert _parse_trade(row, "eth") is None
