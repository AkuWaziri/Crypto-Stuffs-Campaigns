from datetime import datetime, timezone

from models import FreshSignal, Narrative, SourceAccount
from qualification import qualify_with_verification
from solana_verifier import VerificationResult


def test_meme_potential_is_not_a_hard_qualification_gate():
    source = SourceAccount("coindesk", "CoinDesk", "crypto_news", 94, 94)
    signal = FreshSignal(
        source=source,
        signal_id="signal-1",
        text="Solana launches new crypto product",
        url="https://example.com/1",
        published_at=datetime.now(timezone.utc),
    )
    narrative = Narrative(
        narrative_id="nar-1",
        title="solana launch",
        signals=[signal],
        novelty_score=90,
        meme_potential_score=0,
        crypto_relevance_score=100,
        velocity_score=100,
        freshness_score_override=100,
    )
    verification = VerificationResult("nar-1", False, 0.0, "no matching token")

    result = qualify_with_verification(narrative, verification)

    assert result.qualified is True
