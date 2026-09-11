from __future__ import annotations

from datetime import datetime, timezone


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def age_seconds(published_at: datetime, now: datetime | None = None) -> float:
    current = ensure_utc(now or datetime.now(timezone.utc))
    published = ensure_utc(published_at)
    return max(0.0, (current - published).total_seconds())


def is_within_window(
    published_at: datetime,
    *,
    max_age_minutes: int,
    now: datetime | None = None,
) -> bool:
    if max_age_minutes < 0:
        raise ValueError("max_age_minutes cannot be negative")
    return age_seconds(published_at, now) <= max_age_minutes * 60
