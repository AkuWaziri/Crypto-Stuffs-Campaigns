import os
from datetime import datetime, timezone
from typing import Any

import requests

from live_config import LIVE_MAX_EVENTS, LIVE_WINDOW_MINUTES
from models import ActivityEvent, Explanation

BITQUERY_URL = "https://streaming.bitquery.io/graphql"
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

EVM_MIN_BUY_USD = max(100.0, float(os.getenv("EVM_MIN_BUY_USD", "200")))
EVM_MAX_BUY_USD = max(EVM_MIN_BUY_USD, float(os.getenv("EVM_MAX_BUY_USD", "2000")))
EVM_MAJOR_BUY_MIN_USD = max(EVM_MAX_BUY_USD, float(os.getenv("EVM_MAJOR_BUY_MIN_USD", "5000")))
EVM_MAJOR_BUY_MAX_USD = max(EVM_MAJOR_BUY_MIN_USD, float(os.getenv("EVM_MAJOR_BUY_MAX_USD", "10000")))

EVM_DIAGNOSTICS: list[str] = []


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
            AmountsInUsd: {{Quote: {{gt: {EVM_MIN_BUY_USD}}}}}
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
    if not isinstance(rows, list):
        raise RuntimeError("Bitquery returned an unexpected Trades payload")
    return rows


def _number(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _parse_trade(row: dict[str, Any], network: str) -> ActivityEvent | None:
    trader = row.get("Trader") or {}
    pair = row.get("Pair") or {}
    token = pair.get("Token") or {}
    wallet = str(trader.get("Address") or "")
    tx_hash = str((row.get("TransactionHeader") or {}).get("Hash") or "")
    if not wallet or not tx_hash:
        return None

    side = str(row.get("Side") or "").upper()
    if side not in {"BUY", "SELL"}:
        return None

    amounts_usd = row.get("AmountsInUsd") or {}
    value_usd = _number(amounts_usd.get("Quote"))
    if value_usd is None:
        return None

    # Monitor both directions: $200-$2K and $5K-$10K.
    if not (
        EVM_MIN_BUY_USD <= value_usd <= EVM_MAX_BUY_USD
        or EVM_MAJOR_BUY_MIN_USD <= value_usd <= EVM_MAJOR_BUY_MAX_USD
    ):
        return None

    asset = str(token.get("Symbol") or token.get("Id") or "UNKNOWN")

    when_raw = (row.get("Block") or {}).get("Time")
    try:
        when = datetime.fromisoformat(str(when_raw).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        when = datetime.now(timezone.utc)

    explorer = EXPLORERS.get(network)
    evidence = (f"{explorer}{tx_hash}",) if explorer else (tx_hash,)

    return ActivityEvent(
        entity=wallet,
        entity_type="WHALE_WALLET",
        asset=asset,
        action=side,
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
    EVM_DIAGNOSTICS.clear()
    if not os.getenv("BITQUERY_API_KEY", ""):
        EVM_DIAGNOSTICS.append("BITQUERY_API_KEY missing")
        return []

    events: list[ActivityEvent] = []
    seen: set[str] = set()
    for network in EVM_NETWORKS:
        try:
            rows = _query_network(network)
            EVM_DIAGNOSTICS.append(f"{network}: ok rows={len(rows)}")
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "unknown"
            detail = exc.response.text[:300].replace("\n", " ") if exc.response is not None else str(exc)
            EVM_DIAGNOSTICS.append(f"{network}: HTTP {status} {detail}")
            continue
        except requests.RequestException as exc:
            EVM_DIAGNOSTICS.append(f"{network}: request error {exc}")
            continue
        except RuntimeError as exc:
            EVM_DIAGNOSTICS.append(f"{network}: Bitquery error {str(exc)[:500]}")
            continue

        parsed_before = len(events)
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
                EVM_DIAGNOSTICS.append(f"{network}: qualified_events={len(events) - parsed_before}")
                return sorted(events, key=lambda item: item.timestamp, reverse=True)
        EVM_DIAGNOSTICS.append(f"{network}: qualified_events={len(events) - parsed_before}")

    return sorted(events, key=lambda item: item.timestamp, reverse=True)


def explain_evm_event(event: ActivityEvent) -> Explanation:
    if event.action == "SELL":
        if event.value_usd is not None and EVM_MAJOR_BUY_MIN_USD <= event.value_usd <= EVM_MAJOR_BUY_MAX_USD:
            reason = f"Major EVM sale in the configured ${EVM_MAJOR_BUY_MIN_USD:,.0f}-${EVM_MAJOR_BUY_MAX_USD:,.0f} range."
        else:
            reason = f"EVM token sale in the configured ${EVM_MIN_BUY_USD:,.0f}-${EVM_MAX_BUY_USD:,.0f} monitoring band."
    elif event.value_usd is not None and EVM_MAJOR_BUY_MIN_USD <= event.value_usd <= EVM_MAJOR_BUY_MAX_USD:
        reason = f"Major EVM purchase in the configured ${EVM_MAJOR_BUY_MIN_USD:,.0f}-${EVM_MAJOR_BUY_MAX_USD:,.0f} range."
    else:
        reason = f"EVM token purchase in the configured ${EVM_MIN_BUY_USD:,.0f}-${EVM_MAX_BUY_USD:,.0f} monitoring band."
    return Explanation("CONFIRMED", reason, event.evidence, "HIGH")
