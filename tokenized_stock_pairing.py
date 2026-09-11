from __future__ import annotations

from dataclasses import dataclass

from models import Narrative
from token_concept import TokenConcept, build_concept


@dataclass(frozen=True)
class TokenizedStock:
    symbol: str
    name: str
    quality_score: float
    liquidity_score: float
    availability: str


@dataclass(frozen=True)
class PairingCandidate:
    concept: TokenConcept
    stock: TokenizedStock
    reason: str


# Registry only. It is deliberately not an execution or trading integration.
# A production data adapter can replace this registry after live availability is verified.
DEFAULT_TOKENIZED_STOCKS: tuple[TokenizedStock, ...] = (
    TokenizedStock("AAPL", "Apple", 95.0, 95.0, "verify-live"),
    TokenizedStock("TSLA", "Tesla", 92.0, 92.0, "verify-live"),
    TokenizedStock("NVDA", "NVIDIA", 94.0, 94.0, "verify-live"),
    TokenizedStock("MSFT", "Microsoft", 93.0, 93.0, "verify-live"),
    TokenizedStock("AMZN", "Amazon", 91.0, 91.0, "verify-live"),
)


def select_tokenized_stock(
    stocks: tuple[TokenizedStock, ...] = DEFAULT_TOKENIZED_STOCKS,
) -> TokenizedStock:
    eligible = [item for item in stocks if item.quality_score >= 90 and item.liquidity_score >= 90]
    if not eligible:
        raise ValueError("no good tokenized-stock candidate available")
    return max(eligible, key=lambda item: (item.quality_score, item.liquidity_score))


def build_pairing_candidate(
    narrative: Narrative,
    stocks: tuple[TokenizedStock, ...] = DEFAULT_TOKENIZED_STOCKS,
) -> PairingCandidate:
    concept = build_concept(narrative)
    stock = select_tokenized_stock(stocks)
    return PairingCandidate(
        concept=concept,
        stock=stock,
        reason=(
            "Recent attention narrative passed the research gate; pair the concept "
            "with the highest-quality configured tokenized-stock candidate after live availability verification."
        ),
    )
