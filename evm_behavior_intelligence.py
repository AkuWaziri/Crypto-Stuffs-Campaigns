"""Market-behavior evidence independent of contract security."""
from __future__ import annotations
from dataclasses import dataclass
from ethereum_models import MarketData

@dataclass(frozen=True)
class BehaviorReport:
    signals: tuple[str, ...]
    warnings: tuple[str, ...]
    pressure_score: int

def inspect_behavior(market: MarketData) -> BehaviorReport:
    signals = []
    warnings = []
    score = 50

    if market.sells_5m > market.buys_5m * 2 and market.sells_5m >= 10:
        signals.append("ACUTE_SELL_PRESSURE")
        score -= 20
    elif market.buys_5m > market.sells_5m * 2 and market.buys_5m >= 10:
        signals.append("ACUTE_BUY_PRESSURE")
        score += 15

    if market.sells_1h > market.buys_1h * 2 and market.sells_1h >= 20:
        signals.append("SUSTAINED_SELL_PRESSURE")
        score -= 20

    if (
        market.volume_5m_usd > 0
        and market.liquidity_usd > 0
        and market.volume_5m_usd / market.liquidity_usd > 1
    ):
        warnings.append("HIGH_5M_VOLUME_TO_LIQUIDITY")

    if market.change_5m_pct > 25 and market.sells_5m > market.buys_5m:
        warnings.append("PUMP_WITH_DISTRIBUTION_EVIDENCE")
        score -= 10

    return BehaviorReport(tuple(signals), tuple(warnings), max(0, min(100, score)))
