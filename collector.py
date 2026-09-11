from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from freshness import is_within_window
from models import FreshSignal, SourceAccount


@dataclass(frozen=True)
class RawPost:
    signal_id: str
    text: str
    url: str
    published_at: datetime
    engagement: int = 0


class SocialProvider(Protocol):
    def recent_posts(self, source: SourceAccount, *, since: datetime) -> list[RawPost]:
        ...


def collect_fresh_signals(
    provider: SocialProvider,
    sources: list[SourceAccount],
    *,
    now: datetime | None = None,
    max_age_minutes: int = 5,
) -> list[FreshSignal]:
    current = now or datetime.now(timezone.utc)
    signals: list[FreshSignal] = []

    for source in sources:
        if not source.enabled:
            continue
        posts = provider.recent_posts(source, since=current)
        for post in posts:
            if not is_within_window(
                post.published_at,
                max_age_minutes=max_age_minutes,
                now=current,
            ):
                continue
            signals.append(
                FreshSignal(
                    source=source,
                    signal_id=post.signal_id,
                    text=post.text,
                    url=post.url,
                    published_at=post.published_at,
                    engagement=post.engagement,
                )
            )

    return signals
