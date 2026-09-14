import os
from datetime import datetime, timezone
from typing import Any

import requests

from models import ActivityEvent, classify_crypto_flow


HELIUS_BASE = "https://api.helius.xyz/v0/addresses"


def fetch_recent_transactions(address: str, api_key: str, limit: int = 20) -> list[dict[str, Any]]:
    if not address or not api_key:
        return []
    response = requests.get(
        f"{HELIUS_BASE}/{address}/transactions",
        params={"api-key": api_key, "limit": min(max(limit, 1), 100)},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    return data if isinstance(data, list) else []


def _target_flow(tx: dict[str, Any], wallet: str, asset_mint: str | None) -> tuple[bool, bool]:
    received = False
    spent = False
    for transfer in tx.get("tokenTransfers", []):
        if asset_mint and transfer.get("mint") != asset_mint:
            continue
        if transfer.get("toUserAccount") == wallet:
            received = True
        if transfer.get("fromUserAccount") == wallet:
            spent = True
    return received, spent


def parse_swap(tx: dict[str, Any], wallet: str, asset_mint: str | None = None) -> ActivityEvent | None:
    if tx.get("type") != "SWAP":
        return None

    received, spent = _target_flow(tx, wallet, asset_mint)
    action = classify_crypto_flow(
        received_target=received,
        spent_target=spent,
        is_swap=True,
    )
    if action not in {"BUY", "SELL"}:
        return None

    token = asset_mint or "UNKNOWN"
    timestamp = tx.get("timestamp")
    when = datetime.fromtimestamp(timestamp, tz=timezone.utc) if timestamp else datetime.now(timezone.utc)
    signature = tx.get("signature", "")

    return ActivityEvent(
        entity=wallet,
        entity_type="WHALE_WALLET",
        asset=token,
        action=action,
        value_usd=None,
        chain="solana",
        timestamp=when,
        source="helius",
        tx_or_reference=signature,
        evidence=(f"https://orb.helius.dev/tx/{signature}/history",) if signature else (),
    )


def monitor_wallet(address: str, asset_mint: str | None = None, limit: int = 20) -> list[ActivityEvent]:
    transactions = fetch_recent_transactions(address, os.getenv("HELIUS_API_KEY", ""), limit)
    return [event for tx in transactions if (event := parse_swap(tx, address, asset_mint))]
