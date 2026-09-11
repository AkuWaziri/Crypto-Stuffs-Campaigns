from datetime import datetime, timezone

from intelligence_engine import assess_narratives, decide_intelligence
from intelligence_models import IntelligenceAssessment
from models import FreshSignal, Narrative, SourceAccount


NOW = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)


def make_narrative(*, meme=80.0, crypto=85.0, novelty=80.0, velocity=80.0):
    source = SourceAccount("elonmusk", "Elon Musk", "macro", 98, 85)
    signal = FreshSignal(source, "s1", "DOGE payments", "https://x.test/1", NOW, 100, 60, True)
    return Narrative(
        "n1", "DOGE payments", (signal,), novelty, meme, crypto, velocity, 0.0, 90.0, 0.0
    )


def test_simple_intelligence_assesses_narrative():
    assessments = assess_narratives([make_narrative()])
    assert len(assessments) == 1
    assert assessments[0].crypto_relevance == 85.0
    assert assessments[0].tokenability >= 60.0


def test_intelligence_rejects_low_crypto_relevance():
    assessment = IntelligenceAssessment("n1", "event", "topic", "narrative", 90, 90, 90, 20, 90, 0, 70, ())
    decision = decide_intelligence([assessment])[0]
    assert decision.qualified is False


def test_intelligence_returns_at_most_two():
    assessments = [
        IntelligenceAssessment(str(i), "event", "topic", "narrative", 90, 90, 90, 90, 90, 0, 90, ())
        for i in range(4)
    ]
    assert len(decide_intelligence(assessments)) == 2
