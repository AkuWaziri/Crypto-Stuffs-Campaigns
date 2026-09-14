import os
import time
from datetime import datetime, timezone
from typing import Any

import requests

from live_config import LIVE_MAX_EVENTS, LIVE_MIN_USD, LIVE_WINDOW_MINUTES
from models import ActivityEvent, Explanation
from solana_monitor import monitor_wallet

VYBE_BASE = "https://api.vybenetwork.xyz/v4"
SOLANA_EXPLORER = "https://solscan.io/tx/"
USDC_MINT = "EPjFWdd5Aufrn3QWb1b1B9i6G4JqfQk5w5h8w8xw8w8"  # replaced below by common USDC aliases
USDC_MINTS = {
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkGZwyTDt1v",
}
USDT_MINTS = {
    "Es9vMFrzaCERmJfrF4H2FYD6bQ3YkJx8Qw7XQj9rYv",
}


def _get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    api_key = os.getenv("VYBE_API_KEY", "")
    if not api_key:
        raise RuntimeError("VYBE_API_KEY is not configured")
    response = requests.get(
        f"{VYBE_BASE}{path}",
        params=params or {},
        headers={"X-API-Key": api_key, "Accept": "application/json"},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, dict) else {}


def _number(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def fetch_recent_large_trades() -> list[dict[str, Any]]:
    now = int(time.time())
    payload = _get(
        "/trades",
        {
            "timeStart": now - LIVE_WINDOW_MINUTES * 60,
            "timeEnd": now,
            "limit": 1000,
            "sortByDesc": "blockTime",
        },
    )
    rows = payload.get("data", [])
    if not isinstance(rows, list):
        return []

    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        signature = str(row.get("signature") or "")
        if not signature or signature in seen:
            continue

        quote_mint = str(row.get("quoteMintAddress") or "")
        quote_size = _number(row.get("quoteSize"))
        if quote_mint not in USDC_MINTS | USDT_MINTS:
            continue
        if quote_size is None or quote_size < LIVE_MIN_USD:
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
        data = payload.get("data")
        if isinstance(data, dict) and data.get("symbol"):
            return str(data["symbol"])
    except requests.RequestException:
        pass
    return mint[:10] + "..."


def resolve_trade(row: dict[str, Any]) -> ActivityEvent | None:
    wallet = str(row.get("authorityAddress") or row.get("feePayerAddress") or "")
    signature = str(row.get("signature") or "")
    mint = str(row.get("baseMintAddress") or "")
    if not wallet or not signature or not mint:
        return None

    if not os.getenv("HELIUS_API_KEY", ""):
        raise RuntimeError("HELIUS_API_KEY is required to classify live trades as BUY or SELL")

    events = monitor_wallet(wallet, asset_mint=mint, limit=20)
    matched = next((event for event in events if event.tx_or_reference == signature), None)
    if matched is None:
        return None

    quote_size = _number(row.get("quoteSize"))
    block_time = _number(row.get("blockTime"))
    when = (
        datetime.fromtimestamp(int(block_time), tz=timezone.utc)
        if block_time is not None
        else matched.timestamp
    )

    return ActivityEvent(
        entity=wallet,
        entity_type="WHALE_WALLET",
        asset=_token_name(mint),
        action=matched.action,
        value_usd=quote_size,
        chain="solana",
        timestamp=when,
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
        f"Vybe trade data and the matched Helius transaction confirm a {event.action.lower()} of {event.asset}.",
        event.evidence,
        "HIGH",
    )
