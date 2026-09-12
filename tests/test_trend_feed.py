from datetime import datetime, timezone

from models import FreshSignal, Narrative, SourceAccount
from trend_feed import format_feed


def test_format_feed_contains_trend_and_three_token_points():
    source = SourceAccount("coindesk", "CoinDesk", "crypto_news", 94, 94)
    signal = FreshSignal(
        source=source,
        signal_id="signal-1",
        text="Solana announces a new crypto launch",
        url="https://example.com/story",
        published_at=datetime.now(timezone.utc),
    )
    narrative = Narrative(
        narrative_id="nar-1",
        title="solana launch",
        signals=[signal],
    )

    result = format_feed([narrative], max_items=1)

    assert "TRENDING NOW" in result
    assert "Solana Launch" in result
    assert "Token creation potential" in result
    assert result.count("•") == 3
    assert "NO TOKEN CREATED" in result
    assert "https://example.com/story" in result
