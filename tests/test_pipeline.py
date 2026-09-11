from datetime import datetime, timedelta, timezone

from collector import RawPost
from models import SourceAccount
from pipeline import run_cycle

NOW = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)


class FakeProvider:
    def recent_posts(self, source, *, since):
        if source.handle == "elonmusk":
            return [RawPost("1", "$DOGE payments are coming to X", "https://x.com/1", NOW - timedelta(minutes=1), 1000)]
        if source.handle == "saylor":
            return [RawPost("2", "DOGE payments could change crypto adoption", "https://x.com/2", NOW - timedelta(minutes=2), 500)]
        return []


def test_pipeline_collects_and_clusters_without_execution():
    signals, narratives = run_cycle(provider=FakeProvider(), now=NOW)
    assert len(signals) == 2
    assert len(narratives) == 1
    assert len(narratives[0].signals) == 2


def test_pipeline_uses_only_enabled_sources():
    class Provider:
        def recent_posts(self, source, *, since):
            return []

    signals, narratives = run_cycle(provider=Provider(), now=NOW)
    assert signals == []
    assert narratives == []
