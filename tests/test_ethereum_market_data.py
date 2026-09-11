import json

import pytest

import ethereum_market_data
from ethereum_market_data import (
    DexScreenerClient,
    MarketDataProviderError,
    MarketDataValidationError,
    normalize_dexscreener_pair,
    select_best_pair,
)


ADDRESS = "0x1111111111111111111111111111111111111111"
PAIR = "0x2222222222222222222222222222222222222222"


def sample_pair(**overrides):
    pair = {
        "chainId": "ethereum",
        "dexId": "uniswap",
        "pairAddress": PAIR,
        "baseToken": {"address": ADDRESS, "name": "Example", "symbol": "EX"},
        "priceUsd": "1.25",
        "txns": {
            "m5": {"buys": 20, "sells": 10},
            "h1": {"buys": 100, "sells": 80},
        },
        "volume": {"m5": 1000, "h1": 10000},
        "priceChange": {"m5": 3.2, "h1": 8.1},
        "liquidity": {"usd": 50000},
        "fdv": 200000,
        "marketCap": 180000,
        "pairCreatedAt": 1_700_000_000_000,
    }
    pair.update(overrides)
    return pair


def test_normalize_valid_pair():
    data = normalize_dexscreener_pair(sample_pair(), now_ms=1_700_000_100_000)
    assert data.contract == ADDRESS
    assert data.pair == PAIR
    assert data.buy_sell_ratio_5m == 2
    assert data.liquidity_to_market_cap == pytest.approx(50000 / 180000)


def test_negative_price_change_is_valid():
    pair = sample_pair(priceChange={"m5": -12.5, "h1": -2.0})
    data = normalize_dexscreener_pair(pair, now_ms=1_700_000_100_000)
    assert data.change_5m_pct == -12.5


def test_missing_market_data_fails_closed():
    pair = sample_pair()
    del pair["liquidity"]
    with pytest.raises(MarketDataValidationError):
        normalize_dexscreener_pair(pair, now_ms=1_700_000_100_000)


def test_contradictory_market_data_fails_closed():
    pair = sample_pair(liquidity={"usd": 300000}, fdv=100000)
    with pytest.raises(MarketDataValidationError):
        normalize_dexscreener_pair(pair, now_ms=1_700_000_100_000)


def test_select_best_pair_uses_liquidity():
    low = sample_pair(pairAddress="0x3333333333333333333333333333333333333333")
    high = sample_pair(pairAddress="0x4444444444444444444444444444444444444444", liquidity={"usd": 80000})
    data = select_best_pair([low, high], now_ms=1_700_000_100_000)
    assert data.pair == "0x4444444444444444444444444444444444444444"


def test_dexscreener_client_parses_search_response():
    payload = json.dumps({"pairs": [sample_pair()]}).encode()
    client = DexScreenerClient(get=lambda url: payload)
    assert len(client.search_pairs("WETH")) == 1


def test_dexscreener_client_rejects_bad_json():
    client = DexScreenerClient(get=lambda url: b"not-json")
    with pytest.raises(MarketDataProviderError):
        client.search_pairs("WETH")


def test_default_get_sets_api_request_headers(monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b"{}"

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(ethereum_market_data.urllib.request, "urlopen", fake_urlopen)
    assert ethereum_market_data._default_get("https://api.dexscreener.com/latest/dex/search?q=WETH") == b"{}"
    request = captured["request"]
    assert request.get_header("Accept") == "application/json"
    assert request.get_header("User-agent") == "EVMBot/1.0 (read-only market intelligence)"
    assert captured["timeout"] == 15
