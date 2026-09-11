from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from config import MAX_LAUNCHES_PER_CYCLE, TOKEN_LAUNCH_ENABLED, TRADING_ENABLED, SELF_BUY_ENABLED
from qualification import QualificationResult


@dataclass(frozen=True)
class LaunchPlan:
    candidates: tuple[QualificationResult, ...]
    launchable: bool
    reason: str


def build_launch_plan(results: Iterable[QualificationResult]) -> LaunchPlan:
    qualified = [result for result in results if result.qualified]
    if not TOKEN_LAUNCH_ENABLED:
        return LaunchPlan(tuple(qualified[:MAX_LAUNCHES_PER_CYCLE]), False, "token launch disabled")
    if TRADING_ENABLED or SELF_BUY_ENABLED:
        return LaunchPlan((), False, "unsafe execution flags detected")
    return LaunchPlan(tuple(qualified[:MAX_LAUNCHES_PER_CYCLE]), True, "launch gate passed")
