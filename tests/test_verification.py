from datetime import datetime, timezone

from models import FreshSignal, Narrative, SourceAccount
from onchain import TokenRecord
from solana_verifier import verify_narrative


class FakeProvider:
    def __init__(self, records):
        self.records = records

    def search_tokens(self, query):
        return self.records


def narrative():
    source = SourceAccount("elonmusk", "Elon Musk", "macro", 98, 85)
    signal = FreshSignal(source, "1", "DOGE payments are coming", "https://x.test/1", datetime.now(timezone.utc))
    return Narrative("n1", "DOGE payments", [signal], 90, 90, 90, 90)


def test_highly_saturated_existing_token_is_flagged():
    token = TokenRecord("mint", "DOGE", "Dogecoin", liquidity_usd=2_000_000, volume_24h_usd=20_000_000, holder_count=20_000)
    result = verify_narrative(narrative(), FakeProvider([token]))
    assert result.saturated is True
    assert result.best_penalty >= 40


def test_unrelated_token_is_not_saturated():
    token = TokenRecord("mint", "CAT", "Cat Token", liquidity_usd=2_000_000, volume_24h_usd=20_000_000, holder_count=20_000)
    result = verify_narrative(narrative(), FakeProvider([token]))
    assert result.saturated is False
    assert result.best_penalty == 0
