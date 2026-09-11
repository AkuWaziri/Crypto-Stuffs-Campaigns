from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from models import Narrative
from onchain import TokenRecord, TokenSearchProvider


@dataclass(frozen=True)
class TokenMatch:
    token: TokenRecord
    match_confidence: float
    penalty: float
    reason: str


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _terms(narrative: Narrative) -> set[str]:
    text = " ".join([narrative.title, *(signal.text for signal in narrative.signals)])
    return {term for term in re.findall(r"[a-z0-9]{3,}", _normalize(text))}


def match_confidence(narrative: Narrative, token: TokenRecord) -> float:
    terms = _terms(narrative)
    symbol = _normalize(token.symbol)
    name_terms = set(_normalize(token.name).split())

    if symbol and symbol in terms:
        return 100.0
    overlap = len(terms & name_terms)
    if overlap == 0 or not name_terms:
        return 0.0
    return min(90.0, 50.0 + (overlap / len(name_terms)) * 40.0)


def _market_strength(token: TokenRecord) -> float:
    """Estimate saturation strength from public market activity, not price direction."""
    score = 0.0
    if token.liquidity_usd >= 1_000_000:
        score += 35.0
    elif token.liquidity_usd >= 100_000:
        score += 20.0
    elif token.liquidity_usd >= 10_000:
        score += 8.0

    if token.volume_24h_usd >= 10_000_000:
        score += 35.0
    elif token.volume_24h_usd >= 1_000_000:
        score += 25.0
    elif token.volume_24h_usd >= 100_000:
        score += 10.0

    if token.holder_count >= 10_000:
        score += 30.0
    elif token.holder_count >= 1_000:
        score += 20.0
    elif token.holder_count >= 100:
        score += 8.0
    return min(100.0, score)


def assess_token_match(narrative: Narrative, token: TokenRecord) -> TokenMatch:
    confidence = match_confidence(narrative, token)
    if confidence == 0.0:
        return TokenMatch(token, 0.0, 0.0, "no narrative/token match")

    strength = _market_strength(token)
    penalty = min(60.0, (confidence / 100.0) * strength * 0.60)
    if confidence >= 100.0 and strength >= 70.0:
        penalty = 60.0
        reason = "strong exact match with highly saturated token"
    elif confidence >= 100.0:
        penalty = max(10.0, penalty)
        reason = "exact token/symbol match"
    elif strength >= 70.0:
        reason = "strong narrative match with high market activity"
    else:
        reason = "weak or lightly traded existing match"

    return TokenMatch(token, round(confidence, 2), round(penalty, 2), reason)


def assess_saturation(
    narrative: Narrative,
    provider: TokenSearchProvider,
    *,
    queries: Iterable[str] | None = None,
) -> list[TokenMatch]:
    search_queries = list(queries or [narrative.title])
    records: list[TokenRecord] = []
    seen_mints: set[str] = set()

    for query in search_queries:
        for token in provider.search_tokens(query):
            if token.chain.lower() != "solana" or token.mint in seen_mints:
                continue
            seen_mints.add(token.mint)
            records.append(token)

    matches = [assess_token_match(narrative, token) for token in records]
    return sorted(matches, key=lambda match: match.penalty, reverse=True)
