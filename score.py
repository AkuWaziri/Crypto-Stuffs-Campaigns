from datetime import datetime, timezone

from discovery import WhaleCandidate
from models import ActivityEvent, Explanation


def score_signal(
    event: ActivityEvent,
    explanation: Explanation,
    *,
    candidate: WhaleCandidate | None = None,
    repeated_activity: int = 0,
) -> int:
    score = 0
    if event.action in {"BUY", "SELL"}:
        score += 25
    if event.value_usd is not None:
        if event.value_usd >= 1_000_000:
            score += 25
        elif event.value_usd >= 100_000:
            score += 15
        elif event.value_usd >= 10_000:
            score += 8
    if candidate:
        if candidate.roi_pct is not None:
            score += 20 if candidate.roi_pct >= 100 else 12 if candidate.roi_pct >= 50 else 5
        if candidate.win_rate_pct is not None:
            score += 10 if candidate.win_rate_pct >= 70 else 5 if candidate.win_rate_pct >= 55 else 0
    score += min(repeated_activity * 3, 10)
    score += {"CONFIRMED": 10, "INFERRED": 5, "UNKNOWN": 0}[explanation.status]
    age_days = max((datetime.now(timezone.utc) - event.timestamp).total_seconds() / 86400, 0)
    if age_days <= 1:
        score += 10
    elif age_days <= 7:
        score += 5
    return min(score, 100)
