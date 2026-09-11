"""Read-only funding and deployer-flow intelligence for EVM tokens.

This module collects observable transfer evidence around a token creator or
configured anchor addresses. It does not infer maliciousness and does not
submit transactions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from evm_rpc import EVMRPCClient, EthereumRPCError

TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO_ADDRESS = "0x" + ("0" * 40)


class FundingIntelligenceError(RuntimeError):
    pass


class FundingProviderError(FundingIntelligenceError):
    pass


class FundingValidationError(FundingIntelligenceError):
    pass


@dataclass(frozen=True)
class FundingTransfer:
    sender: str
    receiver: str
    block_number: int
    transaction_hash: str
    amount: int


@dataclass(frozen=True)
class FundingReport:
    token: str
    anchor_addresses: tuple[str, ...]
    observed_transfers: int
    inbound_count: int
    outbound_count: int
    unique_senders: tuple[str, ...] = field(default_factory=tuple)
    unique_receivers: tuple[str, ...] = field(default_factory=tuple)
    transfers: tuple[FundingTransfer, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)


def _address(address: str) -> str:
    if not isinstance(address, str) or len(address) != 42 or not address.startswith("0x"):
        raise FundingValidationError("Invalid EVM address")
    try:
        int(address[2:], 16)
    except ValueError as exc:
        raise FundingValidationError("Invalid EVM address") from exc
    return "0x" + address[2:].lower()


def _uint(value: str) -> int:
    if not isinstance(value, str) or not value.startswith("0x") or len(value) < 66:
        raise FundingValidationError("Invalid uint256 value")
    try:
        return int(value[2:66], 16)
    except ValueError as exc:
        raise FundingValidationError("Invalid uint256 value") from exc


def _topic_address(value: str) -> str:
    if not isinstance(value, str) or not value.startswith("0x") or len(value) < 66:
        raise FundingValidationError("Invalid indexed address topic")
    try:
        int(value[2:66], 16)
    except ValueError as exc:
        raise FundingValidationError("Invalid indexed address topic") from exc
    return "0x" + value[26:66].lower()


def _transfer(log: dict) -> FundingTransfer:
    topics = log.get("topics")
    if not isinstance(topics, list) or len(topics) < 3:
        raise FundingValidationError("Transfer log missing indexed addresses")
    sender = _topic_address(topics[1])
    receiver = _topic_address(topics[2])
    block_raw = log.get("blockNumber", "0x0")
    tx_hash = log.get("transactionHash", "")
    try:
        block_number = int(block_raw, 16)
    except (TypeError, ValueError) as exc:
        raise FundingValidationError("Invalid transfer block number") from exc
    if not isinstance(tx_hash, str):
        raise FundingValidationError("Invalid transaction hash")
    data = log.get("data", "0x0")
    amount = _uint(data) if isinstance(data, str) and len(data) >= 66 else 0
    return FundingTransfer(sender, receiver, block_number, tx_hash, amount)


def inspect_funding(
    rpc: EVMRPCClient,
    token_address: str,
    anchor_addresses: Iterable[str],
    from_block: int,
    to_block: int,
) -> FundingReport:
    """Observe ERC-20 transfers involving configured anchor addresses."""
    token = _address(token_address)
    anchors = tuple(sorted({_address(a) for a in anchor_addresses}))
    if not anchors:
        raise FundingValidationError("At least one anchor address is required")
    if from_block < 0 or to_block < from_block:
        raise FundingValidationError("Invalid block range")

    transfers: list[FundingTransfer] = []
    warnings: list[str] = []
    try:
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
        raise FundingProviderError(f"Funding data unavailable: {exc}") from exc

    if not isinstance(logs, list):
        raise FundingProviderError("Transfer-log response is not a list")

    anchor_set = set(anchors)
    for log in logs:
        transfer = _transfer(log)
        if transfer.sender in anchor_set or transfer.receiver in anchor_set:
            transfers.append(transfer)

    transfers.sort(key=lambda item: (item.block_number, item.transaction_hash))
    inbound = sum(1 for item in transfers if item.receiver in anchor_set and item.sender not in anchor_set)
    outbound = sum(1 for item in transfers if item.sender in anchor_set and item.receiver not in anchor_set)
    senders = tuple(sorted({item.sender for item in transfers if item.sender not in anchor_set and item.sender != ZERO_ADDRESS}))
    receivers = tuple(sorted({item.receiver for item in transfers if item.receiver not in anchor_set and item.receiver != ZERO_ADDRESS}))

    if not transfers:
        warnings.append("NO_ANCHORED_TRANSFER_ACTIVITY")
    warnings.append("FUNDING_DATA_IS_TOKEN_FLOW_EVIDENCE")

    return FundingReport(
        token=token,
        anchor_addresses=anchors,
        observed_transfers=len(transfers),
        inbound_count=inbound,
        outbound_count=outbound,
        unique_senders=senders,
        unique_receivers=receivers,
        transfers=tuple(transfers),
        warnings=tuple(warnings),
    )


__all__ = [
    "TRANSFER_TOPIC",
    "FundingIntelligenceError",
    "FundingProviderError",
    "FundingValidationError",
    "FundingTransfer",
    "FundingReport",
    "inspect_funding",
]
