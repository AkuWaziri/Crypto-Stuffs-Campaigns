"""Generic read-only JSON-RPC client for EVM-compatible chains."""

from __future__ import annotations

from typing import Any

from ethereum_rpc import (
    EthereumRPCClient,
    EthereumRPCError,
    EthereumRPCProviderError,
    EthereumRPCResponseError,
)


class EVMRPCClient(EthereumRPCClient):
    """Compatibility-safe generic EVM RPC client.

    The underlying Stage 1 client already enforces the read-only boundary and
    bounded cache. This adapter adds only read methods needed by EVM analysis.
    """

    def __init__(self, rpc_url: str, timeout_seconds: float = 15.0, cache_ttl_seconds: int = 30) -> None:
        super().__init__(rpc_url, timeout_seconds, cache_ttl_seconds)

    def eth_call(self, transaction: dict[str, Any], block: str = "latest") -> str:
        result = self.call("eth_call", [transaction, block])
        if not isinstance(result, str) or not result.startswith("0x"):
            raise EthereumRPCResponseError("eth_call returned an invalid result")
        return result

    def get_storage_at(self, address: str, slot: str, block: str = "latest") -> str:
        result = self.call("eth_getStorageAt", [address, slot, block])
        if not isinstance(result, str) or not result.startswith("0x"):
            raise EthereumRPCResponseError("eth_getStorageAt returned an invalid result")
        return result


__all__ = [
    "EVMRPCClient",
    "EthereumRPCError",
    "EthereumRPCProviderError",
    "EthereumRPCResponseError",
]
