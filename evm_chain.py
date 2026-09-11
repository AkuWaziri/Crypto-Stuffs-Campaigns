"""Chain-agnostic configuration for EVM networks.

The intelligence engine uses this model instead of hard-coding Ethereum.
Ethereum is the first enabled chain; additional EVM chains can be added as
configuration without changing the analysis layers.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EVMChainConfig:
    name: str
    chain_id: int
    rpc_url: str
    native_symbol: str
    explorer_url: str = ""
    wrapped_native_token: str = ""
    dexscreener_chain_id: str = ""
    enabled: bool = True

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("chain name is required")
        if self.chain_id <= 0:
            raise ValueError("chain_id must be positive")
        if not self.rpc_url.strip():
            raise ValueError(f"RPC URL is required for {self.name}")
        if not self.native_symbol.strip():
            raise ValueError(f"native_symbol is required for {self.name}")
        if self.explorer_url and not self.explorer_url.startswith("https://"):
            raise ValueError(f"explorer_url must use HTTPS for {self.name}")
        if self.dexscreener_chain_id and not self.dexscreener_chain_id.strip():
            raise ValueError(f"invalid DexScreener chain id for {self.name}")


# Ethereum remains the first chain. Chain-specific market/discovery settings
# stay outside the core EVM analysis engine.
def ethereum_chain(rpc_url: str) -> EVMChainConfig:
    return EVMChainConfig(
        name="Ethereum",
        chain_id=1,
        rpc_url=rpc_url,
        native_symbol="ETH",
        explorer_url="https://etherscan.io",
        wrapped_native_token="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        dexscreener_chain_id="ethereum",
    )


def arc_chain(rpc_url: str) -> EVMChainConfig:
    """Arc network configuration target.

    RPC/provider and DEX settings are intentionally supplied by the caller;
    no live Arc endpoint is hard-coded into the engine.
    """
    return EVMChainConfig(
        name="Arc",
        chain_id=5042002,
        rpc_url=rpc_url,
        native_symbol="USDC",
        dexscreener_chain_id="arc",
    )
