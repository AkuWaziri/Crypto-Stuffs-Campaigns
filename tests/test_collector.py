from datetime import datetime, timedelta, timezone

from collector import RawPost, collect_fresh_signals
from models import SourceAccount


class FakeProvider:
    def __init__(self, posts):
        self.posts = posts
        self.since = None

    def recent_posts(self, source, *, since):
        self.since = since
        return self.posts


def source(enabled=True):
    return SourceAccount("test", "Test", "test", 90, 90, enabled=enabled)


def test_collector_keeps_only_last_five_minutes():
    now = datetime.now(timezone.utc)
    provider = FakeProvider([
        RawPost("fresh", "fresh", "https://example.com/fresh", now - timedelta(minutes=2)),
        RawPost("old", "old", "https://example.com/old", now - timedelta(minutes=6)),
    ])
    signals = collect_fresh_signals(provider, [source()], now=now, max_age_minutes=5)
    assert [signal.signal_id for signal in signals] == ["fresh"]
    assert provider.since == now - timedelta(minutes=5)


def test_disabled_source_is_not_queried():
    class FailingProvider:
        def recent_posts(self, source, *, since):
            raise AssertionError("disabled source should not be queried")

    assert collect_fresh_signals(FailingProvider(), [source(False)]) == []
