import pytest

from evm_contract_security import (
    ContractValidationError,
    inspect_contract_authorities,
    inspect_erc20,
)
from ethereum_rpc import EthereumRPCProviderError

ADDRESS = "0x1111111111111111111111111111111111111111"
ZERO_UINT = "0x" + ("0" * 64)
ZERO_ADDRESS_WORD = ZERO_UINT
ACTIVE_OWNER_WORD = "0x" + ("0" * 24) + "2222222222222222222222222222222222222222"


class FakeRPC:
    def __init__(self, code="0x6000", storage=ZERO_UINT, fail_core=False, owner=ACTIVE_OWNER_WORD):
        self.code = code
        self.storage = storage
        self.fail_core = fail_core
        self.owner = owner
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
        if selector == "0x8da5cb5b":
            return self.owner
        raise EthereumRPCProviderError("call reverted or unavailable")

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


def test_active_owner_is_warning_not_automatic_hard_risk():
    report = inspect_contract_authorities(FakeRPC(owner=ACTIVE_OWNER_WORD), ADDRESS)
    assert report.owner_status == "active_owner"
    assert report.owner_address == "0x2222222222222222222222222222222222222222"
    assert "ACTIVE_OWNER" in report.warnings
    assert not report.hard_risks
    assert report.safe_for_research


def test_zero_owner_is_detected_as_renounced_or_zero():
    report = inspect_contract_authorities(FakeRPC(owner=ZERO_ADDRESS_WORD), ADDRESS)
    assert report.owner_status == "renounced_or_zero"
    assert report.owner_address == "0x0000000000000000000000000000000000000000"
    assert "OWNER_ZERO_OR_RENOUNCED" in report.warnings
    assert report.safe_for_research


def test_capability_indicators_are_warnings_only():
    code = "0x6000" + "40c10f19" + "8456cb59" + "3f4ba83a" + "42966c68"
    report = inspect_contract_authorities(FakeRPC(code=code), ADDRESS)
    assert report.mint_status == "indicator_present"
    assert report.pause_status == "indicator_present"
    assert "MINT_FUNCTION_INDICATOR" in report.warnings
    assert "PAUSE_FUNCTION_INDICATOR" in report.warnings
    assert "UNPAUSE_FUNCTION_INDICATOR" in report.warnings
    assert "BURN_FUNCTION_INDICATOR" in report.warnings
    assert not report.hard_risks


def test_authority_provider_failure_fails_closed():
    report = inspect_contract_authorities(FakeRPC(fail_core=True), ADDRESS)
    assert not report.safe_for_research
    assert not report.data_complete
    assert "AUTHORITY_DATA_UNCONFIRMED" in report.hard_risks


def test_authority_rpc_usage_is_read_only():
    rpc = FakeRPC()
    inspect_contract_authorities(rpc, ADDRESS)
    assert all(call[0] in {"get_code", "eth_call", "get_storage_at"} for call in rpc.calls)
