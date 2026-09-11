"""Read-only holder and concentration intelligence for EVM tokens.

This module intentionally reports *observed* holder evidence rather than
pretending that a bounded Transfer-log window is a complete holder registry.
No transactions are signed or submitted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from evm_rpc import EVMRPCClient, EthereumRPCError


class HolderIntelligenceError(RuntimeError):
    pass


class HolderProviderError(HolderIntelligenceError):
    pass


class HolderValidationError(HolderIntelligenceError):
    pass


TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO_ADDRESS = "0x" + ("0" * 40)


@dataclass(frozen=True)
class HolderBalance:
    address: str
    balance: int
    share: float


@dataclass(frozen=True)
class HolderReport:
    token: str
    total_supply: int
    observed_addresses: int
    balances_checked: int
    holders: tuple[HolderBalance, ...] = field(default_factory=tuple)
    top_holder_share: float = 0.0
    top_5_share: float = 0.0
    top_10_share: float = 0.0
    coverage: str = "recent_transfer_observation"
    complete: bool = False
    warnings: tuple[str, ...] = field(default_factory=tuple)


def _validate_address(address: str) -> str:
    if not isinstance(address, str) or len(address) != 42 or not address.startswith("0x"):
        raise HolderValidationError("Invalid EVM token address")
    try:
        int(address[2:], 16)
    except ValueError as exc:
        raise HolderValidationError("Invalid EVM token address") from exc
    return "0x" + address[2:].lower()


def _decode_uint256(value: str) -> int:
    if not isinstance(value, str) or not value.startswith("0x") or len(value) < 66:
        raise HolderValidationError("Invalid uint256 RPC response")
    try:
        return int(value[2:66], 16)
    except ValueError as exc:
        raise HolderValidationError("Invalid uint256 RPC response") from exc


def _decode_topic_address(value: str) -> str:
    if not isinstance(value, str) or not value.startswith("0x") or len(value) < 66:
        raise HolderValidationError("Invalid indexed address topic")
    word = value[2:66]
    try:
        int(word, 16)
    except ValueError as exc:
        raise HolderValidationError("Invalid indexed address topic") from exc
    return "0x" + word[-40:].lower()


def _decode_transfer_participants(log: dict) -> tuple[str, str]:
    topics = log.get("topics")
    if not isinstance(topics, list) or len(topics) < 3:
        raise HolderValidationError("Transfer log is missing indexed addresses")
    return _decode_topic_address(topics[1]), _decode_topic_address(topics[2])


def _balance_of(rpc: EVMRPCClient, token: str, holder: str) -> int:
    data = "0x70a08231" + ("0" * 24) + holder[2:]
    return _decode_uint256(rpc.eth_call({"to": token, "data": data}))


def _unique_participants(logs: Iterable[dict], excluded: set[str]) -> set[str]:
    participants: set[str] = set()
    for log in logs:
        sender, receiver = _decode_transfer_participants(log)
        if sender != ZERO_ADDRESS and sender not in excluded:
            participants.add(sender)
        if receiver != ZERO_ADDRESS and receiver not in excluded:
            participants.add(receiver)
    return participants


def inspect_holders(
    rpc: EVMRPCClient,
    token_address: str,
    from_block: int,
    to_block: int,
    *,
    excluded_addresses: Iterable[str] = (),
    max_addresses: int = 100,
) -> HolderReport:
    """Inspect current balances for addresses observed in Transfer logs.

    The result is deliberately marked incomplete because dormant holders that
    did not appear in the selected block window cannot be inferred safely.
    """

    token = _validate_address(token_address)
    if from_block < 0 or to_block < from_block:
        raise HolderValidationError("Invalid block range")
    if max_addresses <= 0:
        raise HolderValidationError("max_addresses must be positive")

    excluded = {_validate_address(address) for address in excluded_addresses}
    excluded.add(ZERO_ADDRESS)

    try:
        total_supply = _decode_uint256(
            rpc.eth_call({"to": token, "data": "0x18160ddd"})
        )
        logs = rpc.get_logs(
            {
                "fromBlock": hex(from_block),
                "toBlock": hex(to_block),
                "address": token,
                "topics": [TRANSFER_TOPIC],
            },
            use_cache=False,
        )
    except EthereumRPCError as exc:
        raise HolderProviderError(f"Holder data unavailable: {exc}") from exc
    except HolderValidationError:
        raise

    if not isinstance(logs, list):
        raise HolderProviderError("Transfer-log response is not a list")

    participants = _unique_participants(logs, excluded)
    warnings: list[str] = []

    if len(participants) > max_addresses:
        warnings.append("HOLDER_ADDRESS_LIMIT_REACHED")
        participants = set(sorted(participants)[:max_addresses])

    balances: list[HolderBalance] = []
    for address in participants:
        try:
            balance = _balance_of(rpc, token, address)
        except (EthereumRPCError, HolderValidationError) as exc:
            warnings.append(f"BALANCE_UNAVAILABLE:{address}:{exc}")
            continue
        if balance <= 0:
            continue
        share = (balance / total_supply) if total_supply > 0 else 0.0
        balances.append(HolderBalance(address=address, balance=balance, share=share))

    balances.sort(key=lambda item: item.balance, reverse=True)
    top_5_share = sum(item.share for item in balances[:5])
    top_10_share = sum(item.share for item in balances[:10])

    if total_supply == 0:
        warnings.append("ZERO_TOTAL_SUPPLY")
    if not logs:
        warnings.append("NO_TRANSFER_ACTIVITY_IN_WINDOW")
    if len(participants) < 10:
        warnings.append("LOW_OBSERVED_HOLDER_COVERAGE")
    warnings.append("HOLDER_DATA_IS_WINDOWED_NOT_COMPLETE")

    return HolderReport(
        token=token,
        total_supply=total_supply,
        observed_addresses=len(participants),
        balances_checked=len(participants),
        holders=tuple(balances),
        top_holder_share=balances[0].share if balances else 0.0,
        top_5_share=top_5_share,
        top_10_share=top_10_share,
        warnings=tuple(warnings),
    )


__all__ = [
    "HolderIntelligenceError",
    "HolderProviderError",
    "HolderValidationError",
    "HolderBalance",
    "HolderReport",
    "TRANSFER_TOPIC",
    "inspect_holders",
]
