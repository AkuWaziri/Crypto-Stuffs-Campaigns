from datetime import datetime, timezone

from discovery import WhaleCandidate
from models import ActivityEvent, Explanation
from score import score_signal


def test_strong_smart_money_signal_scores_high():
    event = ActivityEvent("wallet", "SMART_MONEY", "TOKEN", "BUY", 2_000_000, "solana", datetime.now(timezone.utc), "helius", "sig")
    explanation = Explanation("CONFIRMED", "confirmed", (), "HIGH")
    candidate = WhaleCandidate("wallet", None, "SMART_MONEY", "demo", 185, 78)
    assert score_signal(event, explanation, candidate=candidate, repeated_activity=2) >= 80
