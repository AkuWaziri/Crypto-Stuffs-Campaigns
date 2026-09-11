from __future__ import annotations

import json
import os
from dataclasses import dataclass

from intelligence_models import IntelligenceDecision
from models import Narrative
from tokenized_stock_pairing import PairingCandidate, build_pairing_candidate
from xstocks_provider import XStocksPublicProvider, verified_preferred_stocks


@dataclass(frozen=True)
class LaunchPlan:
    pairing: PairingCandidate
    intelligence_score: float
    reason: str


def build_launch_plans(
    narratives: list[Narrative],
    decisions: list[IntelligenceDecision],
    *,
    max_results: int = 2,
) -> list[LaunchPlan]:
    by_id = {item.narrative_id: item for item in narratives}
    plans: list[LaunchPlan] = []

    stocks = None
    if os.getenv("TRENDSBOT_MODE", "test").lower() != "test":
        try:
            stocks = verified_preferred_stocks(XStocksPublicProvider())
        except (OSError, RuntimeError, ValueError, json.JSONDecodeError):
            # Pairing must fail closed if live tokenized-stock verification fails.
            return []

    for decision in decisions:
        if not decision.qualified:
            continue
        narrative = by_id.get(decision.narrative_id)
        if narrative is None:
            continue
        pairing = (
            build_pairing_candidate(narrative, stocks)
            if stocks is not None
            else build_pairing_candidate(narrative)
        )
        plans.append(
            LaunchPlan(
                pairing=pairing,
                intelligence_score=decision.score,
                reason=decision.reason,
            )
        )
    return plans[:max_results]
