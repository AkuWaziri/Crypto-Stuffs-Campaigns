from __future__ import annotations

from dataclasses import dataclass
from urllib.request import Request, urlopen
import json

from tokenized_stock_pairing import TokenizedStock


XSTOCKS_ASSETS_URL = "https://api.xstocks.fi/api/v2/public/assets"


@dataclass(frozen=True)
class XStocksPublicProvider:
    timeout_seconds: float = 10.0
    assets_url: str = XSTOCKS_ASSETS_URL

    def list_assets(self) -> list[dict]:
        request = Request(
            self.assets_url,
            headers={"Accept": "application/json", "User-Agent": "TrendsBot/1.0"},
            method="GET",
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            if response.status != 200:
                raise RuntimeError(f"xStocks API returned HTTP {response.status}")
            payload = json.loads(response.read().decode("utf-8"))
        return _extract_assets(payload)


def _extract_assets(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        raise ValueError("unexpected xStocks API response")

    for key in ("data", "assets", "results"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            for nested_key in ("assets", "results", "data"):
                nested = value.get(nested_key)
                if isinstance(nested, list):
                    return [item for item in nested if isinstance(item, dict)]

    raise ValueError("xStocks API response did not contain an asset list")


def _symbol(asset: dict) -> str | None:
    for key in ("symbol", "tokenSymbol", "ticker"):
        value = asset.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().upper()
    return None


def _name(asset: dict, symbol: str) -> str:
    for key in ("name", "tokenName", "underlyingName"):
        value = asset.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return symbol.rstrip("xX")


def verified_preferred_stocks(
    provider: XStocksPublicProvider,
    preferred: tuple[tuple[str, str, float], ...] = (
        ("AAPLx", "Apple xStock", 95.0),
        ("NVDAx", "NVIDIA xStock", 94.0),
        ("MSFTx", "Microsoft xStock", 93.0),
        ("TSLAx", "Tesla xStock", 92.0),
        ("AMZNx", "Amazon xStock", 91.0),
    ),
) -> tuple[TokenizedStock, ...]:
    assets = provider.list_assets()
    live_symbols = {_symbol(asset): asset for asset in assets if _symbol(asset)}

    verified: list[TokenizedStock] = []
    for symbol, preferred_name, quality_score in preferred:
        asset = live_symbols.get(symbol.upper())
        if asset is None:
            continue
        verified.append(
            TokenizedStock(
                symbol=symbol.upper(),
                name=_name(asset, preferred_name),
                quality_score=quality_score,
                liquidity_score=quality_score,
                availability="live-verified",
            )
        )

    if not verified:
        raise ValueError("no preferred tokenized-stock asset was verified by xStocks")
    return tuple(verified)
