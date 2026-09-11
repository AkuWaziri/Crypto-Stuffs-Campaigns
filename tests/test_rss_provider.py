from datetime import datetime, timedelta, timezone

from collector import RawPost
from models import SourceAccount
from rss_provider import StaticRSSProvider, _parse_feed


SOURCE = SourceAccount("coindesk", "CoinDesk", "crypto_news", 94, 94)
NOW = datetime(2026, 9, 11, 18, 0, tzinfo=timezone.utc)


def test_parses_rss_items():
    payload = b'''<?xml version="1.0"?><rss><channel><item><title>Bitcoin ETF demand rises</title><link>https://example.com/story</link><pubDate>Fri, 11 Sep 2026 17:59:00 GMT</pubDate><description>Fresh crypto market story</description></item></channel></rss>'''
    posts = _parse_feed(payload, SOURCE)
    assert len(posts) == 1
    assert posts[0].text.startswith("Bitcoin ETF demand rises")
    assert posts[0].url == "https://example.com/story"
    assert posts[0].published_at == datetime(2026, 9, 11, 17, 59, tzinfo=timezone.utc)


def test_static_provider_returns_only_recent_posts():
    recent = RawPost("1", "fresh", "https://example.com/1", NOW - timedelta(minutes=10))
    old = RawPost("2", "old", "https://example.com/2", NOW - timedelta(minutes=90))
    provider = StaticRSSProvider({"coindesk": [recent, old]})
    result = provider.recent_posts(SOURCE, since=NOW - timedelta(minutes=60))
    assert [item.signal_id for item in result] == ["1"]
