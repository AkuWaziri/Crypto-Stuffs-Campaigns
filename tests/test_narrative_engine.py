from datetime import datetime, timedelta, timezone

from models import FreshSignal, SourceAccount
from narrative_engine import build_narratives

NOW = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)
SOURCES = {}


def source(handle):
    if handle not in SOURCES:
        SOURCES[handle] = SourceAccount(handle, handle, "test", 90, 90)
    return SOURCES[handle]


def signal(handle, text, minutes_ago=1, engagement=100):
    return FreshSignal(
        source=source(handle),
        signal_id=f"{handle}-{minutes_ago}-{abs(hash(text))}",
        text=text,
        url=f"https://x.com/{handle}/status/1",
        published_at=NOW - timedelta(minutes=minutes_ago),
        engagement=engagement,
    )


def test_same_emerging_topic_clusters_across_sources():
    signals = [
        signal("elonmusk", "$DOGE payments are coming to X", 1, 1000),
        signal("saylor", "DOGE payments could change crypto adoption", 2, 500),
        signal("lookonchain", "DOGE payment activity is accelerating", 3, 800),
    ]
    narratives = build_narratives(signals, now=NOW)
    assert len(narratives) == 1
    assert len(narratives[0].signals) == 3
    assert len({s.source.handle for s in narratives[0].signals}) == 3


def test_unrelated_topics_stay_separate():
    signals = [
        signal("saylor", "Bitcoin treasury strategy expands", 1),
        signal("VitalikButerin", "Ethereum rollup roadmap update", 1),
    ]
    narratives = build_narratives(signals, now=NOW)
    assert len(narratives) == 2


def test_shared_cashtag_clusters_even_with_different_wording():
    signals = [
        signal("elonmusk", "$DOGE could become useful for payments", 1),
        signal("lookonchain", "Whale activity around $DOGE is rising", 2),
    ]
    narratives = build_narratives(signals, now=NOW)
    assert len(narratives) == 1


def test_old_signal_is_excluded():
    fresh = signal("elonmusk", "$DOGE payments", 1)
    old = signal("saylor", "$DOGE payments", 10)
    narratives = build_narratives([fresh, old], now=NOW)
    assert len(narratives) == 1
    assert [s.source.handle for s in narratives[0].signals] == ["elonmusk"]


def test_duplicate_source_does_not_count_as_cross_account_velocity():
    signals = [
        signal("elonmusk", "$DOGE payments are interesting", 1),
        signal("elonmusk", "$DOGE payments are coming", 2),
        signal("elonmusk", "$DOGE payments discussion", 3),
    ]
    narrative = build_narratives(signals, now=NOW)[0]
    assert len({s.source.handle for s in narrative.signals}) == 1
    assert narrative.velocity_score < 60
