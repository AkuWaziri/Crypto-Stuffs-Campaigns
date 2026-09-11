from datetime import datetime, timezone

from models import FreshSignal, Narrative, SourceAccount
from scoring import qualify_narrative


def make_signal():
    source = SourceAccount("test", "Test", "test", 100, 100)
    return FreshSignal(
        source=source,
        signal_id="1",
        text="A fresh crypto narrative",
        url="https://example.com/1",
        published_at=datetime.now(timezone.utc),
    )


def test_strong_narrative_qualifies():
    narrative = Narrative(
        narrative_id="n1",
        title="Strong narrative",
        signals=[make_signal()],
        novelty_score=90,
        meme_potential_score=90,
        crypto_relevance_score=90,
        velocity_score=90,
    )
    decision = qualify_narrative(narrative)
    assert decision.qualified
    assert decision.trend_score >= 80


def test_weak_meme_potential_does_not_qualify():
    narrative = Narrative(
        narrative_id="n2",
        title="Technical-only event",
        signals=[make_signal()],
        novelty_score=100,
        meme_potential_score=20,
        crypto_relevance_score=100,
        velocity_score=100,
    )
    decision = qualify_narrative(narrative)
    assert not decision.qualified
