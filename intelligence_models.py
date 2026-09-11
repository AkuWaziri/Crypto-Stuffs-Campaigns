from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntelligenceAssessment:
    narrative_id: str
    event_summary: str
    canonical_topic: str
    narrative: str
    novelty: float
    momentum: float
    cultural_resonance: float
    crypto_relevance: float
    tokenability: float
    contradiction: float
    confidence: float
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class IntelligenceDecision:
    narrative_id: str
    qualified: bool
    score: float
    reason: str
