"""Core qualification: combine independent evidence into an explainable label."""
from __future__ import annotations
from dataclasses import dataclass, field
from ethereum_models import MarketData
from evm_contract_security import ContractSecurityReport
from evm_manipulation_intelligence import ManipulationReport

@dataclass(frozen=True)
class QualificationReport:
    score: int
    label: str
    reasons: tuple[str, ...] = field(default_factory=tuple)
    hard_risks: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)


def qualify(*, market: MarketData, security: ContractSecurityReport, manipulation: ManipulationReport, threshold: int = 75) -> QualificationReport:
    if threshold < 0 or threshold > 100:
        raise ValueError("threshold must be between 0 and 100")
    score = 0
    reasons = []
    liquidity = market.liquidity_usd
    if liquidity >= 100_000: score += 15; reasons.append("strong liquidity")
    elif liquidity >= 25_000: score += 10; reasons.append("adequate liquidity")
    elif liquidity > 0: score += 5; reasons.append("limited liquidity")
    ratio = market.liquidity_to_market_cap
    if ratio >= 0.20: score += 10; reasons.append("strong liquidity/market-cap ratio")
    elif ratio >= 0.08: score += 7
    elif ratio >= 0.03: score += 3
    if market.volume_5m_usd > 0: score += 10; reasons.append("recent volume present")
    if market.volume_1h_usd > 0: score += 10
    if market.buys_5m > market.sells_5m: score += 10; reasons.append("positive 5m buy pressure")
    if market.buys_1h > market.sells_1h: score += 10
    if market.change_5m_pct > 0: score += 5
    if market.change_1h_pct > 0: score += 5
    if security.erc20_compatible: score += 10; reasons.append("ERC-20 compatibility observed")
    if security.safe_for_research: score += 10; reasons.append("contract passes current safety gates")
    score += max(0, min(15, manipulation.evidence_score // 10))
    score = min(100, score)
    hard = tuple(sorted(set(security.hard_risks) | set(manipulation.hard_risks)))
    warnings = tuple(sorted(set(security.warnings) | set(manipulation.warnings)))
    if hard:
        label = "HARD RISK"
    elif not market.warnings and score >= threshold:
        label = "RESEARCH NOW"
    elif score >= 55:
        label = "WATCH"
    elif any("UNAVAILABLE" in w or "MISSING" in w for w in warnings):
        label = "INSUFFICIENT DATA"
    else:
        label = "PASS"
    return QualificationReport(score, label, tuple(reasons), hard, warnings)
