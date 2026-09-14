from live_monitor import collect_evm, collect_live_events


def test_evm_live_layer_is_fail_closed_until_provider_adapter_exists():
    assert collect_evm() == []


def test_live_collection_is_safe_without_wallet_configuration():
    assert isinstance(collect_live_events(), list)
