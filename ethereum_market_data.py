"""Market-data ingestion with strict fail-closed validation."""

from __future__ import annotations

import json
import math
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

from ethereum_models import MarketData


class MarketDataError(RuntimeError):
    pass


class MarketDataProviderError(MarketDataError):
    pass


class MarketDataValidationError(MarketDataError):
    pass


HttpGet = Callable[[str], bytes]


def _default_get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.read()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        raise MarketDataProviderError(f"Market-data request failed: {exc}") from exc


def _finite_number(value: Any, field: str, *, allow_zero: bool = True) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise MarketDataValidationError(f"Invalid numeric field: {field}") from exc
    if not math.isfinite(number) or number < 0 or (not allow_zero and number == 0):
        raise MarketDataValidationError(f"Impossible numeric field: {field}")
    return number


def _signed_number(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise MarketDataValidationError(f"Invalid numeric field: {field}") from exc
    if not math.isfinite(number):
        raise MarketDataValidationError(f"Impossible numeric field: {field}")
    return number


def _integer(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise MarketDataValidationError(f"Invalid integer field: {field}")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise MarketDataValidationError(f"Invalid integer field: {field}") from exc
    if number < 0:
        raise MarketDataValidationError(f"Impossible integer field: {field}")
    return number


def _address(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 42 or not value.startswith("0x"):
        raise MarketDataValidationError(f"Invalid Ethereum address: {field}")
    try:
        int(value[2:], 16)
    except ValueError as exc:
        raise MarketDataValidationError(f"Invalid Ethereum address: {field}") from exc
    return "0x" + value[2:].lower()


def _ratio(buys: int, sells: int, field: str) -> float:
    if buys == 0 and sells == 0:
        raise MarketDataValidationError(f"No transactions available for {field}")
    if sells == 0:
        return float("inf")
    return buys / sells


def _pick(pair: dict[str, Any], *keys: str) -> Any:
    current: Any = pair
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


@dataclass
class DexScreenerClient:
    """Official public DexScreener HTTP API client used as one discovery/market source."""

    base_url: str = "https://api.dexscreener.com"
    get: HttpGet = _default_get

    def _json(self, path: str, params: dict[str, str] | None = None) -> Any:
        query = "" if not params else "?" + urllib.parse.urlencode(params)
        url = self.base_url.rstrip("/") + path + query
        try:
            body = self.get(url)
            return json.loads(body.decode())
        except MarketDataProviderError:
            raise
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MarketDataProviderError("DexScreener returned invalid JSON") from exc

    def search_pairs(self, query: str) -> list[dict[str, Any]]:
        payload = self._json("/latest/dex/search", {"q": query})
        pairs = payload.get("pairs") if isinstance(payload, dict) else None
        if not isinstance(pairs, list):
            raise MarketDataProviderError("DexScreener response missing pairs list")
        return [pair for pair in pairs if isinstance(pair, dict)]

    def token_pairs(self, contract: str) -> list[dict[str, Any]]:
        payload = self._json(f"/token-pairs/v1/ethereum/{contract}")
        if not isinstance(payload, list):
            raise MarketDataProviderError("DexScreener token-pairs response is not a list")
        return [pair for pair in payload if isinstance(pair, dict)]


def normalize_dexscreener_pair(pair: dict[str, Any], *, now_ms: int) -> MarketData:
    if pair.get("chainId") != "ethereum":
        raise MarketDataValidationError("Market pair is not on Ethereum")

    base = pair.get("baseToken")
    if not isinstance(base, dict):
        raise MarketDataValidationError("Missing base token")

    contract = _address(base.get("address"), "baseToken.address")
    pair_address = _address(pair.get("pairAddress"), "pairAddress")
    symbol = base.get("symbol")
    name = base.get("name")
    dex = pair.get("dexId")
    if not isinstance(symbol, str) or not symbol.strip() or not isinstance(name, str) or not name.strip():
        raise MarketDataValidationError("Missing token identity")
    if not isinstance(dex, str) or not dex.strip():
        raise MarketDataValidationError("Missing DEX identity")

    created = _integer(pair.get("pairCreatedAt"), "pairCreatedAt")
    if created <= 0 or created > now_ms:
        raise MarketDataValidationError("Invalid pair creation timestamp")
    age_seconds = (now_ms - created) / 1000.0

    price = _finite_number(pair.get("priceUsd"), "priceUsd", allow_zero=False)
    liquidity = _finite_number(_pick(pair, "liquidity", "usd"), "liquidity.usd", allow_zero=False)
    fdv = _finite_number(pair.get("fdv"), "fdv", allow_zero=False)
    market_cap = _finite_number(pair.get("marketCap"), "marketCap", allow_zero=False)

    volume_5m = _finite_number(_pick(pair, "volume", "m5"), "volume.m5")
    volume_1h = _finite_number(_pick(pair, "volume", "h1"), "volume.h1")
    buys_5m = _integer(_pick(pair, "txns", "m5", "buys"), "txns.m5.buys")
    sells_5m = _integer(_pick(pair, "txns", "m5", "sells"), "txns.m5.sells")
    buys_1h = _integer(_pick(pair, "txns", "h1", "buys"), "txns.h1.buys")
    sells_1h = _integer(_pick(pair, "txns", "h1", "sells"), "txns.h1.sells")
    ratio_5m = _ratio(buys_5m, sells_5m, "5m transactions")
    ratio_1h = _ratio(buys_1h, sells_1h, "1h transactions")
    change_5m = _signed_number(_pick(pair, "priceChange", "m5"), "priceChange.m5")
    change_1h = _signed_number(_pick(pair, "priceChange", "h1"), "priceChange.h1")

    if liquidity > fdv:
        raise MarketDataValidationError("Liquidity exceeds FDV")
    if market_cap > fdv * 1.05:
        raise MarketDataValidationError("Market cap contradicts FDV")
    if volume_5m > volume_1h + 1e-9:
        raise MarketDataValidationError("5m volume exceeds 1h volume")

    return MarketData(
        symbol=symbol.strip(),
        name=name.strip(),
        contract=contract,
        pair=pair_address,
        dex=dex.strip(),
        age_seconds=age_seconds,
        price_usd=price,
        market_cap_usd=market_cap,
        liquidity_usd=liquidity,
        fdv_usd=fdv,
        volume_5m_usd=volume_5m,
        volume_1h_usd=volume_1h,
        buys_5m=buys_5m,
        sells_5m=sells_5m,
        buys_1h=buys_1h,
        sells_1h=sells_1h,
        buy_sell_ratio_5m=ratio_5m,
        buy_sell_ratio_1h=ratio_1h,
        change_5m_pct=change_5m,
        change_1h_pct=change_1h,
        pair_created_at_ms=created,
    )


def select_best_pair(pairs: list[dict[str, Any]], *, now_ms: int) -> MarketData:
    """Normalize valid Ethereum pairs and choose the most liquid one."""
    candidates: list[MarketData] = []
    errors: list[str] = []
    for pair in pairs:
        try:
            candidates.append(normalize_dexscreener_pair(pair, now_ms=now_ms))
        except MarketDataValidationError as exc:
            errors.append(str(exc))
    if not candidates:
        raise MarketDataValidationError("No usable Ethereum market pair: " + "; ".join(errors[:3]))
    return max(candidates, key=lambda item: (item.liquidity_usd, item.volume_1h_usd))
