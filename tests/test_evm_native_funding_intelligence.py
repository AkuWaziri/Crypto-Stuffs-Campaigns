from evm_native_funding_intelligence import inspect_native_balance

def test_native_balance_is_observational():
    class RPC:
        def call(self, method, params):
            assert method == "eth_getBalance"
            return "0x64"
    report=inspect_native_balance(RPC(), "0x1111111111111111111111111111111111111111")
    assert report.balance_wei == 100
    assert "NATIVE_BALANCE_IS_NOT_FUNDING_PROOF" in report.warnings
