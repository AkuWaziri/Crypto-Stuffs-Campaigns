"""Read-only EVM token contract security inspection.

This module deliberately reports evidence and uncertainty separately. Missing
or failed evidence never becomes a positive safety signal.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from evm_rpc import EVMRPCClient, EthereumRPCError


class ContractSecurityError(RuntimeError):
    pass


class ContractProviderError(ContractSecurityError):
    pass


class ContractValidationError(ContractSecurityError):
    pass


@dataclass(frozen=True)
class ContractSecurityReport:
    address: str
    exists: bool
    erc20_compatible: bool
    source_verification: str = "unknown"
    owner_status: str = "unknown"
    proxy_status: str = "unknown"
    mint_status: str = "unknown"
    pause_status: str = "unknown"
    blacklist_status: str = "unknown"
    transfer_restriction_status: str = "unknown"
    hard_risks: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def safe_for_research(self) -> bool:
        return self.exists and self.erc20_compatible and not self.hard_risks


@dataclass(frozen=True)
class AuthorityReport:
    """Evidence about privileged-token controls.

    Capability indicators are deliberately warnings, not proof of malicious
    behavior. Function-selector matches can be misleading because arbitrary
    bytecode may contain the same four-byte sequence.
    """

    address: str
    owner_status: str = "unknown"
    owner_address: str | None = None
    mint_status: str = "unknown"
    pause_status: str = "unknown"
    blacklist_status: str = "unknown"
    transfer_restriction_status: str = "unknown"
    hard_risks: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    data_complete: bool = False

    @property
    def safe_for_research(self) -> bool:
        return self.data_complete and not self.hard_risks


# Standard ERC-20 selectors. Calls are eth_call only; nothing is signed or sent.
SELECTORS = {
    "totalSupply": "18160ddd",
    "balanceOf": "70a08231",
    "decimals": "313ce567",
    "symbol": "95d89b41",
    "name": "06fdde03",
    "owner": "8da5cb5b",
}

# These are only bytecode capability indicators. Selector presence does not
# prove access control or even prove that the function is reachable.
CAPABILITY_SELECTORS = {
    "MINT_FUNCTION_INDICATOR": "40c10f19",       # mint(address,uint256)
    "PAUSE_FUNCTION_INDICATOR": "8456cb59",      # pause()
    "UNPAUSE_FUNCTION_INDICATOR": "3f4ba83a",    # unpause()
    "BURN_FUNCTION_INDICATOR": "42966c68",        # burn(uint256)
}


ZERO_ADDRESS = "0x" + ("0" * 40)


def _validate_address(address: str) -> str:
    if not isinstance(address, str) or len(address) != 42 or not address.startswith("0x"):
        raise ContractValidationError("Invalid EVM contract address")
    try:
        int(address[2:], 16)
    except ValueError as exc:
        raise ContractValidationError("Invalid EVM contract address") from exc
    return "0x" + address[2:].lower()


def _decode_uint256(value: str) -> int:
    if not isinstance(value, str) or not value.startswith("0x") or len(value) < 66:
        raise ContractValidationError("Invalid uint256 eth_call response")
    try:
        return int(value[2:66], 16)
    except ValueError as exc:
        raise ContractValidationError("Invalid uint256 eth_call response") from exc


def _decode_address(value: str) -> str:
    if not isinstance(value, str) or not value.startswith("0x") or len(value) < 66:
        raise ContractValidationError("Invalid address eth_call response")
    word = value[2:66]
    try:
        int(word, 16)
    except ValueError as exc:
        raise ContractValidationError("Invalid address eth_call response") from exc
    return "0x" + word[-40:].lower()


def _call(rpc: EVMRPCClient, address: str, selector: str) -> str:
    return rpc.eth_call({"to": address, "data": "0x" + selector})


def _selector_present(code: str, selector: str) -> bool:
    if not isinstance(code, str) or not code.startswith("0x"):
        return False
    return selector.lower() in code[2:].lower()


def inspect_erc20(rpc: EVMRPCClient, address: str) -> ContractSecurityReport:
    address = _validate_address(address)
    code = rpc.get_code(address)
    if not isinstance(code, str) or not code.startswith("0x"):
        raise ContractProviderError("Invalid eth_getCode response")
    if code == "0x":
        return ContractSecurityReport(address=address, exists=False, erc20_compatible=False,
                                      hard_risks=("NO_CONTRACT_CODE",))

    warnings: list[str] = []
    hard_risks: list[str] = []

    try:
        total_supply = _decode_uint256(_call(rpc, address, SELECTORS["totalSupply"]))
        decimals = _decode_uint256(_call(rpc, address, SELECTORS["decimals"]))
        balance_zero = _decode_uint256(
            rpc.eth_call({"to": address, "data": "0x" + SELECTORS["balanceOf"] + ("0" * 64)})
        )
    except (EthereumRPCError, ContractValidationError) as exc:
        warnings.append(f"ERC20 core calls unavailable: {exc}")
        return ContractSecurityReport(
            address=address, exists=True, erc20_compatible=False,
            source_verification="unknown", hard_risks=("ERC20_INTERFACE_UNCONFIRMED",),
            warnings=tuple(warnings),
        )

    if decimals > 255:
        hard_risks.append("INVALID_DECIMALS")
    if total_supply == 0:
        warnings.append("ZERO_TOTAL_SUPPLY")
    if balance_zero < 0:
        hard_risks.append("INVALID_BALANCE")

    proxy_status = "unknown"
    try:
        implementation_slot = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
        slot_value = rpc.get_storage_at(address, implementation_slot)
        proxy_status = "proxy_detected" if int(slot_value, 16) != 0 else "not_detected"
        if proxy_status == "proxy_detected":
            warnings.append("EIP1967_PROXY_DETECTED")
    except (EthereumRPCError, ValueError, TypeError):
        warnings.append("PROXY_STATUS_UNAVAILABLE")

    return ContractSecurityReport(
        address=address,
        exists=True,
        erc20_compatible=True,
        source_verification="unknown",
        proxy_status=proxy_status,
        hard_risks=tuple(hard_risks),
        warnings=tuple(warnings),
    )


def inspect_contract_authorities(rpc: EVMRPCClient, address: str) -> AuthorityReport:
    """Inspect common privileged-token indicators using read-only RPC calls.

    An active owner is reported as a warning, not a hard risk by itself.
    Provider failures fail closed because the bot cannot safely conclude that
    authority is absent when the evidence could not be retrieved.
    """

    address = _validate_address(address)
    code = rpc.get_code(address)
    if not isinstance(code, str) or not code.startswith("0x"):
        raise ContractProviderError("Invalid eth_getCode response")
    if code == "0x":
        return AuthorityReport(
            address=address,
            hard_risks=("NO_CONTRACT_CODE",),
            data_complete=True,
        )

    warnings: list[str] = []
    hard_risks: list[str] = []

    owner_status = "not_exposed"
    owner_address: str | None = None
    try:
        owner_value = _call(rpc, address, SELECTORS["owner"])
        owner_address = _decode_address(owner_value)
        if owner_address == ZERO_ADDRESS:
            owner_status = "renounced_or_zero"
            warnings.append("OWNER_ZERO_OR_RENOUNCED")
        else:
            owner_status = "active_owner"
            warnings.append("ACTIVE_OWNER")
    except EthereumRPCError:
        # owner() is optional. A revert can simply mean the contract does not
        # expose Ownable-style ownership, so keep this distinct from provider
        # failure where possible. The RPC client class is provider-oriented,
        # therefore this remains a conservative unknown state.
        owner_status = "unavailable"
        hard_risks.append("AUTHORITY_DATA_UNCONFIRMED")
    except ContractValidationError:
        owner_status = "invalid_response"
        hard_risks.append("AUTHORITY_DATA_UNCONFIRMED")

    capability_indicators: list[str] = []
    for label, selector in CAPABILITY_SELECTORS.items():
        if _selector_present(code, selector):
            capability_indicators.append(label)
            warnings.append(label)

    mint_status = "indicator_present" if "MINT_FUNCTION_INDICATOR" in capability_indicators else "no_indicator"
    pause_status = "indicator_present" if (
        "PAUSE_FUNCTION_INDICATOR" in capability_indicators
        or "UNPAUSE_FUNCTION_INDICATOR" in capability_indicators
    ) else "no_indicator"

    # Standardized blacklist/fee/transfer-control APIs do not exist across
    # ERC-20, so we intentionally do not claim their absence from bytecode.
    blacklist_status = "not_determined"
    transfer_restriction_status = "not_determined"

    return AuthorityReport(
        address=address,
        owner_status=owner_status,
        owner_address=owner_address,
        mint_status=mint_status,
        pause_status=pause_status,
        blacklist_status=blacklist_status,
        transfer_restriction_status=transfer_restriction_status,
        hard_risks=tuple(hard_risks),
        warnings=tuple(warnings),
        data_complete=not hard_risks,
    )


__all__ = [
    "ContractSecurityError",
    "ContractProviderError",
    "ContractValidationError",
    "ContractSecurityReport",
    "AuthorityReport",
    "inspect_erc20",
    "inspect_contract_authorities",
]
