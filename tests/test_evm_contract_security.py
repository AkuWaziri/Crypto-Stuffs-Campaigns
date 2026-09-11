import pytest

from evm_contract_security import (
    ContractValidationError,
    inspect_erc20,
)
from ethereum_rpc import EthereumRPCProviderError

ADDRESS = "0x1111111111111111111111111111111111111111"
ZERO_UINT = "0x" + ("0" * 64)


class FakeRPC:
    def __init__(self, code="0x6000", storage=ZERO_UINT, fail_core=False):
        self.code = code
        self.storage = storage
        self.fail_core = fail_core
        self.calls = []

    def get_code(self, address):
        self.calls.append(("get_code", address))
        return self.code

    def eth_call(self, transaction, block="latest"):
        self.calls.append(("eth_call", transaction, block))
        if self.fail_core:
            raise EthereumRPCProviderError("provider unavailable")
        selector = transaction["data"][:10]
        if selector == "0x18160ddd":
            return "0x" + ("0" * 63) + "5"
        if selector == "0x313ce567":
            return "0x" + ("0" * 63) + "18"
        if selector == "0x70a08231":
            return ZERO_UINT
        raise AssertionError(f"unexpected selector {selector}")

    def get_storage_at(self, address, slot, block="latest"):
        self.calls.append(("get_storage_at", address, slot, block))
        return self.storage


def test_missing_contract_code_is_hard_risk():
    report = inspect_erc20(FakeRPC(code="0x"), ADDRESS)
    assert not report.exists
    assert not report.safe_for_research
    assert "NO_CONTRACT_CODE" in report.hard_risks


def test_erc20_core_interface_is_detected():
    report = inspect_erc20(FakeRPC(), ADDRESS)
    assert report.exists
    assert report.erc20_compatible
    assert report.safe_for_research
    assert report.proxy_status == "not_detected"


def test_proxy_is_warning_not_automatic_hard_risk():
    storage = "0x" + ("0" * 24) + "2222222222222222222222222222222222222222"
    report = inspect_erc20(FakeRPC(storage=storage), ADDRESS)
    assert report.proxy_status == "proxy_detected"
    assert "EIP1967_PROXY_DETECTED" in report.warnings
    assert not report.hard_risks


def test_invalid_address_rejected():
    with pytest.raises(ContractValidationError):
        inspect_erc20(FakeRPC(), "0x123")


def test_core_provider_failure_fails_closed():
    report = inspect_erc20(FakeRPC(fail_core=True), ADDRESS)
    assert not report.erc20_compatible
    assert "ERC20_INTERFACE_UNCONFIRMED" in report.hard_risks


def test_rpc_usage_is_read_only():
    rpc = FakeRPC()
    inspect_erc20(rpc, ADDRESS)
    assert all(call[0] in {"get_code", "eth_call", "get_storage_at"} for call in rpc.calls)
