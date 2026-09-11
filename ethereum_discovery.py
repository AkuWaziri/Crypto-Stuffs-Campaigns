"""Ethereum-native token discovery with source isolation and deduplication."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ethereum_models import DiscoveryCandidate
from ethereum_rpc import EthereumRPCClient, EthereumRPCError
from eth_config import is_eth_address
from ethereum_market_data import DexScreenerClient


class DiscoveryError(RuntimeError):
    pass


class DiscoveryProviderError(DiscoveryError):
    pass


class DiscoveryValidationError(DiscoveryError):
    pass


@dataclass(frozen=True)
class DiscoveryResult:
    candidates: tuple[DiscoveryCandidate, ...]
    provider_errors: tuple[str, ...] = ()


def normalize_address(value: str) -> str:
    if not is_eth_address(value):
        raise DiscoveryValidationError(f"Invalid Ethereum address: {value}")
    return "0x" + value[2:].lower()


def _pair_contracts_from_log(log: dict[str, Any]) -> tuple[str, str]:
    topics = log.get("topics")
    if not isinstance(topics, list) or len(topics) < 3:
        raise DiscoveryValidationError("PairCreated log has insufficient topics")
    try:
        token0 = normalize_address("0x" + topics[1][-40:])
        token1 = normalize_address("0x" + topics[2][-40:])
    except (TypeError, DiscoveryValidationError) as exc:
        raise DiscoveryValidationError("PairCreated log contains invalid token addresses") from exc
    return token0, token1


def _pair_address_from_data(data: Any) -> str:
    if not isinstance(data, str) or not data.startswith("0x") or len(data) < 66:
        raise DiscoveryValidationError("PairCreated log has invalid data")
    # Uniswap V2-style PairCreated data is (pair address, pair index), both ABI-encoded.
    pair_word = data[2:66]
    return normalize_address("0x" + pair_word[-40:])


class DexScreenerDiscovery:
    source_name = "dexscreener"

    def __init__(self, client: DexScreenerClient) -> None:
        self.client = client

    def discover(self, query: str, max_results: int = 50) -> list[DiscoveryCandidate]:
        pairs = self.client.search_pairs(query)
        result: list[DiscoveryCandidate] = []
        for pair in pairs[:max_results]:
            if pair.get("chainId") != "ethereum":
                continue
            base = pair.get("baseToken")
            if not isinstance(base, dict):
                continue
            try:
                contract = normalize_address(str(base.get("address", "")))
                pair_address = normalize_address(str(pair.get("pairAddress", "")))
            except DiscoveryValidationError:
                continue
            result.append(
                DiscoveryCandidate(
                    contract=contract,
                    source=self.source_name,
                    pair=pair_address,
                    dex=str(pair.get("dexId")) if pair.get("dexId") else None,
                )
            )
        return result


class PairCreatedDiscovery:
    source_name = "onchain_pair_created"

    def __init__(self, rpc: EthereumRPCClient, factory_addresses: tuple[str, ...], topic: str) -> None:
        self.rpc = rpc
        self.factory_addresses = tuple(normalize_address(item) for item in factory_addresses)
        self.topic = topic

    def discover(self, from_block: int, to_block: int) -> list[DiscoveryCandidate]:
        if from_block < 0 or to_block < from_block:
            raise DiscoveryValidationError("Invalid discovery block range")
        if not self.factory_addresses or not self.topic:
            return []
        candidates: list[DiscoveryCandidate] = []
        for factory in self.factory_addresses:
            try:
                logs = self.rpc.get_logs(
                    {
                        "address": factory,
                        "fromBlock": hex(from_block),
                        "toBlock": hex(to_block),
                        "topics": [self.topic],
                    }
                )
            except EthereumRPCError as exc:
                raise DiscoveryProviderError(f"On-chain discovery failed: {exc}") from exc
            for log in logs:
                try:
                    token0, token1 = _pair_contracts_from_log(log)
                    pair = _pair_address_from_data(log.get("data"))
                    block = int(str(log.get("blockNumber", "0")), 16)
                except (DiscoveryValidationError, ValueError, TypeError) as exc:
                    raise DiscoveryValidationError("Invalid PairCreated log") from exc
                for token in (token0, token1):
                    candidates.append(
                        DiscoveryCandidate(
                            contract=token,
                            source=self.source_name,
                            pair=pair,
                            dex=f"factory:{factory}",
                            discovered_at_block=block,
                        )
                    )
        return candidates


def deduplicate_candidates(candidates: list[DiscoveryCandidate]) -> list[DiscoveryCandidate]:
    """Canonical identity is the Ethereum contract address."""
    merged: dict[str, DiscoveryCandidate] = {}
    for candidate in candidates:
        contract = normalize_address(candidate.contract)
        if contract not in merged:
            merged[contract] = DiscoveryCandidate(
                contract=contract,
                source=candidate.source,
                pair=candidate.pair,
                dex=candidate.dex,
                discovered_at_block=candidate.discovered_at_block,
            )
    return list(merged.values())
