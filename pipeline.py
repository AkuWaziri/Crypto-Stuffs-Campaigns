from __future__ import annotations

from datetime import datetime, timezone

from collector import collect_fresh_signals
from config import MAX_SIGNAL_AGE_MINUTES
from narrative_engine import build_narratives
from sources import enabled_sources
from x_provider import XRecentSearchProvider


def run_cycle(*, provider=None, now: datetime | None = None):
    """Run one read-only intelligence cycle.

    No token creation, wallet signing, buying, selling, or trading is reachable
    from this pipeline.
    """
    current = now or datetime.now(timezone.utc)
    social_provider = provider or XRecentSearchProvider()
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
    return signals, narratives
