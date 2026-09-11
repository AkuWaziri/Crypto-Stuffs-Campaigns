from datetime import datetime, timezone

import pytest

from llm_intelligence import LLMIntelligenceProvider
from models import FreshSignal, Narrative, SourceAccount


NOW = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)


def narrative():
    source = SourceAccount("elonmusk", "Elon Musk", "macro", 98, 85)
    signal = FreshSignal(
        source=source,
        signal_id="s1",
        text="$DOGE payments are coming to X",
        url="https://x.com/example/1",
        published_at=NOW,
        engagement=100,
    )
    return Narrative(
        narrative_id="n1",
        title="DOGE payments",
        signals=[signal],
        novelty_score=80,
        meme_potential_score=85,
        crypto_relevance_score=95,
        velocity_score=70,
        existing_token_penalty=0,
    )


def response(data):
    return {"choices": [{"message": {"content": __import__("json").dumps(data)}}]}


def test_llm_provider_parses_structured_assessment():
    data = {
        "event_summary": "X payment discussion",
        "canonical_topic": "DOGE payments",
        "narrative": "DOGE becoming associated with X payments",
        "novelty": 80,
        "momentum": 75,
        "cultural_resonance": 90,
        "crypto_relevance": 95,
        "tokenability": 82,
        "contradiction": 10,
        "confidence": 88,
        "reasons": ["clear crypto relevance", "strong cultural resonance"],
    }

    def fake_request(request, timeout=30):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return __import__("json").dumps(response(data)).encode()

        return Response()

    provider = LLMIntelligenceProvider(api_key="test", request_fn=fake_request)
    result = provider.assess(narrative())

    assert result.narrative_id == "n1"
    assert result.canonical_topic == "DOGE payments"
    assert result.confidence == 88


def test_llm_provider_fails_closed_on_malformed_response():
    provider = LLMIntelligenceProvider(api_key="test", request_fn=lambda request, timeout=30: None)
    with pytest.raises((TypeError, ValueError, KeyError)):
        provider._parse_assessment(narrative(), {"choices": []})


def test_llm_provider_rejects_out_of_range_scores():
    data = {
        "event_summary": "x",
        "canonical_topic": "x",
        "narrative": "x",
        "novelty": 101,
        "momentum": 75,
        "cultural_resonance": 90,
        "crypto_relevance": 95,
        "tokenability": 82,
        "contradiction": 10,
        "confidence": 88,
        "reasons": ["x"],
    }
    with pytest.raises(ValueError):
        LLMIntelligenceProvider._parse_assessment(
            narrative(), response(data)
        )
