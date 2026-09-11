"""Generic read-only JSON-RPC client for EVM-compatible chains."""

from __future__ import annotations

from ethereum_rpc import (
    EthereumRPCClient,
    EthereumRPCError,
    EthereumRPCProviderError,
    EthereumRPCResponseError,
)


class EVMRPCClient(EthereumRPCClient):
    """Compatibility-safe generic EVM RPC client.

    The underlying Stage 1 client already enforces the read-only boundary and
    bounded cache. This adapter removes Ethereum from the public type used by
    new EVM layers without changing the proven RPC behavior.
    """

    def __init__(self, rpc_url: str, timeout_seconds: float = 15.0, cache_ttl_seconds: int = 30) -> None:
        super().__init__(rpc_url, timeout_seconds, cache_ttl_seconds)


__all__ = [
    "EVMRPCClient",
    "EthereumRPCError",
    "EthereumRPCProviderError",
    "EthereumRPCResponseError",
]
