"""Typed models shared by Ethereum discovery and market-data layers."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DiscoveryCandidate:
    contract: str
    source: str
    pair: str | None = None
    dex: str | None = None
    discovered_at_block: int | None = None


@dataclass(frozen=True)
class MarketData:
    symbol: str
    name: str
    contract: str
    pair: str
    dex: str
    age_seconds: float
    price_usd: float
    market_cap_usd: float
    liquidity_usd: float
    fdv_usd: float
    volume_5m_usd: float
    volume_1h_usd: float
    buys_5m: int
    sells_5m: int
    buys_1h: int
    sells_1h: int
    buy_sell_ratio_5m: float
    buy_sell_ratio_1h: float
    change_5m_pct: float
    change_1h_pct: float
    pair_created_at_ms: int
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def liquidity_to_market_cap(self) -> float:
        if self.market_cap_usd <= 0:
            return 0.0
        return self.liquidity_usd / self.market_cap_usd
