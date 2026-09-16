from solana_discovery import _token_received, _token_sent, _quote_value_usd


MINT = "TokenMint"
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkGZwyTDt1v"


def test_token_received_for_wallet():
    tx = {
        "tokenTransfers": [
            {
                "mint": MINT,
                "toUserAccount": "wallet-1",
                "fromUserAccount": "pool",
                "tokenAmount": 2500,
            }
        ]
    }
    assert _token_received(tx, MINT, "wallet-1") == 2500


def test_token_sent_is_not_counted_as_received():
    tx = {
        "tokenTransfers": [
            {
                "mint": MINT,
                "toUserAccount": "pool",
                "fromUserAccount": "wallet-1",
                "tokenAmount": 2500,
            }
        ]
    }
    assert _token_received(tx, MINT, "wallet-1") == 0
    assert _token_sent(tx, MINT, "wallet-1") == 2500


def test_stablecoin_quote_is_used_as_usd_value():
    tx = {
        "tokenTransfers": [
            {
                "mint": USDC,
                "fromUserAccount": "wallet-1",
                "toUserAccount": "pool",
                "tokenAmount": 3500,
            }
        ]
    }
    assert _quote_value_usd(tx, "wallet-1") == 3500
