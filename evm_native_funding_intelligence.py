"""Read-only native-asset funding evidence around an address."""
from __future__ import annotations
from dataclasses import dataclass
from evm_rpc import EVMRPCClient, EthereumRPCError

@dataclass(frozen=True)
class NativeFundingReport:
    address: str
    balance_wei: int | None
    inbound_transactions: int = 0
    outbound_transactions: int = 0
    warnings: tuple[str, ...] = ()

def inspect_native_balance(rpc: EVMRPCClient, address: str) -> NativeFundingReport:
    if not isinstance(address, str) or len(address) != 42 or not address.startswith("0x"):
        raise ValueError("Invalid EVM address")
    try:
        result = rpc.call("eth_getBalance", [address, "latest"])
        balance = int(result, 16) if isinstance(result, str) else None
    except (EthereumRPCError, ValueError) as exc:
        return NativeFundingReport(address.lower(), None, warnings=(f"NATIVE_BALANCE_UNAVAILABLE:{exc}",))
    return NativeFundingReport(address.lower(), balance, warnings=("NATIVE_BALANCE_IS_NOT_FUNDING_PROOF",))
