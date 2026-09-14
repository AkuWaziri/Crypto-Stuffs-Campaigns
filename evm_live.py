import os
from datetime import datetime, timedelta, timezone
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


def _query_network(network: str, since: datetime, limit: int = 100) -> list[dict[str, Any]]:
    query = f"""
    query WhalesBoarderEVMTrades {{
      EVM(network: {network}) {{
        DEXTrades(
          limit: {{count: {limit}}}
          orderBy: {{descending: Block_Time}}
          where: {{Block: {{Time: {{since: \"{since.isoformat().replace('+00:00', 'Z')}\"}}}}}}
        ) {{
          Block {{ Time }}
          Transaction {{ From Hash }}
          Trade {{
            Sender
            Buy {{
              Buyer
              Amount
              AmountInUSD
              Currency {{ Name Symbol SmartContract }}
            }}
            Sell {{
              Seller
              Amount
              AmountInUSD
              Currency {{ Name Symbol SmartContract }}
            }}
            Dex {{ ProtocolName }}
          }}
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
    rows = payload.get("data", {}).get("EVM", {}).get("DEXTrades", [])
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
        addresses = response.json().get("result", {}).get("addresses", [])
        for item in addresses:
            if str(item.get("address", "")).lower() == wallet.lower():
                label = item.get("primary_label")
                if label:
                    entity_type = "KNOWN_ENTITY"
                break
    except requests.RequestException:
        pass

    # Moralis currently exposes wallet PnL summary for Ethereum, Base and Polygon.
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
        except requests.RequestException:
            pass

    return str(label) if label else None, entity_type, roi


def _parse_trade(row: dict[str, Any], network: str) -> ActivityEvent | None:
    tx = row.get("Transaction") or {}
    trade = row.get("Trade") or {}
    wallet = str(trade.get("Sender") or tx.get("From") or "")
    tx_hash = str(tx.get("Hash") or "")
    if not wallet or not tx_hash:
        return None

    buy = trade.get("Buy") or {}
    sell = trade.get("Sell") or {}
    buyer = str(buy.get("Buyer") or "")
    seller = str(sell.get("Seller") or "")

    if buyer.lower() == wallet.lower():
        action = "BUY"
        currency = buy.get("Currency") or {}
        asset = str(currency.get("Symbol") or currency.get("Name") or currency.get("SmartContract") or "UNKNOWN")
        value_usd = _number(buy.get("AmountInUSD"))
    elif seller.lower() == wallet.lower():
        action = "SELL"
        currency = sell.get("Currency") or {}
        asset = str(currency.get("Symbol") or currency.get("Name") or currency.get("SmartContract") or "UNKNOWN")
        value_usd = _number(sell.get("AmountInUSD"))
    else:
        return None

    if value_usd is None:
        value_usd = _number(buy.get("AmountInUSD")) or _number(sell.get("AmountInUSD"))
    if value_usd is None or value_usd < LIVE_MIN_USD:
        return None

    label, entity_type, roi = _moralis_enrichment(wallet, network)
    when_raw = (row.get("Block") or {}).get("Time")
    try:
        when = datetime.fromisoformat(str(when_raw).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        when = datetime.now(timezone.utc)

    explorer = EXPLORERS.get(network)
    evidence = (f"{explorer}{tx_hash}",) if explorer else (tx_hash,)
    if label:
        evidence = evidence + (f"Moralis label: {label}",)
    if roi is not None:
        evidence = evidence + (f"Moralis realized 30d ROI: {roi:.1f}%",)

    return ActivityEvent(
        entity=wallet,
        entity_type=entity_type,
        asset=asset,
        action=action,
        value_usd=value_usd,
        chain=network,
        timestamp=when,
        source="bitquery",
        tx_or_reference=tx_hash,
        evidence=evidence,
    )


def fetch_recent_large_evm_trades() -> list[ActivityEvent]:
    if not os.getenv("BITQUERY_API_KEY", ""):
        return []

    since = datetime.now(timezone.utc) - timedelta(minutes=LIVE_WINDOW_MINUTES)
    events: list[ActivityEvent] = []
    seen: set[tuple[str, str]] = set()

    for network in EVM_NETWORKS:
        try:
            rows = _query_network(network, since)
        except (requests.RequestException, RuntimeError):
            continue
        for row in rows:
            event = _parse_trade(row, network)
            if event is None:
                continue
            key = (network, event.tx_or_reference or "")
            if key in seen:
                continue
            seen.add(key)
            events.append(event)
            if len(events) >= LIVE_MAX_EVENTS:
                return sorted(events, key=lambda item: item.timestamp, reverse=True)

    return sorted(events, key=lambda item: item.timestamp, reverse=True)


def explain_evm_event(event: ActivityEvent) -> Explanation:
    reason = ""
    if event.entity_type == "SMART_MONEY":
        reason = "The wallet has recent realized profitability data supporting a smart-money classification."
    elif event.entity_type == "KNOWN_ENTITY":
        reason = "The wallet has a verified entity label from a secondary data source."

    if reason:
        return Explanation("INFERRED", reason, event.evidence, "MEDIUM")
    return Explanation(
        "CONFIRMED",
        f"Bitquery decoded a DEX trade showing this address as the {event.action.lower()} side of the transaction.",
        event.evidence,
        "HIGH",
    )
