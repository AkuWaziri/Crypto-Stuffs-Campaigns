from demo_data import demo_events
from pipeline import run_demo


def test_full_demo_pipeline_produces_all_signal_types():
    outputs = run_demo(demo_events())
    assert len(outputs) == 3
    joined = "\n".join(outputs)
    assert "SOL_SMART_WALLET_01" in joined
    assert "EVM_WHALE_01" in joined
    assert "Demo Capital" in joined
    assert "SIGNAL SCORE:" in joined
