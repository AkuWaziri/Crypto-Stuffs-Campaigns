from wallet_profile import (
    HistoricalTrade,
    calculate_closed_roi,
    is_whale_candidate,
    successful_asset_buys,
)


WALLET = "Whale"


def test_closed_roi_is_calculated_from_completed_buy_sell():
    trades = [
        HistoricalTrade(WALLET, "TOKEN", "BUY", 100, 1.0),
        HistoricalTrade(WALLET, "TOKEN", "SELL", 100, 2.0),
    ]
    result = calculate_closed_roi(trades, WALLET, "TOKEN")
    assert result is not None
    assert result.realized_roi_pct == 100.0
    assert result.remaining_quantity == 0


def test_partial_sell_uses_fifo_and_keeps_open_position():
    trades = [
        HistoricalTrade(WALLET, "TOKEN", "BUY", 100, 1.0),
        HistoricalTrade(WALLET, "TOKEN", "BUY", 100, 3.0),
        HistoricalTrade(WALLET, "TOKEN", "SELL", 50, 2.0),
    ]
    result = calculate_closed_roi(trades, WALLET, "TOKEN")
    assert result is not None
    assert result.realized_roi_pct == 100.0
    assert result.remaining_quantity == 150


def test_successful_buyer_can_qualify_as_whale():
    trades = [
        HistoricalTrade(WALLET, "TOKEN", "BUY", 100, 1.0),
        HistoricalTrade(WALLET, "TOKEN", "SELL", 100, 2.0),
    ]
    winners = successful_asset_buys(trades, WALLET, min_roi_pct=50)
    assert len(winners) == 1
    assert is_whale_candidate(current_value_usd=None, successful_trades=winners)


def test_small_wallet_without_success_does_not_qualify():
    assert not is_whale_candidate(current_value_usd=50_000, successful_trades=[])
