from solana_monitor import parse_swap


WALLET = "WhaleWallet"
MINT = "TokenMint"


def test_swap_receiving_target_is_buy():
    tx = {
        "type": "SWAP",
        "timestamp": 1750000000,
        "signature": "sig-buy",
        "tokenTransfers": [
            {"mint": MINT, "toUserAccount": WALLET, "fromUserAccount": "DEX"}
        ],
    }
    event = parse_swap(tx, WALLET, MINT)
    assert event is not None
    assert event.action == "BUY"


def test_swap_spending_target_is_sell():
    tx = {
        "type": "SWAP",
        "timestamp": 1750000000,
        "signature": "sig-sell",
        "tokenTransfers": [
            {"mint": MINT, "toUserAccount": "DEX", "fromUserAccount": WALLET}
        ],
    }
    event = parse_swap(tx, WALLET, MINT)
    assert event is not None
    assert event.action == "SELL"


def test_transfer_is_not_classified_as_trade():
    tx = {"type": "TRANSFER", "signature": "sig-transfer", "tokenTransfers": []}
    assert parse_swap(tx, WALLET, MINT) is None
