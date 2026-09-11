import pytest

from evm_early_buyer_intelligence import (
    EarlyBuyerValidationError,
    inspect_early_buyers,
)
from evm_holder_intelligence import TRANSFER_TOPIC

TOKEN = "0x1111111111111111111111111111111111111111"
BUYER_A = "0x2222222222222222222222222222222222222222"
BUYER_B = "0x3333333333333333333333333333333333333333"
PAIR = "0x4444444444444444444444444444444444444444"
OTHER = "0x5555555555555555555555555555555555555555"


def word(address):
    return "0x" + ("0" * 24) + address[2:]


def uint(value):
    return "0x" + f"{value:064x}"


def transfer_log(sender, receiver, amount, block, index):
    return {
        "address": TOKEN,
        "topics": [TRANSFER_TOPIC, word(sender), word(receiver)],
        "data": uint(amount),
        "blockNumber": hex(block),
        "logIndex": hex(index),
    }


def test_early_buyers_are_pair_receivers_and_ordered_by_first_observation():
    class FakeRPC:
        def eth_call(self, tx, block="latest"):
            data = tx["data"]
            if data.startswith("0x70a08231"):
                address = "0x" + data[-40:]
                return {
                    BUYER_A: uint(50),
                    BUYER_B: uint(0),
                }.get(address, uint(0))
            raise AssertionError(data)

        def get_logs(self, params, use_cache=True):
            assert params["fromBlock"] == hex(100)
            assert params["toBlock"] == hex(110)
            assert params["address"] == TOKEN
            assert params["topics"] == [TRANSFER_TOPIC]
            return [
                transfer_log(PAIR, BUYER_B, 25, 103, 2),
                transfer_log(OTHER, BUYER_A, 99, 104, 0),
                transfer_log(PAIR, BUYER_A, 50, 101, 1),
                transfer_log(PAIR, BUYER_A, 20, 102, 4),
            ]

    report = inspect_early_buyers(
        FakeRPC(),
        TOKEN,
        100,
        10,
        pair_addresses=[PAIR],
    )

    assert report.observed_buyer_count == 2
    assert report.buyers[0].address == BUYER_A
    assert report.buyers[0].first_block == 101
    assert report.buyers[0].received_amount == 70
    assert report.buyers[0].current_balance == 50
    assert report.buyers[0].still_holds is True
    assert report.buyers[1].address == BUYER_B
    assert report.buyers[1].still_holds is False
    assert "EARLY_BUYER_DATA_IS_OBSERVATIONAL" in report.warnings


def test_early_buyer_validation_requires_pair_and_positive_window():
    class FakeRPC:
        pass

    with pytest.raises(EarlyBuyerValidationError):
        inspect_early_buyers(FakeRPC(), TOKEN, 100, 10, pair_addresses=[])

    with pytest.raises(EarlyBuyerValidationError):
        inspect_early_buyers(FakeRPC(), TOKEN, 100, 0, pair_addresses=[PAIR])


def test_early_buyer_can_skip_balance_queries():
    class FakeRPC:
        def get_logs(self, params, use_cache=True):
            return [transfer_log(PAIR, BUYER_A, 123, 100, 0)]

    report = inspect_early_buyers(
        FakeRPC(),
        TOKEN,
        100,
        5,
        pair_addresses=[PAIR],
        check_current_balances=False,
    )

    assert report.buyers[0].received_amount == 123
    assert report.buyers[0].current_balance is None
    assert report.buyers[0].still_holds is None
