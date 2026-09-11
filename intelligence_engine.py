from __future__ import annotations

from config import INTELLIGENCE_PROVIDER
from intelligence_models import IntelligenceAssessment, IntelligenceDecision
from intelligence_provider import IntelligenceProvider, SimpleIntelligenceProvider
from models import Narrative


def _default_provider() -> IntelligenceProvider:
    if INTELLIGENCE_PROVIDER == "llm":
        from llm_intelligence import LLMIntelligenceProvider

        return LLMIntelligenceProvider()
    return SimpleIntelligenceProvider()


def assess_narratives(
    narratives: list[Narrative],
    provider: IntelligenceProvider | None = None,
) -> list[IntelligenceAssessment]:
    intelligence = provider or _default_provider()
    return [intelligence.assess(narrative) for narrative in narratives]


def decide_intelligence(
    assessments: list[IntelligenceAssessment],
    *,
    threshold: float = 70.0,
    max_results: int = 2,
) -> list[IntelligenceDecision]:
    decisions: list[IntelligenceDecision] = []
    for assessment in assessments:
        score = max(0.0, min(100.0, (
            assessment.novelty * 0.20
            + assessment.momentum * 0.25
            + assessment.cultural_resonance * 0.15
            + assessment.crypto_relevance * 0.20
            + assessment.tokenability * 0.20
            - assessment.contradiction * 0.20
        )))
        qualified = (
            score >= threshold
            and assessment.confidence >= 60.0
            and assessment.crypto_relevance >= 60.0
            and assessment.tokenability >= 60.0
            and assessment.contradiction < 50.0
        )
        reason = "qualified" if qualified else "below intelligence gate"
        decisions.append(IntelligenceDecision(assessment.narrative_id, qualified, round(score, 2), reason))

    decisions.sort(key=lambda item: item.score, reverse=True)
    return decisions[:max_results]
