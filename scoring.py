from __future__ import annotations

from models import Narrative, QualificationDecision


LAUNCH_THRESHOLD = 80.0


def qualify_narrative(narrative: Narrative) -> QualificationDecision:
    if not narrative.signals:
        return QualificationDecision(
            narrative_id=narrative.narrative_id,
            qualified=False,
            trend_score=0.0,
            reason="no signals",
        )

    if not all(signal.is_fresh for signal in narrative.signals):
        score = narrative.trend_score
        return QualificationDecision(
            narrative_id=narrative.narrative_id,
            qualified=False,
            trend_score=score,
            reason="one or more signals are older than the freshness window",
        )

    score = narrative.trend_score
    qualified = score >= LAUNCH_THRESHOLD and narrative.meme_potential_score >= 70
    reason = "meets intelligence threshold" if qualified else "below launch qualification threshold"

    return QualificationDecision(
        narrative_id=narrative.narrative_id,
        qualified=qualified,
        trend_score=score,
        reason=reason,
    )
