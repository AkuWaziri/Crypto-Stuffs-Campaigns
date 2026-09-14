from datetime import datetime, timezone

from feed import format_event
from models import ActivityEvent, Explanation


def test_feed_contains_core_signal_fields():
    event = ActivityEvent("wallet", "WHALE_WALLET", "SOL", "BUY", 100000, "solana", datetime.now(timezone.utc), "helius", "sig")
    text = format_event(event, Explanation("CONFIRMED", "confirmed reason", ("evidence",), "HIGH"), 90)
    assert "WHALESBOARDER" in text
    assert "BUY" in text
    assert "wallet" in text
    assert "SIGNAL SCORE: 90/100" in text
