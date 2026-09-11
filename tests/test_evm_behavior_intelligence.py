from types import SimpleNamespace
from evm_behavior_intelligence import inspect_behavior

def test_behavior_flags_sell_pressure():
    market=SimpleNamespace(sells_5m=30,buys_5m=5,sells_1h=40,buys_1h=10,volume_5m_usd=20_000,liquidity_usd=10_000,change_5m_pct=30)
    report=inspect_behavior(market)
    assert "ACUTE_SELL_PRESSURE" in report.signals
    assert "PUMP_WITH_DISTRIBUTION_EVIDENCE" in report.warnings
