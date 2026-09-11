"""Deterministic manipulation-risk evidence aggregation.

This layer produces explainable evidence flags. It does not claim intent or
replace raw observations.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from ethereum_models import MarketData
from evm_contract_security import ContractSecurityReport
from evm_holder_intelligence import HolderReport
from evm_early_buyer_intelligence import EarlyBuyerReport
from evm_funding_intelligence import FundingReport
from evm_cluster_intelligence import ClusterReport

@dataclass(frozen=True)
class ManipulationReport:
    hard_risks: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    signals: tuple[str, ...] = field(default_factory=tuple)
    evidence_score: int = 0

def inspect_manipulation(*, market: MarketData, security: ContractSecurityReport, holders: HolderReport, early_buyers: EarlyBuyerReport, funding: FundingReport, cluster: ClusterReport) -> ManipulationReport:
    hard, warnings, signals = set(security.hard_risks), set(security.warnings), set()
    if market.liquidity_usd <= 0:
        hard.add("NO_LIQUIDITY")
    elif market.liquidity_usd < 10_000:
        warnings.add("VERY_LOW_LIQUIDITY")
    if market.market_cap_usd > 0 and market.liquidity_to_market_cap < 0.03:
        warnings.add("LOW_LIQUIDITY_TO_MARKET_CAP")
    if market.sells_5m > market.buys_5m * 2 and market.sells_5m >= 10:
        signals.add("SHORT_TERM_SELL_PRESSURE")
    if market.sells_1h > market.buys_1h * 2 and market.sells_1h >= 20:
        signals.add("ONE_HOUR_SELL_PRESSURE")
    if holders.top_holder_share >= 0.20:
        warnings.add("HIGH_TOP_HOLDER_CONCENTRATION")
    if holders.top_10_share >= 0.50:
        warnings.add("HIGH_TOP10_CONCENTRATION")
    if early_buyers.observed_buyer_count == 0:
        warnings.add("EARLY_BUYER_DATA_MISSING")
    if funding.inbound_count and funding.outbound_count:
        signals.add("ANCHOR_INBOUND_AND_OUTBOUND_FLOW")
    signals.update(cluster.signals)
    if cluster.overlap_count >= 3:
        warnings.add("MULTI_LAYER_ADDRESS_OVERLAP")
    score = 100
    score -= min(50, 20 * len(hard))
    score -= min(30, 8 * len(warnings))
    score -= min(20, 5 * len(signals))
    score = max(0, score)
    return ManipulationReport(tuple(sorted(hard)), tuple(sorted(warnings)), tuple(sorted(signals)), score)
