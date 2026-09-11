from datetime import datetime, timezone

from models import FreshSignal, Narrative
from token_concept import build_concept
from sources import SOURCE_ACCOUNTS


def test_concept_is_deterministic_and_traces_sources():
    signal = FreshSignal(SOURCE_ACCOUNTS[0], "signal-1", "DOGE payments", "https://x.test/1", datetime.now(timezone.utc))
    narrative = Narrative("n1", "DOGE payments", [signal], 90, 90, 90, 90)
    concept = build_concept(narrative)
    assert concept.symbol == "DOGE"
    assert concept.source_signal_ids == ("signal-1",)
