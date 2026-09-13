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


def test_format_feed_is_decision_focused():
    result = format_feed([_narrative("Solana announces a new crypto launch")], max_items=1)

    assert "CRYPTO TRENDS" in result
    assert "1. Solana announces a new crypto launch" in result
    assert "https://example.com/story" in result
    assert "Token creation potential" not in result
    assert "NO TOKEN CREATED" not in result
    assert "READ-ONLY" not in result
    assert "•" not in result


def test_format_feed_uses_latest_signal_as_headline():
    result = format_feed([
        _narrative(
            "Stablecoin payments expand across a new network. Users can now settle transactions faster.",
            title="stablecoin payments",
        )
    ], max_items=1)

    assert "1. Stablecoin payments expand across a new network." in result
    assert "Users can now settle transactions faster." in result


def test_format_feed_limits_items_and_numbers_them():
    narratives = [
        _narrative("Bitcoin ETF flows accelerate", title="bitcoin etf"),
        _narrative("Solana activity rises", title="solana activity"),
    ]
    result = format_feed(narratives, max_items=1)

    assert "1. Bitcoin ETF flows accelerate" in result
    assert "2. Solana activity rises" not in result
