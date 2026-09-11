from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class LaunchObservation:
    mint: str
    observed_at: datetime
    liquidity_usd: float = 0.0
    volume_usd: float = 0.0
    holders: int = 0
    creator_fees_usd: float = 0.0


class PostLaunchProvider:
    """Read-only observation boundary for future launched tokens."""

    def observe(self, mint: str) -> LaunchObservation:
        raise RuntimeError("post-launch provider is not implemented")


@dataclass(frozen=True)
class PerformanceSnapshot:
    mint: str
    observations: tuple[LaunchObservation, ...]
    peak_volume_usd: float
    peak_liquidity_usd: float
    peak_holders: int
    total_creator_fees_usd: float


def summarize_observations(mint: str, observations: list[LaunchObservation]) -> PerformanceSnapshot:
    return PerformanceSnapshot(
        mint=mint,
        observations=tuple(observations),
        peak_volume_usd=max((item.volume_usd for item in observations), default=0.0),
        peak_liquidity_usd=max((item.liquidity_usd for item in observations), default=0.0),
        peak_holders=max((item.holders for item in observations), default=0),
        total_creator_fees_usd=sum(item.creator_fees_usd for item in observations),
    )
