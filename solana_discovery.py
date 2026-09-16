import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

import requests

from models import ActivityEvent, Explanation

BITQUERY_URL = "https://streaming.bitquery.io/eap"
SOLANA_EXPLORER = "https://solscan.io/tx/"

SOLANA_MIN_BUY_USD = max(100.0, float(os.getenv("SOLANA_MIN_BUY_USD", "2000")))
SOLANA_MAJOR_BUY_USD = max(SOLANA_MIN_BUY_USD, float(os.getenv("SOLANA_MAJOR_BUY_USD", "100000")))
SOLANA_REPEAT_MIN_USD = max(100.0, float(os.getenv("SOLANA_REPEAT_MIN_USD", "1000")))
SOLANA_REPEAT_MAX_USD = max(SOLANA_REPEAT_MIN_USD, float(os.getenv("SOLANA_REPEAT_MAX_USD", "5000")))
SOLANA_EMERGING_MAX_USD = max(SOLANA_MIN_BUY_USD, float(os.getenv("SOLANA_EMERGING_MAX_USD", "10000")))
SOLANA_WINDOW_MINUTES = max(5, int(os.getenv("SOLANA_WINDOW_MINUTES", "30")))
SOLANA_MAX_TRADES = max(20, min(int(os.getenv("SOLANA_MAX_TRADES", "200")), 500))

STABLE_MINTS = {
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkGZwyTDt1v",  # USDC
    "Es9vMFrzaCERmJfrF4H2FYD6bQ3YkJx8Qw7XQj9rYv",  # legacy/variant USDT reference
}
SOL_MINTS = {
    "So11111111111111111111111111111111111111112",
    "11111111111111111111111111111111",
}

SOLANA_DIAGNOSTICS: list[str] = []

QUERY = """
{
  Solana {
    DEXTrades(
      limit: { count: 200 }
      orderBy: { descending: Block_Time }
      where: {
        Block: { Time: { after_relative: { minutes_ago: 30 } } }
        Transaction: { Result: { Success: true } }
      }
    ) {
      Trade {
        Dex { ProtocolName ProtocolFamily }
        Buy {
          Account { Address }
          Amount
          AmountInUSD
          Currency { Symbol Name MintAddress }
          PriceInUSD
        }
        Sell {
          Account { Address }
          Amount
          AmountInUSD
          Currency { Symbol Name MintAddress }
          PriceInUSD
        }
      }
      Block { Time Height }
      Transaction { Signature FeePayer }
    }
  }
}
"""


def _number(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _bitquery_headers() -> dict[str, str]:
    token = os.getenv("BITQUERY_API_KEY", "").strip()
    if not token:
        return {}
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }


def _fetch_trades() -> list[dict[str, Any]]:
    SOLANA_DIAGNOSTICS.clear()
    if not os.getenv("BITQUERY_API_KEY", "").strip():
        SOLANA_DIAGNOSTICS.append("missing BITQUERY_API_KEY")
        return []

    query = QUERY.replace("limit: { count: 200 }", f"limit: {{ count: {SOLANA_MAX_TRADES} }}")
    try:
        response = requests.post(
            BITQUERY_URL,
            headers=_bitquery_headers(),
            data=json.dumps({"query": query}),
            timeout=45,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("errors"):
            SOLANA_DIAGNOSTICS.append(f"bitquery_error={payload['errors']}")
            return []
        return payload.get("data", {}).get("Solana", {}).get("DEXTrades", []) or []
    except requests.RequestException as exc:
        SOLANA_DIAGNOSTICS.append(f"request_error={exc}")
        return []
    except (ValueError, TypeError, KeyError) as exc:
        SOLANA_DIAGNOSTICS.append(f"parse_error={exc}")
        return []


def _buy_wallet(row: dict[str, Any]) -> str:
    trade = row.get("Trade") or {}
    buy = trade.get("Buy") or {}
    account = buy.get("Account") or {}
    return str(account.get("Address") or row.get("Transaction", {}).get("FeePayer") or "")


def _buy_currency(row: dict[str, Any]) -> dict[str, Any]:
    return ((row.get("Trade") or {}).get("Buy") or {}).get("Currency") or {}


def _buy_value(row: dict[str, Any]) -> float | None:
    return _number(((row.get("Trade") or {}).get("Buy") or {}).get("AmountInUSD"))


def _row_timestamp(row: dict[str, Any]) -> datetime:
    raw = (row.get("Block") or {}).get("Time")
    if isinstance(raw, str):
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def discover_solana_events() -> list[ActivityEvent]:
    """Discover broad Solana DEX buys from the live Bitquery trade stream.

    This deliberately does not restrict discovery to a fixed wallet list or stablecoin pairs.
    Bitquery identifies the actual buyer, token mint, USD trade value, DEX and signature.
    Helius remains available elsewhere in the project for wallet-level enrichment.
    """
    events: list[ActivityEvent] = []
    seen: set[str] = set()

    for row in _fetch_trades():
        value_usd = _buy_value(row)
        if value_usd is None or value_usd < SOLANA_MIN_BUY_USD:
            continue

        currency = _buy_currency(row)
        mint = str(currency.get("MintAddress") or "")
        if not mint or mint in STABLE_MINTS or mint in SOL_MINTS:
            continue

        signature = str((row.get("Transaction") or {}).get("Signature") or "")
        wallet = _buy_wallet(row)
        if not signature or not wallet or signature in seen:
            continue
        seen.add(signature)

        dex = (row.get("Trade") or {}).get("Dex") or {}
        symbol = str(currency.get("Symbol") or mint[:10] + "...")
        protocol = str(dex.get("ProtocolName") or dex.get("ProtocolFamily") or "Solana DEX")
        timestamp = _row_timestamp(row)

        events.append(
            ActivityEvent(
                entity=wallet,
                entity_type="SOLANA_WHALE_BUY",
                asset=symbol,
                action="BUY",
                value_usd=value_usd,
                chain="solana",
                timestamp=timestamp,
                source="bitquery",
                tx_or_reference=signature,
                evidence=(
                    f"{SOLANA_EXPLORER}{signature}",
                    f"mint: {mint}",
                    f"dex: {protocol}",
                ),
            )
        )

    events.sort(key=lambda event: event.timestamp, reverse=True)
    return events


def explain_discovered_event(event: ActivityEvent, all_events: list[ActivityEvent]) -> Explanation:
    token_events = [
        e for e in all_events
        if e.chain == "solana" and e.action == "BUY" and e.asset == event.asset
    ]
    wallets = {e.entity for e in token_events}
    wallet_events = [e for e in token_events if e.entity == event.entity]

    repeat_count = sum(
        1
        for e in wallet_events
        if e.value_usd is not None
        and SOLANA_REPEAT_MIN_USD <= e.value_usd <= SOLANA_REPEAT_MAX_USD
    )

    recent_count = sum(
        1
        for e in token_events
        if abs((e.timestamp - event.timestamp).total_seconds()) <= 15 * 60
    )

    if repeat_count >= 2:
        reason = (
            f"Repeated accumulation: this wallet has at least {repeat_count} detected buys "
            f"in the ${SOLANA_REPEAT_MIN_USD:,.0f}-${SOLANA_REPEAT_MAX_USD:,.0f} range for {event.asset}."
        )
    elif len(wallets) >= 3:
        reason = (
            f"Multi-wallet accumulation: {len(wallets)} distinct wallets were detected buying "
            f"{event.asset} in the same live window."
        )
    elif event.value_usd is not None and event.value_usd >= SOLANA_MAJOR_BUY_USD:
        reason = f"Major Solana purchase of approximately ${event.value_usd:,.0f} by the observed wallet."
    elif event.value_usd is not None and event.value_usd <= SOLANA_EMERGING_MAX_USD:
        reason = (
            f"Emerging-token purchase in the configured ${SOLANA_MIN_BUY_USD:,.0f}-"
            f"${SOLANA_EMERGING_MAX_USD:,.0f} monitoring band."
        )
    else:
        reason = f"Recent Solana DEX purchase detected from Bitquery trade data."

    evidence = event.evidence + (
        f"distinct_buyers_in_window: {len(wallets)}",
        f"token_buys_in_15m: {recent_count}",
    )
    return Explanation("CONFIRMED", reason, evidence, "HIGH")
