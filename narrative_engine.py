from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Iterable

from models import FreshSignal, Narrative

# Generic terms should not cause unrelated posts to cluster together.
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "for",
    "from", "has", "have", "he", "her", "his", "i", "in", "is", "it", "its",
    "of", "on", "or", "our", "that", "the", "their", "this", "to", "was", "we",
    "were", "will", "with", "you", "your", "just", "now", "new", "today", "via",
    "crypto", "token", "tokens", "coin", "coins", "market", "markets", "blockchain",
}

TOKEN_RE = re.compile(r"(?:\$[A-Za-z][A-Za-z0-9_]{1,14}|#[A-Za-z][A-Za-z0-9_]{1,49}|[A-Za-z][A-Za-z0-9_]{2,49})")


def _terms(text: str) -> set[str]:
    values: set[str] = set()
    for raw in TOKEN_RE.findall(text.lower()):
        token = raw.strip("#$")
        if len(token) < 3 or token in STOPWORDS:
            continue
        values.add(token)
    return values


def _special_terms(text: str) -> set[str]:
    return {x.lower() for x in re.findall(r"(?:\$[A-Za-z][A-Za-z0-9_]{1,14}|#[A-Za-z][A-Za-z0-9_]{1,49})", text)}


def _similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _should_cluster(a: FreshSignal, b: FreshSignal, threshold: float = 0.34) -> bool:
    ta, tb = _terms(a.text), _terms(b.text)
    shared_special = _special_terms(a.text) & _special_terms(b.text)
    if shared_special:
        return True
    return _similarity(ta, tb) >= threshold


def _cluster(signals: list[FreshSignal]) -> list[list[FreshSignal]]:
    clusters: list[list[FreshSignal]] = []
    for signal in signals:
        placed = False
        for group in clusters:
            if any(_should_cluster(signal, existing) for existing in group):
                group.append(signal)
                placed = True
                break
        if not placed:
            clusters.append([signal])
    return clusters


def _velocity(group: list[FreshSignal]) -> float:
    """Score propagation speed and source diversity inside the active window."""
    unique_sources = {s.source for s in group}
    if len(group) <= 1:
        return 20.0
    source_score = min(len(unique_sources), 5) / 5 * 60
    timestamps = [s.published_at for s in group]
    span = max((max(timestamps) - min(timestamps)).total_seconds(), 1.0)
    time_score = max(0.0, 40.0 * (1.0 - min(span / 300.0, 1.0)))
    return round(min(100.0, source_score + time_score), 2)


def _title(group: list[FreshSignal]) -> str:
    counts = Counter(term for signal in group for term in _terms(signal.text))
    top = [term for term, _ in counts.most_common(4)]
    return " / ".join(top) if top else "emerging crypto narrative"


def build_narratives(signals: Iterable[FreshSignal], now: datetime | None = None) -> list[Narrative]:
    """Build deterministic candidate narratives from already-collected fresh signals.

    The engine deliberately does not call an LLM. It provides an auditable baseline
    that can later be enriched by semantic models without giving them launch authority.
    """
    now = now or datetime.now(timezone.utc)
    fresh = [s for s in signals if s.is_fresh and s.published_at <= now]
    fresh.sort(key=lambda s: s.published_at)
    groups = _cluster(fresh)

    narratives: list[Narrative] = []
    for index, group in enumerate(groups, start=1):
        if not group:
            continue
        unique_ids = {s.signal_id for s in group}
        unique_sources = {s.source for s in group}
        terms = [term for signal in group for term in _terms(signal.text)]
        distinctive = Counter(terms)

        authority = sum(s.engagement for s in group)
        max_engagement = max((s.engagement for s in group), default=0)
        authority_score = min(100.0, len(unique_sources) * 15 + min(max_engagement / 1000, 40))
        novelty_score = min(100.0, 35 + len(distinctive) * 5 + (15 if len(unique_sources) > 1 else 0))
        crypto_relevance = 100.0 if any(t in {"solana", "bitcoin", "ethereum", "defi", "memecoin", "memecoins", "airdrop", "stablecoin"} for t in distinctive) else 65.0
        meme_potential = min(100.0, 35 + len(unique_sources) * 12 + min(len(distinctive), 6) * 5)

        narratives.append(
            Narrative(
                narrative_id=f"nar-{index}-{min(unique_ids)}",
                title=_title(group),
                signals=group,
                novelty_score=round(novelty_score, 2),
                meme_potential_score=round(meme_potential, 2),
                crypto_relevance_score=round(crypto_relevance, 2),
                velocity_score=_velocity(group),
                existing_token_penalty=0.0,
            )
        )

    return sorted(narratives, key=lambda n: n.trend_score, reverse=True)
