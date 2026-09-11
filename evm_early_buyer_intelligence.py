"""Read-only early-buyer intelligence for EVM tokens.

This module identifies token recipients whose transfers originate from a
configured liquidity/pair address near a supplied launch block. It reports
observations only; it does not infer intent and performs no execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from evm_holder_intelligence import TRANSFER_TOPIC, ZERO_ADDRESS
from evm_rpc import EVMRPCClient, EthereumRPCError


class EarlyBuyerIntelligenceError(RuntimeError):
    pass


class EarlyBuyerProviderError(EarlyBuyerIntelligenceError):
    pass


class EarlyBuyerValidationError(EarlyBuyerIntelligenceError):
    pass


@dataclass(frozen=True)
class EarlyBuyer:
    address: str
    first_block: int
    first_transfer_index: int | None
    received_amount: int
    current_balance: int | None
    still_holds: bool | None


@dataclass(frozen=True)
class EarlyBuyerReport:
    token: str
    launch_block: int
    window_end_block: int
    pair_addresses: tuple[str, ...]
    buyers: tuple[EarlyBuyer, ...] = field(default_factory=tuple)
    observed_buyer_count: int = 0
    warnings: tuple[str, ...] = field(default_factory=tuple)


def _validate_address(address: str) -> str:
    if not isinstance(address, str) or len(address) != 42 or not address.startswith("0x"):
        raise EarlyBuyerValidationError("Invalid EVM address")
    try:
        int(address[2:], 16)
    except ValueError as exc:
        raise EarlyBuyerValidationError("Invalid EVM address") from exc
    return "0x" + address[2:].lower()


def _decode_uint256(value: str) -> int:
    if not isinstance(value, str) or not value.startswith("0x") or len(value) < 66:
        raise EarlyBuyerValidationError("Invalid uint256 RPC response")
    try:
        return int(value[2:66], 16)
    except ValueError as exc:
        raise EarlyBuyerValidationError("Invalid uint256 RPC response") from exc


def _decode_topic_address(value: str) -> str:
    if not isinstance(value, str) or not value.startswith("0x") or len(value) < 66:
        raise EarlyBuyerValidationError("Invalid indexed address topic")
    word = value[2:66]
    try:
        int(word, 16)
    except ValueError as exc:
        raise EarlyBuyerValidationError("Invalid indexed address topic") from exc
    return "0x" + word[-40:].lower()


def _decode_transfer(log: dict) -> tuple[str, str, int]:
    topics = log.get("topics")
    if not isinstance(topics, list) or len(topics) < 3:
        raise EarlyBuyerValidationError("Transfer log is missing indexed addresses")
    data = log.get("data")
    if not isinstance(data, str) or not data.startswith("0x") or len(data) < 66:
        raise EarlyBuyerValidationError("Transfer log is missing amount data")
    return (
        _decode_topic_address(topics[1]),
        _decode_topic_address(topics[2]),
        _decode_uint256(data),
    )


def _log_block(log: dict) -> int:
    value = log.get("blockNumber")
    if isinstance(value, str) and value.startswith("0x"):
        try:
            return int(value, 16)
        except ValueError:
            pass
    if isinstance(value, int) and value >= 0:
        return value
    raise EarlyBuyerValidationError("Transfer log is missing blockNumber")


def _log_index(log: dict) -> int | None:
    value = log.get("logIndex")
    if isinstance(value, str) and value.startswith("0x"):
        try:
            return int(value, 16)
        except ValueError:
            return None
    return value if isinstance(value, int) and value >= 0 else None


def inspect_early_buyers(
    rpc: EVMRPCClient,
    token_address: str,
    launch_block: int,
    window_blocks: int,
    *,
    pair_addresses: Iterable[str],
    max_buyers: int = 100,
    check_current_balances: bool = True,
) -> EarlyBuyerReport:
    """Observe first token receipts from configured pair addresses.

    A buyer is an address receiving tokens directly from one of the supplied
    pair addresses during the bounded launch window. This is an observation
    layer, not proof that the transfer represented a market purchase.
    """

    token = _validate_address(token_address)
    pairs = tuple(sorted({_validate_address(address) for address in pair_addresses}))
    if not pairs:
        raise EarlyBuyerValidationError("At least one pair address is required")
    if launch_block < 0:
        raise EarlyBuyerValidationError("launch_block must be non-negative")
    if window_blocks <= 0:
        raise EarlyBuyerValidationError("window_blocks must be positive")
    if max_buyers <= 0:
        raise EarlyBuyerValidationError("max_buyers must be positive")

    window_end = launch_block + window_blocks
    warnings: list[str] = []

    try:
        logs = rpc.get_logs(
            {
                "fromBlock": hex(launch_block),
                "toBlock": hex(window_end),
                "address": token,
                "topics": [TRANSFER_TOPIC],
            },
            use_cache=False,
        )
    except EthereumRPCError as exc:
        raise EarlyBuyerProviderError(f"Early-buyer data unavailable: {exc}") from exc

    if not isinstance(logs, list):
        raise EarlyBuyerProviderError("Transfer-log response is not a list")

    pair_set = set(pairs)
    candidates: dict[str, tuple[int, int | None, int]] = {}
    for log in logs:
        sender, receiver, amount = _decode_transfer(log)
        if sender not in pair_set or receiver == ZERO_ADDRESS or receiver in pair_set:
            continue
        block = _log_block(log)
        index = _log_index(log)
        current = candidates.get(receiver)
        if current is None:
            candidates[receiver] = (block, index, amount)
        else:
            first_block, first_index, received = current
            received += amount
            if (block, index if index is not None else -1) < (
                first_block,
                first_index if first_index is not None else -1,
            ):
                first_block, first_index = block, index
            candidates[receiver] = (first_block, first_index, received)

    if len(candidates) > max_buyers:
        warnings.append("EARLY_BUYER_ADDRESS_LIMIT_REACHED")
        ordered = sorted(candidates.items(), key=lambda item: (item[1][0], item[0]))[:max_buyers]
        candidates = dict(ordered)

    buyers: list[EarlyBuyer] = []
    for address, (first_block, first_index, received_amount) in candidates.items():
        current_balance: int | None = None
        still_holds: bool | None = None
        if check_current_balances:
            data = "0x70a08231" + ("0" * 24) + address[2:]
            try:
                current_balance = _decode_uint256(rpc.eth_call({"to": token, "data": data}))
                still_holds = current_balance > 0
            except (EthereumRPCError, EarlyBuyerValidationError) as exc:
                warnings.append(f"EARLY_BUYER_BALANCE_UNAVAILABLE:{address}:{exc}")

        buyers.append(
            EarlyBuyer(
                address=address,
                first_block=first_block,
                first_transfer_index=first_index,
                received_amount=received_amount,
                current_balance=current_balance,
                still_holds=still_holds,
            )
        )

    buyers.sort(key=lambda item: (item.first_block, item.first_transfer_index if item.first_transfer_index is not None else -1, item.address))

    if not logs:
        warnings.append("NO_TRANSFER_ACTIVITY_IN_EARLY_WINDOW")
    if not buyers:
        warnings.append("NO_PAIR_TO_BUYER_TRANSFERS_IN_WINDOW")
    warnings.append("EARLY_BUYER_DATA_IS_OBSERVATIONAL")

    return EarlyBuyerReport(
        token=token,
        launch_block=launch_block,
        window_end_block=window_end,
        pair_addresses=pairs,
        buyers=tuple(buyers),
        observed_buyer_count=len(buyers),
        warnings=tuple(warnings),
    )


__all__ = [
    "EarlyBuyerIntelligenceError",
    "EarlyBuyerProviderError",
    "EarlyBuyerValidationError",
    "EarlyBuyer",
    "EarlyBuyerReport",
    "inspect_early_buyers",
]
