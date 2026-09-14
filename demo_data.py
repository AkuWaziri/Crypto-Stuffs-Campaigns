from datetime import datetime, timedelta, timezone


def demo_events() -> list[dict]:
    now = datetime.now(timezone.utc)
    return [
        {
            "kind": "solana",
            "wallet": "SOL_SMART_WALLET_01",
            "asset_mint": "SOLANA_TOKEN_DEMO",
            "tx": {
                "type": "SWAP",
                "timestamp": now.timestamp(),
                "signature": "demo-solana-signature",
                "tokenTransfers": [
                    {"mint": "SOLANA_TOKEN_DEMO", "toUserAccount": "SOL_SMART_WALLET_01"}
                ],
            },
            "value_usd": 250000,
            "candidate": {"wallet": "SOL_SMART_WALLET_01", "roi": 185, "winRate": 78, "type": "SMART_MONEY"},
        },
        {
            "kind": "evm",
            "wallet": "EVM_WHALE_01",
            "asset": "ETH",
            "tx": {
                "type": "SWAP",
                "timestamp": (now - timedelta(hours=2)).timestamp(),
                "hash": "0xdemo-evm-hash",
                "spentTarget": True,
                "receivedTarget": False,
                "evidence": ("https://etherscan.io/tx/0xdemo-evm-hash",),
            },
            "value_usd": 1800000,
            "candidate": {"wallet": "EVM_WHALE_01", "roi": 92, "winRate": 71, "type": "WHALE_WALLET"},
        },
        {
            "kind": "stock",
            "row": {
                "entity": "Demo Capital",
                "asset": "AAPL",
                "action": "BUY",
                "value_usd": 3200000,
                "timestamp": (now - timedelta(days=2)).timestamp(),
                "accession": "DEMO-13F-001",
                "evidence": ("https://www.sec.gov/edgar/search/",),
            },
        },
    ]
