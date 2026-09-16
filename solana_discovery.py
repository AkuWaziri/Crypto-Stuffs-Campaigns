import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

import requests

from models import ActivityEvent, Explanation

DEX_BASE = "https://api.dexscreener.com"
HELIUS_ENHANCED = "https://api.helius.xyz/v0/addresses"
SOLANA_EXPLORER = "https://solscan.io/tx/"

SOLANA_MIN_BUY_USD = max(100.0, float(os.getenv("SOLANA_MIN_BUY_USD", "2000")))
SOLANA_MAJOR_BUY_USD = max(SOLANA_MIN_BUY_USD, float(os.getenv("SOLANA_MAJOR_BUY_USD", "100000")))
SOLANA_REPEAT_MIN_USD = max(100.0, float(os.getenv("SOLANA_REPEAT_MIN_USD", "1000")))
SOLANA_REPEAT_MAX_USD = max(SOLANA_REPEAT_MIN_USD, float(os.getenv("SOLANA_REPEAT_MAX_USD", "5000")))
SOLANA_EMERGING_MAX_USD = max(SOLANA_MIN_BUY_USD, float(os.getenv("SOLANA_EMERGING_MAX_USD", "10000")))
SOLANA_NEW_TOKEN_MINUTES = max(1, int(os.getenv("SOLANA_NEW_TOKEN_MINUTES", "5")))
SOLANA_DISCOVERY_MINUTES = max(5, int(os.getenv("SOLANA_DISCOVERY_MINUTES", "30")))
SOLANA_DISCOVERY_LIMIT = max(1, min(int(os.getenv("SOLANA_DISCOVERY_LIMIT", "20")), 50))
SOLANA_EVENTS_PER_TOKEN = max(5, min(int(os.getenv("SOLANA_EVENTS_PER_TOKEN", "50")), 100))


def _number(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _get_json(url: str, *, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> Any:
    response = requests.get(url, params=params or {}, headers=headers or {}, timeout=20)
    response.raise_for_status()
    return response.json()


def _helius_transactions(address: str, since: int) -> list[dict[str, Any]]:
    api_key = os.getenv("HELIUS_API_KEY", "")
    if not api_key or not address:
        return []
    payload = _get_json(
        f"{HELIUS_ENHANCED}/{address}/transactions",
        params={
            "api-key": api_key,
            "type": "SWAP",
            "gte-time": since,
            "sort-order": "asc",
            "limit": SOLANA_EVENTS_PER_TOKEN,
        },
    )
    return payload if isinstance(payload, list) else []


def _latest_solana_tokens() -> list[str]:
    payload = _get_json(f"{DEX_BASE}/token-profiles/latest/v1")
    rows = payload if isinstance(payload, list) else []
    tokens: list[str] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or row.get("chainId") != "solana":
            continue
        address = str(row.get("tokenAddress") or "")
        if address and address not in seen:
            seen.add(address)
            tokens.append(address)
        if len(tokens) >= SOLANA_DISCOVERY_LIMIT:
            break
    return tokens


def _pair_snapshot(token: str) -> dict[str, Any] | None:
    payload = _get_json(f"{DEX_BASE}/token-pairs/v1/solana/{token}")
    rows = payload if isinstance(payload, list) else []
    pairs = [row for row in rows if isinstance(row, dict)]
    if not pairs:
        return None
    pairs.sort(key=lambda row: _number(row.get("pairCreatedAt")) or 0, reverse=True)
    return pairs[0]


def _wallet_from_tx(tx: dict[str, Any]) -> str:
    return str(tx.get("feePayer") or tx.get("user") or tx.get("source") or "")


def _token_received(tx: dict[str, Any], mint: str, wallet: str) -> float:
    total = 0.0
    for transfer in tx.get("tokenTransfers", []) or []:
        if not isinstance(transfer, dict) or str(transfer.get("mint") or "") != mint:
            continue
        if str(transfer.get("toUserAccount") or "") != wallet:
            continue
        amount = _number(transfer.get("tokenAmount"))
        if amount is None:
            amount = _number(transfer.get("amount"))
            decimals = _number(transfer.get("decimals"))
            if amount is not None and decimals is not None:
                amount = amount / (10 ** int(decimals))
        if amount is not None:
            total += amount
    return total


def _token_sent(tx: dict[str, Any], mint: str, wallet: str) -> float:
    total = 0.0
    for transfer in tx.get("tokenTransfers", []) or []:
        if not isinstance(transfer, dict) or str(transfer.get("mint") or "") != mint:
            continue
        if str(transfer.get("fromUserAccount") or "") != wallet:
            continue
        amount = _number(transfer.get("tokenAmount"))
        if amount is None:
            amount = _number(transfer.get("amount"))
            decimals = _number(transfer.get("decimals"))
            if amount is not None and decimals is not None:
                amount = amount / (10 ** int(decimals))
        if amount is not None:
            total += amount
    return total


def _quote_value_usd(tx: dict[str, Any], wallet: str) -> float | None:
    # Prefer stablecoin transfers because their USD value is directly observable.
    stable_mints = {
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkGZwyTDt1v",
        "Es9vMFrzaCERmJfrF4H2FYD6bQ3YkJx8Qw7XQj9rYv",
    }
    total = 0.0
    found = False
    for transfer in tx.get("tokenTransfers", []) or []:
        if not isinstance(transfer, dict) or str(transfer.get("mint") or "") not in stable_mints:
            continue
        if str(transfer.get("fromUserAccount") or "") != wallet:
            continue
        amount = _number(transfer.get("tokenAmount"))
        if amount is None:
            amount = _number(transfer.get("amount"))
            decimals = _number(transfer.get("decimals"))
            if amount is not None and decimals is not None:
                amount = amount / (10 ** int(decimals))
        if amount is not None:
            total += amount
            found = True
    return total if found else None


def _sol_value_usd(tx: dict[str, Any], wallet: str) -> float | None:
    # Native SOL value is converted with the transaction's quoted SOL price when Helius provides it.
    sol_price = _number(tx.get("nativeTransfersUsd"))
    if sol_price is not None and sol_price > 0:
        return sol_price
    return None


def _trade_value_usd(tx: dict[str, Any], wallet: str, token_price_usd: float | None, mint: str) -> float | None:
    stable = _quote_value_usd(tx, wallet)
    if stable is not None and stable > 0:
        return stable
    received = _token_received(tx, mint, wallet)
    if received > 0 and token_price_usd is not None and token_price_usd > 0:
        return received * token_price_usd
    return _sol_value_usd(tx, wallet)


def _event_timestamp(tx: dict[str, Any]) -> datetime:
    raw = _number(tx.get("timestamp"))
    if raw is None:
        raw = _number(tx.get("blockTime"))
    return datetime.fromtimestamp(int(raw), tz=timezone.utc) if raw else datetime.now(timezone.utc)


def _token_symbol(pair: dict[str, Any], mint: str) -> str:
    base = pair.get("baseToken") if isinstance(pair, dict) else None
    if isinstance(base, dict) and base.get("symbol"):
        return str(base["symbol"])
    return mint[:10] + "..."


def discover_solana_events() -> list[ActivityEvent]:
    """Discover recent Solana token activity without restricting discovery to USDC/USDT pairs.

    DexScreener supplies a lightweight recent-token candidate list. Helius then supplies the
    transaction history used to identify the wallets buying those tokens. The monitor remains
    read-only and does not execute transactions.
    """
    now = int(datetime.now(timezone.utc).timestamp())
    discovery_since = now - SOLANA_DISCOVERY_MINUTES * 60
    events: list[ActivityEvent] = []
    seen_signatures: set[str] = set()

    for mint in _latest_solana_tokens():
        try:
            pair = _pair_snapshot(mint)
            if not pair:
                continue
            created = _number(pair.get("pairCreatedAt"))
            if created is None or created < discovery_since * 1000:
                continue

            age_minutes = max(0.0, (now - created / 1000) / 60)
            price_usd = _number(pair.get("priceUsd"))
            symbol = _token_symbol(pair, mint)
            transactions = _helius_transactions(mint, int(created / 1000))

            for tx in transactions:
                signature = str(tx.get("signature") or "")
                if not signature or signature in seen_signatures:
                    continue
                wallet = _wallet_from_tx(tx)
                if not wallet:
                    continue
                received = _token_received(tx, mint, wallet)
                sent = _token_sent(tx, mint, wallet)
                if received <= 0 or sent > 0:
                    continue
                value_usd = _trade_value_usd(tx, wallet, price_usd, mint)
                if value_usd is None or value_usd < SOLANA_MIN_BUY_USD:
                    continue
                seen_signatures.add(signature)
                events.append(
                    ActivityEvent(
                        entity=wallet,
                        entity_type="SOLANA_EARLY_BUY",
                        asset=symbol,
                        action="BUY",
                        value_usd=value_usd,
                        chain="solana",
                        timestamp=_event_timestamp(tx),
                        source="helius",
                        tx_or_reference=signature,
                        evidence=(f"{SOLANA_EXPLORER}{signature}", f"mint: {mint}"),
                    )
                )
        except requests.RequestException:
            continue
        except (TypeError, ValueError, KeyError):
            continue

    return events[: max(SOLANA_DISCOVERY_LIMIT, 10)]


def explain_discovered_event(event: ActivityEvent, all_events: list[ActivityEvent]) -> Explanation:
    token_events = [e for e in all_events if e.chain == "solana" and e.asset == event.asset and e.action == "BUY"]
    wallets = {e.entity for e in token_events}
    wallet_events = [e for e in token_events if e.entity == event.entity]
    repeat_count = sum(
        1 for e in wallet_events
        if e.value_usd is not None and SOLANA_REPEAT_MIN_USD <= e.value_usd <= SOLANA_REPEAT_MAX_USD
    )
    age_minutes = max(0.0, (datetime.now(timezone.utc) - event.timestamp).total_seconds() / 60)

    if age_minutes <= SOLANA_NEW_TOKEN_MINUTES:
        reason = f"Early activity: this wallet bought {event.asset} within roughly {SOLANA_NEW_TOKEN_MINUTES} minutes of the detected market launch."
    elif repeat_count >= 2:
        reason = f"Repeated accumulation: this wallet has at least {repeat_count} detected buys in the ${SOLANA_REPEAT_MIN_USD:,.0f}-${SOLANA_REPEAT_MAX_USD:,.0f} range for {event.asset}."
    elif len(wallets) >= 3:
        reason = f"Multiple-wallet activity: {len(wallets)} distinct wallets were detected buying {event.asset} in the same discovery window."
    elif event.value_usd is not None and event.value_usd >= SOLANA_MAJOR_BUY_USD:
        reason = f"Large on-chain purchase of approximately ${event.value_usd:,.0f} by the observed wallet."
    elif event.value_usd is not None and event.value_usd <= SOLANA_EMERGING_MAX_USD:
        reason = f"Emerging-token purchase in the configured ${SOLANA_MIN_BUY_USD:,.0f}-${SOLANA_EMERGING_MAX_USD:,.0f} monitoring band."
    else:
        reason = "Recent Solana purchase detected from Helius transaction data."

    evidence = event.evidence + (f"distinct_buyers_in_window: {len(wallets)}",)
    return Explanation("CONFIRMED", reason, evidence, "HIGH")
