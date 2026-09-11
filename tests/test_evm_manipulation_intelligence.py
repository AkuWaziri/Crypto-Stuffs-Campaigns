from types import SimpleNamespace
from evm_manipulation_intelligence import inspect_manipulation

def market():
    return SimpleNamespace(liquidity_usd=5_000, market_cap_usd=500_000, liquidity_to_market_cap=.01, sells_5m=30, buys_5m=5, sells_1h=50, buys_1h=10, warnings=())

def test_manipulation_aggregates_independent_evidence():
    security=SimpleNamespace(hard_risks=(), warnings=(), safe_for_research=True, erc20_compatible=True)
    holders=SimpleNamespace(top_holder_share=.25, top_10_share=.60)
    early=SimpleNamespace(observed_buyer_count=3)
    funding=SimpleNamespace(inbound_count=2, outbound_count=1)
    cluster=SimpleNamespace(signals=("EARLY_BUYER_FUNDING_OVERLAP",), overlap_count=3)
    report=inspect_manipulation(market=market(), security=security, holders=holders, early_buyers=early, funding=funding, cluster=cluster)
    assert "HIGH_TOP_HOLDER_CONCENTRATION" in report.warnings
    assert "SHORT_TERM_SELL_PRESSURE" in report.signals
    assert report.evidence_score < 100
