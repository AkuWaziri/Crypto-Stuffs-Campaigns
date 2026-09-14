import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from live_config import LIVE_MAX_EVENTS, LIVE_MIN_USD, LIVE_WINDOW_MINUTES
from models import ActivityEvent, Explanation
from solana_monitor import monitor_wallet

VYBE_BASE = "https://api.vybenetwork.com/v4"
SOLANA_EXPLORER = "https://solscan.io/tx/"


def _get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    api_key = os.getenv("VYBE_API_KEY", "")
    if not api_key:
        raise RuntimeError("VYBE_API_KEY is not configured")
    response = requests.get(
        f"{VYBE_BASE}{path}",
        params=params or {},
        headers={"X-API-Key": api_key},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, dict) else {}


def fetch_recent_large_trades() -> list[dict[str, Any]]:
    now = int(time.time())
    payload = _get(
        "/trades",
        {
            "timeStart": now - LIVE_WINDOW_MINUTES * 60,
            "timeEnd": now,
            "limit": 100,
            "sortByDesc": "blockTime",
        },
    )
    rows = payload.get("data", [])
    if not isinstance(rows, list):
        return []

    selected = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        signature = row.get("signature")
        if not signature or signature in seen:
            continue
        try:
            value_usd = float(row.get("valueUsd"))
        except (TypeError, ValueError):
            continue
        if value_usd < LIVE_MIN_USD:
            continue
        seen.add(signature)
        selected.append(row)
        if len(selected) >= LIVE_MAX_EVENTS:
            break
    return selected


def _token_name(mint: str) -> str:
    try:
        payload = _get(f"/tokens/{mint}")
        symbol = payload.get("symbol")
        if symbol:
            return str(symbol)
    except requests.RequestException:
        pass
    return mint[:10] + "..."


def resolve_trade(row: dict[str, Any]) -> ActivityEvent | None:
    wallet = str(row.get("authorityAddress") or row.get("feePayerAddress") or "")
    signature = str(row.get("signature") or "")
    mint = str(row.get("baseMintAddress") or "")
    if not wallet or not signature or not mint:
        return None

    helius_key = os.getenv("HELIUS_API_KEY", "")
    if not helius_key:
        raise RuntimeError("HELIUS_API_KEY is required to classify live trades as BUY or SELL")

    events = monitor_wallet(wallet, asset_mint=mint, limit=20)
    matched = next((event for event in events if event.tx_or_reference == signature), None)
    if matched is None:
        return None

    return ActivityEvent(
        entity=wallet,
        entity_type="WHALE_WALLET",
        asset=_token_name(mint),
        action=matched.action,
        value_usd=float(row.get("valueUsd")) if row.get("valueUsd") is not None else None,
        chain="solana",
        timestamp=datetime.fromtimestamp(
            int(row.get("blockTime")), tz=timezone.utc
        ) if row.get("blockTime") else matched.timestamp,
        source="vybe",
        tx_or_reference=signature,
        evidence=(f"{SOLANA_EXPLORER}{signature}",),
    )


def collect_vybe_live_events() -> list[ActivityEvent]:
    events: list[ActivityEvent] = []
    for row in fetch_recent_large_trades():
        event = resolve_trade(row)
        if event is not None:
            events.append(event)
    return events


def explain_live_event(event: ActivityEvent) -> Explanation:
    return Explanation(
        "CONFIRMED",
        f"Vybe trade data and the matched on-chain transaction confirm a {event.action.lower()} of {event.asset}.",
        event.evidence,
        "HIGH",
    )
