from vybe_live import fetch_recent_large_trades


def test_live_trade_filtering_uses_usd_threshold(monkeypatch):
    def fake_get(path, params=None):
        return {
            "data": [
                {
                    "signature": "small",
                    "valueUsd": "99999",
                    "authorityAddress": "wallet-1",
                    "baseMintAddress": "mint-1",
                },
                {
                    "signature": "large",
                    "valueUsd": "125000",
                    "authorityAddress": "wallet-2",
                    "baseMintAddress": "mint-2",
                },
            ]
        }

    monkeypatch.setattr("vybe_live._get", fake_get)
    rows = fetch_recent_large_trades()

    assert [row["signature"] for row in rows] == ["large"]


def test_live_trade_filtering_deduplicates_signatures(monkeypatch):
    def fake_get(path, params=None):
        return {
            "data": [
                {"signature": "same", "valueUsd": "150000"},
                {"signature": "same", "valueUsd": "150000"},
            ]
        }

    monkeypatch.setattr("vybe_live._get", fake_get)
    rows = fetch_recent_large_trades()

    assert len(rows) == 1
