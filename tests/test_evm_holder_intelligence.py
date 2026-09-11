import pytest

from evm_holder_intelligence import (
    TRANSFER_TOPIC,
    HolderValidationError,
    inspect_holders,
)

TOKEN = "0x1111111111111111111111111111111111111111"
A = "0x2222222222222222222222222222222222222222"
B = "0x3333333333333333333333333333333333333333"
PAIR = "0x4444444444444444444444444444444444444444"


def word(address):
    return "0x" + ("0" * 24) + address[2:]


def uint(value):
    return "0x" + f"{value:064x}"


def transfer_log(sender, receiver):
    return {
        "topics": [TRANSFER_TOPIC, word(sender), word(receiver)],
        "data": "0x" + ("0" * 64),
    }


def test_holder_report_uses_current_balances_and_excludes_configured_addresses():
    class FakeRPC:
        def eth_call(self, tx, block="latest"):
            data = tx["data"]
            if data == "0x18160ddd":
                return uint(1_000_000)
            if data.startswith("0x70a08231"):
                address = "0x" + data[-40:]
                return {
                    A: uint(400_000),
                    B: uint(100_000),
                    PAIR: uint(500_000),
                }.get(address, uint(0))
            raise AssertionError(data)

        def get_logs(self, params, use_cache=True):
            assert params["address"] == TOKEN
            assert params["topics"] == [TRANSFER_TOPIC]
            return [
                transfer_log("0x" + "0" * 40, A),
                transfer_log(A, B),
                transfer_log(B, PAIR),
            ]

    report = inspect_holders(
        FakeRPC(),
        TOKEN,
        100,
        200,
        excluded_addresses=[PAIR],
    )

    assert report.total_supply == 1_000_000
    assert report.observed_addresses == 2
    assert report.holders[0].address == A
    assert report.holders[0].share == pytest.approx(0.4)
    assert report.top_holder_share == pytest.approx(0.4)
    assert report.top_5_share == pytest.approx(0.5)
    assert report.complete is False
    assert "HOLDER_DATA_IS_WINDOWED_NOT_COMPLETE" in report.warnings


def test_holder_report_rejects_invalid_block_range():
    class FakeRPC:
        pass

    with pytest.raises(HolderValidationError):
        inspect_holders(FakeRPC(), TOKEN, 10, 9)


def test_transfer_topic_is_standard_erc20_event_topic():
    assert TRANSFER_TOPIC == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
