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


# Test-only registry. Production/observation pairing uses the live xStocks adapter.
DEFAULT_TOKENIZED_STOCKS: tuple[TokenizedStock, ...] = (
    TokenizedStock("AAPLx", "Apple xStock", 95.0, 95.0, "test-verified"),
    TokenizedStock("TSLAx", "Tesla xStock", 92.0, 92.0, "test-verified"),
    TokenizedStock("NVDAx", "NVIDIA xStock", 94.0, 94.0, "test-verified"),
    TokenizedStock("MSFTx", "Microsoft xStock", 93.0, 93.0, "test-verified"),
    TokenizedStock("AMZNx", "Amazon xStock", 91.0, 91.0, "test-verified"),
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
            "with a verified tokenized-stock candidate."
        ),
    )
