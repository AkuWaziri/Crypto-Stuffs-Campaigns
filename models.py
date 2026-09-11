from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class SourceAccount:
    handle: str
    display_name: str
    category: str
    authority_score: int
    reliability_score: int
    enabled: bool = True


@dataclass(frozen=True)
class FreshSignal:
    source: SourceAccount
    signal_id: str
    text: str
    url: str
    published_at: datetime
    engagement: int = 0

    @property
    def age_seconds(self) -> float:
        return max(0.0, (utc_now() - self.published_at).total_seconds())

    @property
    def is_fresh(self) -> bool:
        from config import MAX_SIGNAL_AGE_MINUTES

        return self.age_seconds <= MAX_SIGNAL_AGE_MINUTES * 60


@dataclass
class Narrative:
    narrative_id: str
    title: str
    signals: list[FreshSignal] = field(default_factory=list)
    novelty_score: float = 0.0
    meme_potential_score: float = 0.0
    crypto_relevance_score: float = 0.0
    velocity_score: float = 0.0
    existing_token_penalty: float = 0.0

    @property
    def freshness_score(self) -> float:
        if not self.signals:
            return 0.0
        newest = min(signal.age_seconds for signal in self.signals)
        return max(0.0, min(100.0, 100.0 - (newest / 300.0) * 100.0))

    @property
    def authority_score(self) -> float:
        if not self.signals:
            return 0.0
        return max(signal.source.authority_score for signal in self.signals)

    @property
    def trend_score(self) -> float:
        score = (
            self.freshness_score * 0.20
            + self.authority_score * 0.15
            + self.velocity_score * 0.15
            + self.crypto_relevance_score * 0.10
            + self.meme_potential_score * 0.10
            + self.novelty_score * 0.10
        )
        score -= self.existing_token_penalty
        return max(0.0, min(100.0, score))


@dataclass(frozen=True)
class QualificationDecision:
    narrative_id: str
    qualified: bool
    trend_score: float
    reason: str
    decided_at: datetime = field(default_factory=utc_now)
