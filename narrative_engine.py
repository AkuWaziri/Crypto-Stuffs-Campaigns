from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone
from typing import Iterable

from models import FreshSignal, Narrative

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "for",
    "from", "has", "have", "he", "her", "his", "i", "in", "is", "it", "its",
    "of", "on", "or", "our", "that", "the", "their", "this", "to", "was", "we",
    "were", "will", "with", "you", "your", "just", "now", "new", "today", "via",
    "crypto", "token", "tokens", "coin", "coins", "market", "markets", "blockchain",
}
TOKEN_RE = re.compile(r"(?:\$[A-Za-z][A-Za-z0-9_]{1,14}|#[A-Za-z][A-Za-z0-9_]{1,49}|[A-Za-z][A-Za-z0-9_]{2,49})")
SPECIAL_RE = re.compile(r"(?:\$[A-Za-z][A-Za-z0-9_]{1,14}|#[A-Za-z][A-Za-z0-9_]{1,49})")


def _terms(text: str) -> set[str]:
    return {
        raw.strip("#$")
        for raw in TOKEN_RE.findall(text.lower())
        if len(raw.strip("#$")) >= 3 and raw.strip("#$") not in STOPWORDS
    }


def _special_terms(text: str) -> set[str]:
    return {x.lower() for x in SPECIAL_RE.findall(text)}


def _similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _should_cluster(a: FreshSignal, b: FreshSignal, threshold: float = 0.25) -> bool:
    """Cluster closely related short posts while preserving unrelated narratives."""
    special_overlap = _special_terms(a.text) & _special_terms(b.text)
    if special_overlap:
        return True
    return _similarity(_terms(a.text), _terms(b.text)) >= threshold


def _cluster(signals: list[FreshSignal]) -> list[list[FreshSignal]]:
    clusters: list[list[FreshSignal]] = []
    for signal in signals:
        for group in clusters:
            if any(_should_cluster(signal, existing) for existing in group):
                group.append(signal)
                break
        else:
            clusters.append([signal])
    return clusters


def _velocity(group: list[FreshSignal]) -> float:
    unique_sources = {s.source.handle for s in group}
    if len(group) <= 1:
        return 20.0
    span = max((max(s.published_at for s in group) - min(s.published_at for s in group)).total_seconds(), 1.0)
    source_score = min(len(unique_sources), 5) / 5 * 60
    time_score = max(0.0, 40.0 * (1.0 - min(span / 300.0, 1.0)))
    return round(min(100.0, source_score + time_score), 2)


def _title(group: list[FreshSignal]) -> str:
    counts = Counter(term for signal in group for term in _terms(signal.text))
    return " / ".join(term for term, _ in counts.most_common(4)) or "emerging crypto narrative"


def build_narratives(signals: Iterable[FreshSignal], now: datetime | None = None, max_age_minutes: int = 5) -> list[Narrative]:
    """Build auditable narrative candidates without an LLM or execution capability."""
    now = now or datetime.now(timezone.utc)
    cutoff = now.timestamp() - max_age_minutes * 60
    fresh = [s for s in signals if cutoff <= s.published_at.timestamp() <= now.timestamp()]
    fresh.sort(key=lambda s: s.published_at)

    narratives: list[Narrative] = []
    for index, group in enumerate(_cluster(fresh), start=1):
        unique_sources = {s.source.handle for s in group}
        counts = Counter(term for signal in group for term in _terms(signal.text))
        max_engagement = max((s.engagement for s in group), default=0)
        authority_score = min(100.0, max((s.source.authority_score for s in group), default=0) + min(max_engagement / 1000, 10))
        novelty_score = min(100.0, 35 + len(counts) * 5 + (15 if len(unique_sources) > 1 else 0))
        crypto_relevance = 100.0 if any(t in {"solana", "bitcoin", "ethereum", "defi", "memecoin", "memecoins", "airdrop", "stablecoin"} for t in counts) else 65.0
        meme_potential = min(100.0, 35 + len(unique_sources) * 12 + min(len(counts), 6) * 5)
        narratives.append(Narrative(
            narrative_id=f"nar-{index}-{group[0].signal_id}",
            title=_title(group),
            signals=group,
            novelty_score=round(novelty_score, 2),
            meme_potential_score=round(meme_potential, 2),
            crypto_relevance_score=round(crypto_relevance, 2),
            velocity_score=_velocity(group),
            existing_token_penalty=0.0,
        ))

    return sorted(narratives, key=lambda n: n.trend_score, reverse=True)
