from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from models import Narrative
from onchain import TokenRecord, TokenSearchProvider
from saturation import TokenMatch, assess_saturation


@dataclass(frozen=True)
class VerificationResult:
    narrative_id: str
    matched_tokens: tuple[TokenMatch, ...]
    best_penalty: float
    saturated: bool
    confidence: float


def verify_narrative(
    narrative: Narrative,
    provider: TokenSearchProvider,
    *,
    queries: Iterable[str] | None = None,
    saturation_threshold: float = 40.0,
) -> VerificationResult:
    matches = assess_saturation(narrative, provider, queries=queries)
    best = matches[0].penalty if matches else 0.0
    confidence = matches[0].match_confidence if matches else 0.0
    return VerificationResult(
        narrative_id=narrative.narrative_id,
        matched_tokens=tuple(matches),
        best_penalty=best,
        saturated=best >= saturation_threshold,
        confidence=confidence,
    )


def verify_many(
    narratives: Iterable[Narrative],
    provider: TokenSearchProvider,
    *,
    saturation_threshold: float = 40.0,
) -> list[VerificationResult]:
    return [
        verify_narrative(
            narrative,
            provider,
            saturation_threshold=saturation_threshold,
        )
        for narrative in narratives
    ]
