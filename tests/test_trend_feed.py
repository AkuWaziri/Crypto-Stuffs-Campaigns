from datetime import datetime, timezone

from models import FreshSignal, Narrative, SourceAccount
from trend_feed import format_feed


def _narrative(text: str, title: str = "solana launch") -> Narrative:
    source = SourceAccount("coindesk", "CoinDesk", "crypto_news", 94, 94)
    signal = FreshSignal(
        source=source,
        signal_id="signal-1",
        text=text,
        url="https://example.com/story",
        published_at=datetime.now(timezone.utc),
    )
    return Narrative(
        narrative_id="nar-1",
        title=title,
        signals=[signal],
    )


def test_format_feed_contains_trend_and_three_token_points():
    result = format_feed([_narrative("Solana announces a new crypto launch")], max_items=1)

    assert "TRENDING NOW" in result
    assert "Solana Launch" in result
    assert "Token creation potential" in result
    assert result.count("•") == 3
    assert "NO TOKEN CREATED" in result
    assert "https://example.com/story" in result


def test_token_angles_change_for_stablecoin_story():
    result = format_feed([
        _narrative(
            "A new stablecoin payment rail expands USDC adoption",
            title="stablecoin payments",
        )
    ], max_items=1)

    assert "payment rail or stablecoin adoption story" in result
    assert "merchant/community incentives" in result


def test_token_angles_change_for_airdrop_story():
    result = format_feed([
        _narrative(
            "New airdrop campaign opens claims for early users",
            title="airdrop campaign",
        )
    ], max_items=1)

    assert "campaign moment" in result
    assert "quests or community access" in result
