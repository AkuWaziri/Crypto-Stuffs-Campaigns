from datetime import datetime, timezone

import pytest

from models import FreshSignal, Narrative, SourceAccount
from tokenized_stock_pairing import (
    TokenizedStock,
    build_pairing_candidate,
    select_tokenized_stock,
)


def narrative() -> Narrative:
    source = SourceAccount("source", "Source", "macro", 95, 90)
    signal = FreshSignal(
        source=source,
        signal_id="s1",
        text="A new crypto narrative is getting attention",
        url="https://example.com/1",
        published_at=datetime.now(timezone.utc),
        engagement=1000,
    )
    return Narrative(
        narrative_id="n1",
        title="New Crypto Narrative",
        signals=[signal],
        novelty_score=90,
        meme_potential_score=90,
        crypto_relevance_score=95,
        velocity_score=95,
    )


def test_selects_high_quality_liquid_candidate():
    stocks = (
        TokenizedStock("LOW", "Low", 89, 99, "verify-live"),
        TokenizedStock("GOOD", "Good", 94, 93, "verify-live"),
        TokenizedStock("BEST", "Best", 96, 96, "verify-live"),
    )
    assert select_tokenized_stock(stocks).symbol == "BEST"


def test_fails_closed_without_good_candidate():
    stocks = (TokenizedStock("LOW", "Low", 89, 89, "verify-live"),)
    with pytest.raises(ValueError):
        select_tokenized_stock(stocks)


def test_builds_pairing_candidate():
    result = build_pairing_candidate(narrative())
    assert result.concept.narrative_id == "n1"
    assert result.stock.quality_score >= 90
    assert result.stock.liquidity_score >= 90
