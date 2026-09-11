import pytest

from ethereum_discovery import (
    DexScreenerDiscovery,
    DiscoveryValidationError,
    PairCreatedDiscovery,
    deduplicate_candidates,
    normalize_address,
)
from ethereum_models import DiscoveryCandidate

A = "0x1111111111111111111111111111111111111111"
B = "0x2222222222222222222222222222222222222222"
PAIR = "0x3333333333333333333333333333333333333333"
FACTORY = "0x4444444444444444444444444444444444444444"
TOPIC = "0x" + "aa" * 32


def test_normalize_address_is_canonical():
    assert normalize_address(A.upper()) == A


def test_invalid_address_rejected():
    with pytest.raises(DiscoveryValidationError):
        normalize_address("0x123")


def test_deduplicate_uses_contract_as_identity():
    candidates = [
        DiscoveryCandidate(A.upper(), "source-a"),
        DiscoveryCandidate(A, "source-b", pair=PAIR),
    ]
    result = deduplicate_candidates(candidates)
    assert len(result) == 1
    assert result[0].contract == A


def test_dexscreener_discovery_only_accepts_ethereum():
    class FakeClient:
        def search_pairs(self, query):
            return [
                {
                    "chainId": "solana",
                    "baseToken": {"address": A},
                    "pairAddress": PAIR,
                },
                {
                    "chainId": "ethereum",
                    "baseToken": {"address": A},
                    "pairAddress": PAIR,
                    "dexId": "uniswap",
                },
            ]

    result = DexScreenerDiscovery(FakeClient()).discover("WETH")
    assert len(result) == 1
    assert result[0].contract == A


def test_pair_created_discovery_decodes_topics_and_data():
    class FakeRPC:
        def get_logs(self, params):
            token0 = "0" * 24 + A[2:]
            token1 = "0" * 24 + B[2:]
            pair_word = "0" * 24 + PAIR[2:]
            return [{
                "topics": [TOPIC, "0x" + token0, "0x" + token1],
                "data": "0x" + pair_word + ("0" * 64),
                "blockNumber": "0x10",
            }]

    result = PairCreatedDiscovery(FakeRPC(), (FACTORY,), TOPIC).discover(16, 16)
    assert [item.contract for item in result] == [A, B]
    assert result[0].pair == PAIR
    assert result[0].discovered_at_block == 16
