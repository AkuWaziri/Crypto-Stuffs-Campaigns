from datetime import datetime, timezone
from typing import Any

from models import ActivityEvent, classify_crypto_flow


def parse_swap_transfer(
    tx: dict[str, Any],
    wallet: str,
    *,
    asset: str = "UNKNOWN",
    value_usd: float | None = None,
    chain: str = "evm",
) -> ActivityEvent | None:
    """Parse provider-normalized EVM swap data without guessing from transfers alone."""
    if tx.get("type") != "SWAP":
        return None
    received = bool(tx.get("receivedTarget"))
    spent = bool(tx.get("spentTarget"))
    action = classify_crypto_flow(received_target=received, spent_target=spent, is_swap=True)
    if action not in {"BUY", "SELL"}:
        return None
    timestamp = tx.get("timestamp")
    if isinstance(timestamp, (int, float)):
        when = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    else:
        when = datetime.now(timezone.utc)
    reference = str(tx.get("hash") or tx.get("transactionHash") or "")
    evidence = tuple(tx.get("evidence") or ())
    return ActivityEvent(
        entity=wallet,
        entity_type=str(tx.get("entityType") or "WHALE_WALLET"),
        asset=asset,
        action=action,
        value_usd=value_usd,
        chain=chain,
        timestamp=when,
        source=str(tx.get("source") or "evm_provider"),
        tx_or_reference=reference or None,
        evidence=evidence,
    )


def parse_rpc_transfer_log(log: dict[str, Any], wallet: str, *, asset: str, chain: str = "evm") -> ActivityEvent | None:
    """Normalize a token transfer only as TRANSFER; ERC-20 transfers do not prove a trade."""
    if not log.get("tokenTransfer"):
        return None
    return ActivityEvent(
        entity=wallet,
        entity_type="WHALE_WALLET",
        asset=asset,
        action="TRANSFER",
        value_usd=None,
        chain=chain,
        timestamp=datetime.now(timezone.utc),
        source="evm_rpc",
        tx_or_reference=log.get("transactionHash"),
        evidence=tuple(log.get("evidence") or ()),
    )
