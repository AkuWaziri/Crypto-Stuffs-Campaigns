from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from models import Narrative
from solana_verifier import VerificationResult


@dataclass(frozen=True)
class QualificationResult:
    narrative_id: str
    qualified: bool
    score: float
    reason: str


def qualify_with_verification(
    narrative: Narrative,
    verification: VerificationResult,
    *,
    threshold: float = 80.0,
    hard_saturation_penalty: float = 55.0,
) -> QualificationResult:
    score = max(0.0, narrative.trend_score - verification.best_penalty)
    if not narrative.signals:
        return QualificationResult(narrative.narrative_id, False, score, "no signals")
    if verification.saturated or verification.best_penalty >= hard_saturation_penalty:
        return QualificationResult(
            narrative.narrative_id,
            False,
            score,
            "existing Solana narrative is too saturated",
        )
    if narrative.meme_potential_score < 70.0:
        return QualificationResult(narrative.narrative_id, False, score, "meme potential below threshold")
    if score < threshold:
        return QualificationResult(narrative.narrative_id, False, score, "verified trend score below threshold")
    return QualificationResult(narrative.narrative_id, True, score, "qualified after on-chain verification")


def rank_verified(
    narratives: Iterable[Narrative],
    verifications: Iterable[VerificationResult],
    *,
    threshold: float = 80.0,
) -> list[QualificationResult]:
    by_id = {item.narrative_id: item for item in verifications}
    results = []
    for narrative in narratives:
        verification = by_id.get(narrative.narrative_id)
        if verification is None:
            results.append(QualificationResult(narrative.narrative_id, False, 0.0, "missing verification"))
            continue
        results.append(qualify_with_verification(narrative, verification, threshold=threshold))
    return sorted(results, key=lambda item: item.score, reverse=True)
