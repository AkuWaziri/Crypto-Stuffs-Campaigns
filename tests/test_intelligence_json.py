import json

import pytest

from intelligence_json import parse_assessment
from models import FreshSignal, Narrative, SourceAccount


def make_narrative():
    source = SourceAccount("elonmusk", "Elon Musk", "macro", 98, 85)
    signal = FreshSignal(source, "s1", "DOGE payments", "https://x.test/1", None, 100)
    return Narrative("n1", "DOGE payments", [signal], 80, 80, 85, 80, 0.0)


def payload():
    return {
        "event_summary": "DOGE payments are gaining attention",
        "canonical_topic": "DOGE payments",
        "narrative": "A crypto payment narrative is spreading",
        "novelty": 80,
        "momentum": 85,
        "cultural_resonance": 80,
        "crypto_relevance": 90,
        "tokenability": 75,
        "contradiction": 10,
        "confidence": 85,
        "reasons": ["multiple sources", "crypto relevance is high"],
    }


def test_parse_valid_json():
    assessment = parse_assessment(json.dumps(payload()), make_narrative())
    assert assessment.narrative_id == "n1"
    assert assessment.crypto_relevance == 90.0
    assert assessment.reasons == ("multiple sources", "crypto relevance is high")


def test_parse_rejects_invalid_json():
    with pytest.raises(ValueError):
        parse_assessment("not json", make_narrative())


def test_parse_rejects_out_of_range_score():
    data = payload()
    data["novelty"] = 101
    with pytest.raises(ValueError):
        parse_assessment(json.dumps(data), make_narrative())


def test_parse_rejects_missing_field():
    data = payload()
    del data["tokenability"]
    with pytest.raises(ValueError):
        parse_assessment(json.dumps(data), make_narrative())
