import os
from datetime import datetime, timezone
from typing import Any

import requests

from live_config import LIVE_MAX_EVENTS, LIVE_MIN_USD, LIVE_WINDOW_MINUTES
from models import ActivityEvent, Explanation

BITQUERY_URL = "https://streaming.bitquery.io/graphql"
MORALIS_URL = "https://deep-index.moralis.io/api/v2.2"
EVM_NETWORKS = tuple(
    item.strip()
    for item in os.getenv("EVM_NETWORKS", "eth,base,bsc,arbitrum,polygon").split(",")
    if item.strip()
)
NETWORK_NAMES = {
    "eth": "Ethereum",
    "base": "Base",
    "bsc": "Binance Smart Chain",
    "arbitrum": "Arbitrum",
    "polygon": "Matic",
}
EXPLORERS = {
    "eth": "https://etherscan.io/tx/",
    "base": "https://basescan.org/tx/",
    "bsc": "https://bscscan.com/tx/",
    "arbitrum": "https://arbiscan.io/tx/",
    "polygon": "https://polygonscan.com/tx/",
}


def _bitquery_headers() -> dict[str, str]:
    key = os.getenv("BITQUERY_API_KEY", "")
    if not key:
        raise RuntimeError("BITQUERY_API_KEY is not configured")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _query_network(network: str, limit: int = 100) -> list[dict[str, Any]]:
    network_name = NETWORK_NAMES.get(network, network)
    query = f"""
    query WhalesBoarderEVMTrades {{
      Trading {{
        Trades(
          limit: {{count: {limit}}}
          orderBy: {{descending: Block_Time}}
          where: {{
            Block: {{Time: {{since_relative: {{minutes_ago: {LIVE_WINDOW_MINUTES}}}}}}}
            Pair: {{Market: {{Network: {{is: "{network_name}"}}}}}}
            AmountsInUsd: {{Quote: {{gt: {LIVE_MIN_USD}}}}}
          }}
        ) {{
          Block {{ Time }}
          Side
          Trader {{ Address }}
          Amounts {{ Base Quote }}
          AmountsInUsd {{ Base Quote }}
          Pair {{
            Token {{ Symbol Id }}
            QuoteToken {{ Symbol Id }}
            Market {{ Network Protocol }}
          }}
          TransactionHeader {{ Hash }}
        }}
      }}
    }}
    """
    response = requests.post(
        BITQUERY_URL,
        headers=_bitquery_headers(),
        json={"query": query},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("errors"):
        raise RuntimeError(str(payload["errors"]))
    rows = payload.get("data", {}).get("Trading", {}).get("Trades", [])
    return rows if isinstance(rows, list) else []


def _number(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _moralis_enrichment(wallet: str, network: str) -> tuple[str | None, str, float | None]:
    key = os.getenv("MORALIS_API_KEY", "")
    if not key:
        return None, "WHALE_WALLET", None

    label = None
    entity_type = "WHALE_WALLET"
    roi = None
    headers = {"X-API-Key": key}

    try:
        response = requests.get(
            f"{MORALIS_URL}/entities/search",
            params={"query": wallet, "limit": 5},
            headers=headers,
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        addresses = payload.get("result", {}).get("addresses", [])
        for item in addresses:
            if str(item.get("address", "")).lower() == wallet.lower():
                label = item.get("primary_label")
                if label:
                    entity_type = "KNOWN_ENTITY"
                break
    except (requests.RequestException, ValueError, AttributeError):
        pass

    if network in {"eth", "base", "polygon"}:
        try:
            response = requests.get(
                f"{MORALIS_URL}/wallets/{wallet}/profitability/summary",
                params={"chain": network, "days": "30"},
                headers=headers,
                timeout=15,
            )
            response.raise_for_status()
            summary = response.json()
            roi = _number(summary.get("total_realized_profit_percentage"))
            if roi is not None and roi >= 50:
                entity_type = "SMART_MONEY"
        except (requests.RequestException, ValueError, AttributeError):
            pass

    return str(label) if label else None, entity_type, roi


def _parse_trade(row: dict[str, Any], network: str) -> ActivityEvent | None:
    trader = row.get("Trader") or {}
    pair = row.get("Pair") or {}
    token = pair.get("Token") or {}
    wallet = str(trader.get("Address") or "")
    tx_hash = str((row.get("TransactionHeader") or {}).get("Hash") or "")
    if not wallet or not tx_hash:
        return None

    side = str(row.get("Side") or "").upper()
    if side == "BUY":
        action = "BUY"
    elif side == "SELL":
        action = "SELL"
    else:
        return None

    amounts_usd = row.get("AmountsInUsd") or {}
    value_usd = _number(amounts_usd.get("Quote"))
    if value_usd is None or value_usd < LIVE_MIN_USD:
        return None

    asset = str(token.get("Symbol") or token.get("Id") or "UNKNOWN")
    label, entity_type, roi = _moralis_enrichment(wallet, network)

    when_raw = (row.get("Block") or {}).get("Time")
    try:
        when = datetime.fromisoformat(str(when_raw).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        when = datetime.now(timezone.utc)

    explorer = EXPLORERS.get(network)
    evidence = (f"{explorer}{tx_hash}",) if explorer else (tx_hash,)
    if label:
        evidence += (f"Moralis label: {label}",)
    if roi is not None:
        evidence += (f"Moralis realized 30d ROI: {roi:.1f}%",)

    return ActivityEvent(
        entity=wallet,
        entity_type=entity_type,
        asset=asset,
        action=action,
        value_usd=value_usd,
        chain=network,
        timestamp=when,
        source="bitquery_trading",
        tx_or_reference=tx_hash,
        evidence=evidence,
    )


def event_key(event: ActivityEvent) -> str:
    return "|".join(
        (
            event.chain or "",
            event.tx_or_reference or "",
            event.entity.lower(),
            event.action,
            event.asset,
        )
    )


def fetch_recent_large_evm_trades() -> list[ActivityEvent]:
    if not os.getenv("BITQUERY_API_KEY", ""):
        return []

    events: list[ActivityEvent] = []
    seen: set[str] = set()
    for network in EVM_NETWORKS:
        try:
            rows = _query_network(network)
        except (requests.RequestException, RuntimeError):
            continue
        for row in rows:
            event = _parse_trade(row, network)
            if event is None:
                continue
            key = event_key(event)
            if key in seen:
                continue
            seen.add(key)
            events.append(event)
            if len(events) >= LIVE_MAX_EVENTS:
                return sorted(events, key=lambda item: item.timestamp, reverse=True)

    return sorted(events, key=lambda item: item.timestamp, reverse=True)


def explain_evm_event(event: ActivityEvent) -> Explanation:
    if event.entity_type == "SMART_MONEY":
        return Explanation(
            "INFERRED",
            "Moralis reports strong recent realized profitability for this address, supporting a smart-money classification.",
            event.evidence,
            "MEDIUM",
        )
    if event.entity_type == "KNOWN_ENTITY":
        return Explanation(
            "INFERRED",
            "Moralis identifies this address as a known entity.",
            event.evidence,
            "MEDIUM",
        )
    return Explanation(
        "CONFIRMED",
        f"Bitquery Trading.Trades reports this wallet as the {event.action.lower()} side of the trade.",
        event.evidence,
        "HIGH",
    )
