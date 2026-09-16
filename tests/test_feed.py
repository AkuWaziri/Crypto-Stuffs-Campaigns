from datetime import datetime, timezone

from feed import format_event
from models import ActivityEvent, Explanation


def test_feed_separates_wallet_and_token_address():
    event = ActivityEvent(
        "0xwallet",
        "WHALE_WALLET",
        "SOL",
        "BUY",
        100000,
        "solana",
        datetime.now(timezone.utc),
        "helius",
        "sig",
        (),
        "TokenMintAddress",
    )
    text = format_event(event, Explanation("CONFIRMED", "confirmed reason", ("evidence",), "HIGH"), 90)
    assert "WHALESBOARDER" in text
    assert "BUY" in text
    assert "WHO: 0xwallet" in text
    assert "ADDRESS: TokenMintAddress" in text
    assert "ADDRESS: 0xwallet" not in text
    assert "WHY IT MAY MATTER" not in text
    assert "POSSIBLE REASON" not in text
    assert "SIGNAL SCORE:" not in text
    assert "CONFIDENCE:" not in text
