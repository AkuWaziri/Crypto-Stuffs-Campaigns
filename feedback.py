from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from post_launch import PerformanceSnapshot


@dataclass(frozen=True)
class FeedbackRecord:
    narrative_id: str
    mint: str
    peak_volume_usd: float
    peak_liquidity_usd: float
    peak_holders: int
    creator_fees_usd: float
    outcome_score: float


def outcome_score(snapshot: PerformanceSnapshot) -> float:
    """Bounded observation score used for future learning; no trading signal."""
    volume = min(40.0, snapshot.peak_volume_usd / 250_000.0)
    liquidity = min(30.0, snapshot.peak_liquidity_usd / 100_000.0)
    holders = min(30.0, snapshot.peak_holders / 100.0)
    return round(min(100.0, volume + liquidity + holders), 2)


def make_feedback(narrative_id: str, mint: str, snapshot: PerformanceSnapshot) -> FeedbackRecord:
    return FeedbackRecord(
        narrative_id=narrative_id,
        mint=mint,
        peak_volume_usd=snapshot.peak_volume_usd,
        peak_liquidity_usd=snapshot.peak_liquidity_usd,
        peak_holders=snapshot.peak_holders,
        creator_fees_usd=snapshot.total_creator_fees_usd,
        outcome_score=outcome_score(snapshot),
    )
