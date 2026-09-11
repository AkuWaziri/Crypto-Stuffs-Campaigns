from datetime import datetime, timezone

from models import FreshSignal, Narrative, SourceAccount
from onchain import TokenRecord
from saturation import assess_saturation, assess_token_match

NOW = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)
SOURCE = SourceAccount("elonmusk", "Elon Musk", "macro", 98, 85)


def narrative(title: str, text: str | None = None) -> Narrative:
    signal = FreshSignal(
        source=SOURCE,
        signal_id="1",
        text=text or title,
        url="https://example.com/1",
        published_at=NOW,
    )
    return Narrative("n1", title, [signal], novelty_score=80, meme_potential_score=80, crypto_relevance_score=90, velocity_score=80)


def test_exact_existing_token_match_gets_penalty():
    result = assess_token_match(
        narrative("DOGE payments"),
        TokenRecord("mint1", "DOGE", "Dogecoin", liquidity_usd=2_000_000, volume_24h_usd=15_000_000, holder_count=50_000),
    )
    assert result.match_confidence == 100.0
    assert result.penalty == 60.0


def test_symbol_only_match_does_not_match_unrelated_symbol():
    result = assess_token_match(
        narrative("DOGE payments"),
        TokenRecord("mint2", "PEPE", "Pepe", liquidity_usd=5_000_000, volume_24h_usd=20_000_000, holder_count=100_000),
    )
    assert result.match_confidence == 0.0
    assert result.penalty == 0.0


def test_weak_existing_token_has_lower_penalty():
    result = assess_token_match(
        narrative("DOGE payments"),
        TokenRecord("mint3", "DOGE", "Dogecoin", liquidity_usd=5_000, volume_24h_usd=2_000, holder_count=20),
    )
    assert result.match_confidence == 100.0
    assert 0.0 < result.penalty < 60.0


def test_no_match_has_zero_penalty():
    result = assess_token_match(
        narrative("DOGE payments"),
        TokenRecord("mint4", "SOL", "Solana", liquidity_usd=10_000_000, volume_24h_usd=30_000_000, holder_count=200_000),
    )
    assert result.penalty == 0.0


def test_saturation_deduplicates_mints_and_ignores_non_solana():
    class Provider:
        def search_tokens(self, query):
            return [
                TokenRecord("mint1", "DOGE", "Dogecoin", liquidity_usd=2_000_000, volume_24h_usd=15_000_000, holder_count=50_000),
                TokenRecord("mint1", "DOGE", "Dogecoin"),
                TokenRecord("eth1", "DOGE", "Dogecoin", chain="ethereum", liquidity_usd=20_000_000),
            ]

    matches = assess_saturation(narrative("DOGE payments"), Provider())
    assert len(matches) == 1
    assert matches[0].token.mint == "mint1"
