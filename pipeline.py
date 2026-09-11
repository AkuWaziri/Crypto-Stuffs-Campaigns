from __future__ import annotations

from datetime import datetime, timezone

from collector import collect_fresh_signals
from config import MAX_SIGNAL_AGE_MINUTES
from intelligence_engine import assess_narratives, decide_intelligence
from intelligence_models import IntelligenceAssessment, IntelligenceDecision
from launch_plan import LaunchPlan, build_launch_plans
from narrative_engine import build_narratives
from onchain import EmptyTokenSearchProvider, TokenSearchProvider
from qualification import QualificationResult, rank_verified
from solana_verifier import verify_many
from sources import enabled_sources
from x_provider import XRecentSearchProvider


def run_cycle(
    *,
    provider=None,
    token_provider: TokenSearchProvider | None = None,
    intelligence_provider=None,
    now: datetime | None = None,
):
    """Run one read-only intelligence cycle.

    No token creation, wallet signing, buying, selling, or trading is reachable.
    Final launch plans are research-only pairings for qualified recent narratives.
    """
    current = now or datetime.now(timezone.utc)
    social_provider = provider or XRecentSearchProvider()
    chain_provider = token_provider or EmptyTokenSearchProvider()

    signals = collect_fresh_signals(
        social_provider,
        enabled_sources(),
        now=current,
        max_age_minutes=MAX_SIGNAL_AGE_MINUTES,
    )
    narratives = build_narratives(
        signals,
        now=current,
        max_age_minutes=MAX_SIGNAL_AGE_MINUTES,
    )
    verifications = verify_many(narratives, chain_provider)
    qualifications: list[QualificationResult] = rank_verified(narratives, verifications)

    verified_narratives = {
        item.narrative_id
        for item in qualifications
        if item.qualified
    }
    candidates = [item for item in narratives if item.narrative_id in verified_narratives]
    assessments: list[IntelligenceAssessment] = assess_narratives(candidates, intelligence_provider)
    intelligence: list[IntelligenceDecision] = decide_intelligence(assessments)
    launch_plans: list[LaunchPlan] = build_launch_plans(candidates, intelligence)

    return signals, narratives, verifications, qualifications, assessments, intelligence, launch_plans
