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


# Standard ERC-20 selectors. Calls are eth_call only; nothing is signed or sent.
SELECTORS = {
    "totalSupply": "18160ddd",
    "balanceOf": "70a08231",
    "decimals": "313ce567",
    "symbol": "95d89b41",
    "name": "06fdde03",
}


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


def _call(rpc: EVMRPCClient, address: str, selector: str) -> str:
    return rpc.eth_call({"to": address, "data": "0x" + selector})


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

    # ERC-20 compatibility requires the core callable surface to respond with
    # ABI-shaped data. balanceOf is checked against the zero address.
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
    if balance_zero < 0:  # defensive; uint decoding cannot produce this
        hard_risks.append("INVALID_BALANCE")

    # EIP-1967 implementation slot. A non-zero value is evidence of proxy
    # architecture, not automatically malicious behavior.
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


__all__ = [
    "ContractSecurityError",
    "ContractProviderError",
    "ContractValidationError",
    "ContractSecurityReport",
    "inspect_erc20",
]
