from __future__ import annotations

from typing import Protocol

from intelligence_models import IntelligenceAssessment
from models import Narrative


class IntelligenceProvider(Protocol):
    def assess(self, narrative: Narrative) -> IntelligenceAssessment: ...


class SimpleIntelligenceProvider:
    """Small deterministic baseline. No network calls and no execution access."""

    def assess(self, narrative: Narrative) -> IntelligenceAssessment:
        source_count = len({signal.source.handle for signal in narrative.signals})
        momentum = min(100.0, source_count * 25.0 + narrative.velocity_score * 0.5)
        crypto_relevance = narrative.crypto_relevance_score
        cultural = narrative.meme_potential_score
        novelty = narrative.novelty_score
        tokenability = min(100.0, cultural * 0.5 + novelty * 0.25 + crypto_relevance * 0.25)
        contradiction = 0.0
        confidence = min(100.0, 0.35 * momentum + 0.25 * novelty + 0.25 * crypto_relevance + 0.15 * cultural)

        reasons = (
            f"{source_count} independent source(s)",
            f"crypto relevance {crypto_relevance:.1f}",
            f"meme potential {cultural:.1f}",
            f"novelty {novelty:.1f}",
        )
        return IntelligenceAssessment(
            narrative_id=narrative.narrative_id,
            event_summary=narrative.title,
            canonical_topic=narrative.title,
            narrative=narrative.title,
            novelty=novelty,
            momentum=momentum,
            cultural_resonance=cultural,
            crypto_relevance=crypto_relevance,
            tokenability=tokenability,
            contradiction=contradiction,
            confidence=confidence,
            reasons=reasons,
        )
