"""Configuration for the Ethereum read-only intelligence system."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class EthereumConfig:
    chain_id: int = int(os.getenv("ETH_CHAIN_ID", "1"))
    rpc_url: str = os.getenv("ETH_RPC_URL", "")
    observation_limit: int = int(os.getenv("ETH_OBSERVATION_LIMIT", "25"))
    rpc_timeout_seconds: float = float(os.getenv("ETH_RPC_TIMEOUT_SECONDS", "15"))
    rpc_cache_ttl_seconds: int = int(os.getenv("ETH_RPC_CACHE_TTL_SECONDS", "30"))
    core_threshold: float = float(os.getenv("ETH_CORE_THRESHOLD", "75"))
    telegram_interval_minutes: int = int(os.getenv("ETH_TELEGRAM_INTERVAL_MINUTES", "15"))
    dexscreener_base_url: str = os.getenv(
        "ETH_DEXSCREENER_BASE_URL", "https://api.dexscreener.com"
    )
    discovery_query: str = os.getenv("ETH_DISCOVERY_QUERY", "WETH")
    discovery_max_results: int = int(os.getenv("ETH_DISCOVERY_MAX_RESULTS", "50"))
    factory_addresses: tuple[str, ...] = _csv(os.getenv("ETH_FACTORY_ADDRESSES", ""))
    pair_created_topic: str = os.getenv("ETH_PAIR_CREATED_TOPIC", "")

    def validate(self) -> None:
        if self.chain_id != 1:
            raise ValueError("ETH_CHAIN_ID must be 1 for Ethereum mainnet")
        if not self.rpc_url.strip():
            raise ValueError("ETH_RPC_URL is required")
        if self.observation_limit <= 0:
            raise ValueError("ETH_OBSERVATION_LIMIT must be positive")
        if self.rpc_timeout_seconds <= 0:
            raise ValueError("ETH_RPC_TIMEOUT_SECONDS must be positive")
        if self.rpc_cache_ttl_seconds < 0:
            raise ValueError("ETH_RPC_CACHE_TTL_SECONDS cannot be negative")
        if not 0 <= self.core_threshold <= 100:
            raise ValueError("ETH_CORE_THRESHOLD must be between 0 and 100")
        if self.telegram_interval_minutes <= 0:
            raise ValueError("ETH_TELEGRAM_INTERVAL_MINUTES must be positive")
        if not self.dexscreener_base_url.startswith("https://"):
            raise ValueError("ETH_DEXSCREENER_BASE_URL must use HTTPS")
        if not self.discovery_query.strip():
            raise ValueError("ETH_DISCOVERY_QUERY cannot be empty")
        if self.discovery_max_results <= 0:
            raise ValueError("ETH_DISCOVERY_MAX_RESULTS must be positive")
        for address in self.factory_addresses:
            if not is_eth_address(address):
                raise ValueError(f"Invalid Ethereum factory address: {address}")
        if self.pair_created_topic and (
            not self.pair_created_topic.startswith("0x") or len(self.pair_created_topic) != 66
        ):
            raise ValueError("ETH_PAIR_CREATED_TOPIC must be a 32-byte hex topic")


def is_eth_address(value: str) -> bool:
    if not isinstance(value, str) or len(value) != 42 or not value.startswith("0x"):
        return False
    try:
        int(value[2:], 16)
    except ValueError:
        return False
    return True


eth_config = EthereumConfig()
