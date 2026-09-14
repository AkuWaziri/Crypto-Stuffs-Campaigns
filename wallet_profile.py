from dataclasses import dataclass
from typing import Literal


EntityType = Literal[
    "WHALE_WALLET",
    "FUND",
    "TREASURY",
    "MARKET_MAKER",
    "EXCHANGE",
    "PROTOCOL",
    "INSTITUTION",
    "INSIDER",
]


@dataclass(frozen=True)
class HistoricalTrade:
    wallet: str
    asset: str
    action: Literal["BUY", "SELL"]
    quantity: float
    price_usd: float


@dataclass(frozen=True)
class AssetPerformance:
    wallet: str
    asset: str
    bought_quantity: float
    sold_quantity: float
    realized_roi_pct: float | None
    remaining_quantity: float


def calculate_closed_roi(trades: list[HistoricalTrade], wallet: str, asset: str) -> AssetPerformance | None:
    """Calculate simple FIFO realized ROI for one wallet/asset pair.

    This deliberately uses only completed buy/sell pairs. It does not claim
    an ROI for an open position because that requires a current market price.
    """
    relevant = [t for t in trades if t.wallet == wallet and t.asset == asset]
    if not relevant:
        return None

    lots: list[list[float]] = []
    realized_cost = 0.0
    realized_proceeds = 0.0
    bought = 0.0
    sold = 0.0

    for trade in relevant:
        if trade.quantity <= 0 or trade.price_usd < 0:
            continue
        if trade.action == "BUY":
            lots.append([trade.quantity, trade.price_usd])
            bought += trade.quantity
            continue

        remaining = trade.quantity
        sold += trade.quantity
        while remaining > 0 and lots:
            lot_qty, lot_price = lots[0]
            matched = min(remaining, lot_qty)
            realized_cost += matched * lot_price
            realized_proceeds += matched * trade.price_usd
            lot_qty -= matched
            remaining -= matched
            if lot_qty <= 0:
                lots.pop(0)
            else:
                lots[0][0] = lot_qty

    if sold == 0 or realized_cost == 0:
        roi = None
    else:
        roi = ((realized_proceeds - realized_cost) / realized_cost) * 100

    remaining_quantity = sum(qty for qty, _ in lots)
    return AssetPerformance(
        wallet=wallet,
        asset=asset,
        bought_quantity=bought,
        sold_quantity=sold,
        realized_roi_pct=roi,
        remaining_quantity=remaining_quantity,
    )


def successful_asset_buys(
    trades: list[HistoricalTrade],
    wallet: str,
    min_roi_pct: float = 50.0,
) -> list[AssetPerformance]:
    """Return assets where the wallet completed a profitable trade history.

    This is a second definition of a whale candidate: a wallet can qualify
    because it repeatedly bought assets that later produced strong realized ROI,
    even if its current balance is not among the largest wallets.
    """
    assets = sorted({t.asset for t in trades if t.wallet == wallet})
    results: list[AssetPerformance] = []
    for asset in assets:
        performance = calculate_closed_roi(trades, wallet, asset)
        if performance and performance.realized_roi_pct is not None and performance.realized_roi_pct >= min_roi_pct:
            results.append(performance)
    return results


def is_whale_candidate(
    *,
    current_value_usd: float | None,
    successful_trades: list[AssetPerformance],
    min_wallet_value_usd: float = 1_000_000.0,
    min_successful_assets: int = 1,
) -> bool:
    """A whale can qualify by size OR by demonstrated historical success."""
    large_wallet = current_value_usd is not None and current_value_usd >= min_wallet_value_usd
    successful_buyer = len(successful_trades) >= min_successful_assets
    return large_wallet or successful_buyer
