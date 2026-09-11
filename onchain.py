from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class TokenRecord:
    mint: str
    symbol: str
    name: str
    chain: str = "solana"
    liquidity_usd: float = 0.0
    volume_24h_usd: float = 0.0
    holder_count: int = 0
    market_cap_usd: float = 0.0
    created_at: datetime | None = None


class TokenSearchProvider(Protocol):
    def search_tokens(self, query: str) -> list[TokenRecord]: ...


class EmptyTokenSearchProvider:
    """Safe default provider: performs no network calls and returns no matches."""

    def search_tokens(self, query: str) -> list[TokenRecord]:
        return []
