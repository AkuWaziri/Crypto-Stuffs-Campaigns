from datetime import datetime, timedelta, timezone

from collector import RawPost
from onchain import TokenRecord
from pipeline import run_cycle

NOW = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)


class FakeProvider:
    def recent_posts(self, source, *, since):
        if source.handle == "elonmusk":
            return [RawPost("1", "$DOGE payments are coming to X", "https://x.com/1", NOW - timedelta(minutes=1), 1000)]
        if source.handle == "saylor":
            return [RawPost("2", "DOGE payments could change crypto adoption", "https://x.com/2", NOW - timedelta(minutes=2), 500)]
        if source.handle == "lookonchain":
            return [RawPost("3", "DOGE payment activity is accelerating", "https://x.com/3", NOW - timedelta(minutes=3), 800)]
        return []


class EmptyChainProvider:
    def search_tokens(self, query):
        return []


class SaturatedChainProvider:
    def search_tokens(self, query):
        return [TokenRecord("mint", "DOGE", "Dogecoin", liquidity_usd=2_000_000, volume_24h_usd=20_000_000, holder_count=20_000)]


def test_pipeline_collects_qualifies_and_intelligently_ranks():
    signals, narratives, verifications, qualifications, assessments, intelligence = run_cycle(
        provider=FakeProvider(), token_provider=EmptyChainProvider(), now=NOW
    )
    assert len(signals) == 3
    assert len(narratives) == 1
    assert len(verifications) == 1
    assert qualifications[0].qualified is True
    assert len(assessments) == 1
    assert len(intelligence) == 1
    assert intelligence[0].qualified is True


def test_pipeline_rejects_saturated_existing_token():
    _, _, verifications, qualifications, assessments, intelligence = run_cycle(
        provider=FakeProvider(), token_provider=SaturatedChainProvider(), now=NOW
    )
    assert verifications[0].saturated is True
    assert qualifications[0].qualified is False
    assert assessments == []
    assert intelligence == []


def test_pipeline_uses_only_enabled_sources():
    class Provider:
        def recent_posts(self, source, *, since):
            return []

    signals, narratives, verifications, qualifications, assessments, intelligence = run_cycle(
        provider=Provider(), now=NOW
    )
    assert signals == []
    assert narratives == []
    assert verifications == []
    assert qualifications == []
    assert assessments == []
    assert intelligence == []
