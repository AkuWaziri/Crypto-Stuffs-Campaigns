from types import SimpleNamespace
from evm_qualification import qualify

def base():
    return SimpleNamespace(liquidity_usd=150_000, market_cap_usd=500_000, liquidity_to_market_cap=.3, volume_5m_usd=20_000, volume_1h_usd=100_000, buys_5m=20, sells_5m=10, buys_1h=100, sells_1h=80, change_5m_pct=2, change_1h_pct=8, warnings=())

def test_qualification_research_now():
    security=SimpleNamespace(hard_risks=(), warnings=(), safe_for_research=True, erc20_compatible=True)
    manipulation=SimpleNamespace(hard_risks=(), warnings=(), evidence_score=100)
    report=qualify(market=base(), security=security, manipulation=manipulation)
    assert report.score >= 75
    assert report.label == "RESEARCH NOW"

def test_hard_risk_overrides_score():
    security=SimpleNamespace(hard_risks=("MINT_AUTHORITY",), warnings=(), safe_for_research=False, erc20_compatible=True)
    manipulation=SimpleNamespace(hard_risks=(), warnings=(), evidence_score=100)
    report=qualify(market=base(), security=security, manipulation=manipulation)
    assert report.label == "HARD RISK"
